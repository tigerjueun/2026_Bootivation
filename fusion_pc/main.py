from __future__ import annotations

import argparse
import json
import queue
import sys
import threading
import time
from pathlib import Path
from typing import Any

import zmq

SRC = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC))

from bootivation_fusion.adapters.parsers import parse_pos_line, parse_vision_message
from bootivation_fusion.adapters.retail_zmq import RetailCustomerSubscriber
from bootivation_fusion.adapters.serial_worker import RiderSerialLink, SerialEventReader
from bootivation_fusion.adapters.vision_emergency import (
    EmergencyDispatcher,
    VisionEmergencyClient,
)
from bootivation_fusion.config import load_config
from bootivation_fusion.core.state_manager import StateManager
from bootivation_fusion.domain.events import Event
from bootivation_fusion.event_logger import JsonlLogger
from ops_dashboard import OpsDashboard


PRODUCTS = ("A", "B", "C")
RIDER_COMMAND_GAP_SEC = 0.30
RIDER_CONNECT_SETTLE_SEC = 2.0
CUSTOMER_EXIT_GRACE_SEC = 1.20
PAYMENT_ASSOCIATION_WINDOW_SEC = 8.0

VALID_AUDIO_EVENTS = {
    "SYSTEM_READY",
    "PLACE_BEFORE",
    "SCAN_PRODUCT",
    "SCAN_COMPLETED",
    "TRAY_MISMATCH",
    "SYSTEM_RESET",
}


def normalize_counts(value: dict[str, Any] | None) -> dict[str, int]:
    value = value or {}
    return {
        product: max(0, int(value.get(product, 0)))
        for product in PRODUCTS
    }


def choose_customer_payment(state: object) -> dict[str, int]:
    """Choose the most authoritative current POS customer count."""
    candidates = [
        getattr(state, "pos_reported_items", {}) or {},
        getattr(state, "pos_session_items", {}) or {},
    ]

    for candidate in candidates:
        normalized = normalize_counts(candidate)
        if sum(normalized.values()) > 0:
            return normalized

    # `paid_items` is cumulative across completed customer sessions in the
    # current StateManager. Use it only as a last fallback.
    return normalize_counts(getattr(state, "paid_items", {}) or {})


class RpiTraySubscriber(threading.Thread):
    def __init__(
        self,
        *,
        endpoint: str,
        output_queue: queue.Queue[dict[str, Any]],
        stop_event: threading.Event,
    ) -> None:
        super().__init__(name="rpi-tray-zmq", daemon=True)
        self.endpoint = endpoint
        self.output_queue = output_queue
        self.stop_event = stop_event

        context = zmq.Context.instance()
        self.socket = context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")

    def stop(self) -> None:
        self.stop_event.set()

    def run(self) -> None:
        try:
            self.socket.connect(self.endpoint)
            print(f"[rpi] SUB {self.endpoint}")

            poller = zmq.Poller()
            poller.register(self.socket, zmq.POLLIN)

            while not self.stop_event.is_set():
                events = dict(poller.poll(300))
                if self.socket not in events:
                    continue

                try:
                    message = self.socket.recv_json(flags=zmq.NOBLOCK)
                except (zmq.Again, ValueError):
                    continue

                if not isinstance(message, dict):
                    continue
                if message.get("source") != "rpi_tray":
                    continue
                if message.get("event") != "TRAY_COUNT":
                    continue

                self.output_queue.put(message)

        except Exception as error:
            print(f"[rpi] subscriber stopped: {error}")
        finally:
            self.socket.close(0)


class RpiCommandLink:
    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.PUSH)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.setsockopt(zmq.SNDTIMEO, 800)
        self.socket.connect(endpoint)
        print(f"[rpi] PUSH {endpoint}")

    def send(self, payload: dict[str, Any]) -> bool:
        try:
            self.socket.send_json(payload)
        except zmq.Again:
            print(f"[rpi] command timeout: {payload}")
            return False

        print("[rpi] CMD " + json.dumps(payload, ensure_ascii=False))
        return True

    def close(self) -> None:
        self.socket.close(0)


def send_rider_command(
    rider_link: RiderSerialLink | None,
    command: str,
) -> None:
    if rider_link is None:
        return

    normalized = command.strip()
    if not normalized:
        return

    rider_link.send(normalized)
    time.sleep(RIDER_COMMAND_GAP_SEC)


def send_rider_commands(
    rider_link: RiderSerialLink | None,
    commands: list[object],
) -> None:
    for command in commands:
        if getattr(command, "target", None) != "rider":
            continue
        send_rider_command(
            rider_link,
            str(getattr(command, "command", "")),
        )


def manual_console(
    *,
    event_queue: queue.Queue[Event],
    order_queue: queue.Queue[dict[str, int]],
    action_queue: queue.Queue[dict[str, Any]],
    stop_event: threading.Event,
) -> None:
    print(
        "Commands: status | rpi | vision | order A=1,B=1 | "
        "event REMOVE_CANDIDATE:A | audio TRAY_MISMATCH | "
        "rpi-reset | emergency 100 | reset | quit"
    )

    while not stop_event.is_set():
        try:
            line = input("fusion> ").strip()
        except EOFError:
            stop_event.set()
            return

        if not line:
            continue

        if line == "quit":
            stop_event.set()
            return

        if line == "reset":
            event_queue.put(Event(source="manual", kind="SYSTEM_RESET"))
            continue

        if line in {"status", "rpi", "vision", "rpi-reset"}:
            action_queue.put({"action": line})
            continue

        if line.startswith("audio "):
            event_name = line.removeprefix("audio ").strip().upper()
            if event_name not in VALID_AUDIO_EVENTS:
                print(
                    "Invalid audio event. Use: "
                    + ", ".join(sorted(VALID_AUDIO_EVENTS))
                )
                continue
            action_queue.put({
                "action": "audio",
                "event": event_name,
            })
            continue

        if line.startswith("emergency "):
            customer_text = line.removeprefix("emergency ").strip()
            if not customer_text.isdigit():
                print("Usage: emergency <customer_id>")
                continue
            action_queue.put({
                "action": "emergency",
                "customer_id": int(customer_text),
            })
            continue

        if line.startswith("order "):
            order: dict[str, int] = {}

            for token in line.removeprefix("order ").split(","):
                name, _, quantity = token.strip().partition("=")
                if (
                    name.upper() in PRODUCTS
                    and quantity.isdigit()
                ):
                    order[name.upper()] = int(quantity)

            if not order or sum(order.values()) <= 0:
                print("Invalid order. Example: order A=1,B=1,C=1")
                continue

            order_queue.put(order)
            continue

        if line.startswith("event "):
            raw = line.removeprefix("event ").strip()
            event = parse_vision_message(raw)
            if event is None:
                print("Invalid manual event")
                continue
            event_queue.put(event)
            continue

        print("Unknown command")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="config/system.json",
    )
    parser.add_argument(
        "--rpi-endpoint",
        default="tcp://10.77.0.2:5562",
    )
    parser.add_argument(
        "--rpi-command-endpoint",
        default="tcp://10.77.0.2:5563",
    )
    parser.add_argument(
        "--vision-emergency-endpoint",
        help=(
            "Override Vision WebUI Emergency endpoint, "
            "for example tcp://192.168.0.20:5556"
        ),
    )
    parser.add_argument("--emergency-timeout-ms", type=int, default=3000)
    parser.add_argument("--emergency-retries", type=int, default=1)
    parser.add_argument("--no-rpi", action="store_true")
    parser.add_argument("--no-ui", action="store_true")
    parser.add_argument("--ui-host", default="127.0.0.1")
    parser.add_argument("--ui-port", type=int, default=8088)
    args = parser.parse_args()

    config = load_config(args.config)

    event_queue: queue.Queue[Event] = queue.Queue()
    order_queue: queue.Queue[dict[str, int]] = queue.Queue()
    action_queue: queue.Queue[dict[str, Any]] = queue.Queue()
    rpi_queue: queue.Queue[dict[str, Any]] = queue.Queue()
    customer_session_queue: queue.Queue[dict[str, Any]] = queue.Queue()
    stop_event = threading.Event()

    latest_rpi: dict[str, Any] = {}
    latest_vision: dict[str, Any] = {}

    rider_config = config["rider"]
    state_manager = StateManager(
        cooldown_sec=float(
            config["remove_validation"]["cooldown_sec"]
        ),
        rider_pick_source=str(
            rider_config.get("pick_source", "vision")
        ),
    )
    logger = JsonlLogger(config["logging"]["event_log"])
    dashboard = OpsDashboard(action_queue)

    if not args.no_ui:
        dashboard.start(args.ui_host, args.ui_port)

    workers: list[object] = []
    rider_link: RiderSerialLink | None = None
    rpi_command_link: RpiCommandLink | None = None
    emergency_dispatcher: EmergencyDispatcher | None = None

    pos_config = config["pos"]
    if pos_config.get("enabled"):
        worker = SerialEventReader(
            name="pos",
            port=pos_config["port"],
            baud=int(pos_config["baud"]),
            timeout=float(pos_config["timeout_sec"]),
            event_queue=event_queue,
            parser=parse_pos_line,
        )
        worker.start()
        workers.append(worker)

    if rider_config.get("enabled"):
        try:
            rider_link = RiderSerialLink(
                rider_config["port"],
                int(rider_config["baud"]),
                float(rider_config["timeout_sec"]),
            )
            time.sleep(RIDER_CONNECT_SETTLE_SEC)
        except Exception as error:
            print(f"[rider] disabled for this run: {error}")

    if not args.no_rpi:
        rpi_worker = RpiTraySubscriber(
            endpoint=args.rpi_endpoint,
            output_queue=rpi_queue,
            stop_event=stop_event,
        )
        rpi_worker.start()
        workers.append(rpi_worker)

        rpi_command_link = RpiCommandLink(
            args.rpi_command_endpoint
        )

    vision_config = config["vision"]
    if vision_config.get("enabled"):
        vision_worker = RetailCustomerSubscriber(
            endpoint=vision_config["subscriber_endpoint"],
            event_queue=event_queue,
            session_queue=customer_session_queue,
            stop_event=stop_event,
            latest_state=latest_vision,
            topic=vision_config.get("topic", "retail"),
        )
        vision_worker.start()
        workers.append(vision_worker)

    emergency_endpoint = (
        args.vision_emergency_endpoint
        or vision_config.get("emergency_endpoint")
    )

    def on_emergency_result(result: dict[str, Any]) -> None:
        logger.write({
            "stage": "vision_emergency",
            **result,
        })

        if result.get("ok"):
            response = result.get("response", {})
            dashboard.record_event(
                "EMERGENCY_DELIVERED",
                (
                    f"Vision emergency delivered for customer "
                    f"{result.get('customer_id')}"
                ),
                level="SUCCESS",
                source="vision",
                details=result,
            )
            print(
                "[emergency] response "
                + json.dumps(response, ensure_ascii=False)
            )
        else:
            dashboard.alert(
                "EMERGENCY_DELIVERY_FAILED",
                (
                    f"Vision emergency failed for customer "
                    f"{result.get('customer_id')}"
                ),
                severity="WARNING",
                details=result,
            )

    if emergency_endpoint:
        emergency_dispatcher = EmergencyDispatcher(
            VisionEmergencyClient(
                str(emergency_endpoint),
                timeout_ms=args.emergency_timeout_ms,
                retries=args.emergency_retries,
            ),
            callback=on_emergency_result,
        )
        emergency_dispatcher.start()
        print(f"[emergency] REQ {emergency_endpoint}")

    console_thread = threading.Thread(
        target=manual_console,
        kwargs={
            "event_queue": event_queue,
            "order_queue": order_queue,
            "action_queue": action_queue,
            "stop_event": stop_event,
        },
        daemon=True,
    )
    console_thread.start()

    active_customer_id: int | None = None
    paid_by_customer: dict[int, dict[str, int]] = {}
    pending_exits: list[dict[str, Any]] = []
    unassigned_payment: tuple[
        dict[str, int],
        float,
    ] | None = None

    try:
        while not stop_event.is_set():
            # Raspberry Pi state
            try:
                while True:
                    message = rpi_queue.get_nowait()
                    latest_rpi.clear()
                    latest_rpi.update(message)
                    dashboard.update_rpi(message)
                    logger.write({
                        "stage": "rpi_tray",
                        **message,
                    })
            except queue.Empty:
                pass

            # Vision POS/EXIT session transitions
            try:
                while True:
                    session = customer_session_queue.get_nowait()
                    kind = str(session.get("kind", "")).upper()
                    customer_id = int(session["customer_id"])

                    if kind == "CUSTOMER_POS":
                        active_customer_id = customer_id
                        dashboard.customer_started(customer_id)
                        dashboard.customer_at_pos(
                            customer_id,
                            session.get("picked", {}),
                        )

                        if unassigned_payment is not None:
                            payment, payment_time = unassigned_payment
                            if (
                                time.monotonic() - payment_time
                                <= PAYMENT_ASSOCIATION_WINDOW_SEC
                            ):
                                paid_by_customer[customer_id] = payment
                                dashboard.customer_paid(
                                    customer_id,
                                    payment,
                                )
                                print(
                                    f"[customer] matched pending payment "
                                    f"to customer={customer_id}: {payment}"
                                )
                                unassigned_payment = None

                    elif kind == "CUSTOMER_EXIT":
                        # Allow serial PAY_DONE already in transit to be handled
                        # before the final unpaid decision.
                        pending_exits.append({
                            **session,
                            "due_at": (
                                time.monotonic()
                                + CUSTOMER_EXIT_GRACE_SEC
                            ),
                        })
                        print(
                            f"[customer] exit scheduled "
                            f"customer={customer_id} "
                            f"picked={session.get('picked')}"
                        )

            except queue.Empty:
                pass

            # Delayed customer exit evaluation
            current_time = time.monotonic()
            remaining_exits: list[dict[str, Any]] = []

            for session in pending_exits:
                if current_time < float(session["due_at"]):
                    remaining_exits.append(session)
                    continue

                customer_id = int(session["customer_id"])
                picked = normalize_counts(session.get("picked"))
                paid = paid_by_customer.get(customer_id)

                if paid is None and unassigned_payment is not None:
                    pending_payment, pending_time = unassigned_payment
                    if (
                        current_time - pending_time
                        <= PAYMENT_ASSOCIATION_WINDOW_SEC
                    ):
                        paid = pending_payment
                        unassigned_payment = None

                paid = normalize_counts(paid)

                result = dashboard.finalize_customer_exit(
                    customer_id,
                    picked,
                    paid,
                    was_at_kiosk=bool(
                        session.get("was_at_kiosk")
                    ),
                    exit_event=session.get("event"),
                )
                logger.write({
                    "stage": "customer_exit_result",
                    "customer_id": customer_id,
                    **result,
                })

                if result["severity"] == "CRITICAL":
                    send_rider_command(rider_link, "LED:RED")

                    if rpi_command_link is not None:
                        rpi_command_link.send({
                            "command": "PLAY_AUDIO",
                            "event": "TRAY_MISMATCH",
                            "reason": result["code"],
                            "customer_id": customer_id,
                        })

                    if emergency_dispatcher is not None:
                        emergency_dispatcher.submit(
                            customer_id=customer_id,
                            reason=result["code"],
                            details=result,
                        )

                paid_by_customer.pop(customer_id, None)
                if active_customer_id == customer_id:
                    active_customer_id = None

            pending_exits = remaining_exits

            # Manual/ordering commands
            try:
                while True:
                    order = order_queue.get_nowait()
                    commands = state_manager.set_order(order)
                    send_rider_commands(rider_link, commands)
                    dashboard.update_fusion(state_manager.state)
            except queue.Empty:
                pass

            try:
                while True:
                    action = action_queue.get_nowait()
                    action_name = str(
                        action.get("action", "")
                    ).lower()

                    if action_name == "status":
                        print(json.dumps(
                            state_manager.state.__dict__,
                            ensure_ascii=False,
                            indent=2,
                        ))
                    elif action_name == "rpi":
                        print(json.dumps(
                            latest_rpi,
                            ensure_ascii=False,
                            indent=2,
                        ))
                    elif action_name == "vision":
                        print(json.dumps(
                            latest_vision,
                            ensure_ascii=False,
                            indent=2,
                        ))
                    elif (
                        action_name == "rpi-reset"
                        and rpi_command_link is not None
                    ):
                        rpi_command_link.send({
                            "command": "SYSTEM_RESET",
                        })
                    elif (
                        action_name == "audio"
                        and rpi_command_link is not None
                    ):
                        rpi_command_link.send({
                            "command": "PLAY_AUDIO",
                            "event": action["event"],
                        })
                    elif action_name == "emergency":
                        if emergency_dispatcher is None:
                            print(
                                "[emergency] endpoint is not configured"
                            )
                        else:
                            emergency_dispatcher.submit(
                                customer_id=int(
                                    action["customer_id"]
                                ),
                                reason="MANUAL_TEST",
                            )
            except queue.Empty:
                pass

            # POS and generated Vision events
            try:
                event = event_queue.get(timeout=0.2)
            except queue.Empty:
                dashboard.tick()
                continue

            previous_pos_done = bool(
                getattr(
                    state_manager.state,
                    "pos_payment_done",
                    False,
                )
            )

            logger.write({
                "stage": "event",
                **event.to_dict(),
            })

            commands = state_manager.handle(event)
            dashboard.update_fusion(state_manager.state)

            for command in commands:
                logger.write({
                    "stage": "command",
                    "target": command.target,
                    "command": command.command,
                    "reason": command.reason,
                })

            send_rider_commands(rider_link, commands)

            current_pos_done = bool(
                getattr(
                    state_manager.state,
                    "pos_payment_done",
                    False,
                )
            )
            current_mode = str(
                getattr(state_manager.state, "mode", "")
            ).upper()

            if (
                not previous_pos_done
                and current_pos_done
                and current_mode == "CUSTOMER"
            ):
                payment = choose_customer_payment(
                    state_manager.state
                )

                if active_customer_id is not None:
                    paid_by_customer[
                        active_customer_id
                    ] = payment
                    dashboard.customer_paid(
                        active_customer_id,
                        payment,
                    )
                    print(
                        f"[customer] payment customer="
                        f"{active_customer_id}: {payment}"
                    )
                else:
                    unassigned_payment = (
                        payment,
                        time.monotonic(),
                    )
                    print(
                        "[customer] payment waiting for Vision POS: "
                        f"{payment}"
                    )

                if rpi_command_link is not None:
                    rpi_command_link.send({
                        "command": "PAYMENT_CONFIRMED",
                        "expected": payment,
                    })

            if event.kind == "SYSTEM_RESET":
                active_customer_id = None
                paid_by_customer.clear()
                pending_exits.clear()
                unassigned_payment = None
                dashboard.system_reset()

                if rpi_command_link is not None:
                    rpi_command_link.send({
                        "command": "SYSTEM_RESET",
                    })

            dashboard.tick()

    except KeyboardInterrupt:
        stop_event.set()

    finally:
        stop_event.set()

        for worker in workers:
            if hasattr(worker, "stop"):
                worker.stop()

        if rider_link is not None:
            rider_link.close()

        if rpi_command_link is not None:
            rpi_command_link.close()

        if emergency_dispatcher is not None:
            emergency_dispatcher.stop()
            emergency_dispatcher.join(timeout=2.0)

        dashboard.stop()


if __name__ == "__main__":
    main()

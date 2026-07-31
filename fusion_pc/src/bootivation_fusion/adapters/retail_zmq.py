from __future__ import annotations

import json
import queue
import threading
from collections.abc import MutableMapping
from typing import Any

import zmq

from bootivation_fusion.adapters.parsers import parse_vision_message
from bootivation_fusion.domain.events import Event


PRODUCTS = ("A", "B", "C")
FINAL_STATES = {"POS", "EXIT"}


def normalize_counts(payload: dict[str, Any]) -> dict[str, int]:
    return {
        "A": max(0, int(payload.get("zone_A_picks", 0))),
        "B": max(0, int(payload.get("zone_B_picks", 0))),
        "C": max(0, int(payload.get("zone_C_picks", 0))),
    }


class RetailCustomerSubscriber(threading.Thread):
    """Receive final Vision customer transitions from ZMQ port 5555.

    Wire format:
        retail {"timestamp": ..., "customer_id": ..., "state": "POS"|"EXIT", ...}

    The final upstream publishes one POS transition and one EXIT transition per
    customer. The subscriber stores the last cumulative PICK counts and converts
    only positive deltas into REMOVE_CANDIDATE events. This preserves Rider
    integration while treating the EXIT packet as the authoritative final count.
    """

    REQUIRED_FIELDS = {
        "timestamp",
        "customer_id",
        "state",
        "active",
        "visit_state",
        "zone_A_picks",
        "zone_B_picks",
        "zone_C_picks",
        "at_kiosk",
    }

    def __init__(
        self,
        *,
        endpoint: str,
        event_queue: queue.Queue[Event],
        session_queue: queue.Queue[dict[str, Any]],
        stop_event: threading.Event,
        latest_state: MutableMapping[str, Any],
        topic: str = "retail",
    ) -> None:
        super().__init__(name="vision-retail-zmq", daemon=True)
        self.endpoint = endpoint
        self.event_queue = event_queue
        self.session_queue = session_queue
        self.stop_event = stop_event
        self.latest_state = latest_state
        self.topic = topic.strip() or "retail"

        self._last_counts: dict[int, dict[str, int]] = {}
        self._pos_seen: set[int] = set()
        self._seen_transitions: set[tuple[int, str, float]] = set()

        context = zmq.Context.instance()
        self._socket = context.socket(zmq.SUB)
        self._socket.setsockopt(zmq.LINGER, 0)
        self._socket.setsockopt_string(zmq.SUBSCRIBE, self.topic + " ")

    def stop(self) -> None:
        self.stop_event.set()

    @classmethod
    def parse_wire_message(
        cls,
        raw_message: str,
        *,
        expected_topic: str,
    ) -> dict[str, Any]:
        try:
            topic, json_text = raw_message.split(" ", 1)
        except ValueError as error:
            raise ValueError(
                "Vision message does not contain '<topic> <json>'."
            ) from error

        if topic != expected_topic:
            raise ValueError(
                f"Unexpected Vision topic: {topic!r}; expected {expected_topic!r}."
            )

        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError as error:
            raise ValueError(f"Malformed Vision JSON: {error}") from error

        if not isinstance(payload, dict):
            raise ValueError("Vision JSON body must be an object.")

        missing = cls.REQUIRED_FIELDS.difference(payload)
        if missing:
            raise ValueError(
                "Vision payload missing fields: "
                + ", ".join(sorted(missing))
            )

        state = str(payload["state"]).strip().upper()
        if state not in FINAL_STATES:
            raise ValueError(
                f"Unsupported Vision state: {state!r}; expected POS or EXIT."
            )

        return {
            "timestamp": float(payload["timestamp"]),
            "customer_id": int(payload["customer_id"]),
            "state": state,
            "active": bool(payload["active"]),
            "visit_state": str(payload["visit_state"]),
            "zone_A_picks": max(0, int(payload["zone_A_picks"])),
            "zone_B_picks": max(0, int(payload["zone_B_picks"])),
            "zone_C_picks": max(0, int(payload["zone_C_picks"])),
            "at_kiosk": bool(payload["at_kiosk"]),
            "event": payload.get("event"),
        }

    def _emit_event(self, raw_event: str) -> None:
        event = parse_vision_message(raw_event)
        if event is None:
            print(f"[vision] parser rejected generated event: {raw_event}")
            return
        self.event_queue.put(event)
        print(f"[vision] EVENT {raw_event}")

    def _emit_pick_deltas(
        self,
        *,
        customer_id: int,
        current_counts: dict[str, int],
    ) -> None:
        previous = self._last_counts.get(
            customer_id,
            {"A": 0, "B": 0, "C": 0},
        )

        for product in PRODUCTS:
            delta = current_counts[product] - previous[product]
            if delta > 0:
                print(
                    f"[vision] PICK delta customer={customer_id} "
                    f"product={product} +{delta}"
                )
                for _ in range(delta):
                    self._emit_event(f"REMOVE_CANDIDATE:{product}")
            elif delta < 0:
                # The final Vision protocol has no RETURN event. Count decreases
                # are logged but never converted into negative inventory changes.
                print(
                    f"[vision] PICK correction ignored customer={customer_id} "
                    f"product={product} {previous[product]}->{current_counts[product]}"
                )

        self._last_counts[customer_id] = dict(current_counts)

    def _process_transition(self, customer: dict[str, Any]) -> None:
        customer_id = int(customer["customer_id"])
        state = str(customer["state"]).upper()
        timestamp = float(customer["timestamp"])
        transition_key = (customer_id, state, timestamp)

        if transition_key in self._seen_transitions:
            return
        self._seen_transitions.add(transition_key)

        self.latest_state.clear()
        self.latest_state.update(customer)

        current_counts = normalize_counts(customer)
        self._emit_pick_deltas(
            customer_id=customer_id,
            current_counts=current_counts,
        )

        if state == "POS":
            self._pos_seen.add(customer_id)
            self._emit_event("ENTER:POS")
            self.session_queue.put({
                "kind": "CUSTOMER_POS",
                "timestamp": timestamp,
                "customer_id": customer_id,
                "picked": current_counts,
                "visit_state": customer["visit_state"],
            })
            print(
                f"[vision] POS customer={customer_id} "
                f"picked={current_counts}"
            )
            return

        self._emit_event("ENTER:EXIT")
        self.session_queue.put({
            "kind": "CUSTOMER_EXIT",
            "timestamp": timestamp,
            "customer_id": customer_id,
            "picked": current_counts,
            "event": customer.get("event"),
            "was_at_kiosk": customer_id in self._pos_seen,
        })
        print(
            f"[vision] EXIT customer={customer_id} "
            f"picked={current_counts} event={customer.get('event')}"
        )

        self._last_counts.pop(customer_id, None)
        self._pos_seen.discard(customer_id)

    def run(self) -> None:
        try:
            self._socket.connect(self.endpoint)
            print(
                f"[vision] SUB {self.endpoint} "
                f"topic={self.topic!r}"
            )

            poller = zmq.Poller()
            poller.register(self._socket, zmq.POLLIN)

            while not self.stop_event.is_set():
                events = dict(poller.poll(300))
                if self._socket not in events:
                    continue

                try:
                    raw_message = self._socket.recv_string(
                        flags=zmq.NOBLOCK
                    )
                except zmq.Again:
                    continue

                try:
                    customer = self.parse_wire_message(
                        raw_message,
                        expected_topic=self.topic,
                    )
                except (TypeError, ValueError) as error:
                    print(f"[vision] parse failed: {error}")
                    continue

                self._process_transition(customer)

        except Exception as error:
            print(f"[vision] subscriber stopped: {error}")
        finally:
            self._socket.close(0)

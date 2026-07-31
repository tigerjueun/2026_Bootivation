from __future__ import annotations

import queue
import threading
import time
from collections.abc import Callable
from typing import Any

import zmq


class VisionEmergencyClient:
    """REQ/REP client for the Vision WebUI emergency receiver on port 5556."""

    def __init__(
        self,
        endpoint: str,
        *,
        timeout_ms: int = 3000,
        retries: int = 1,
    ) -> None:
        self.endpoint = endpoint
        self.timeout_ms = max(100, int(timeout_ms))
        self.retries = max(0, int(retries))
        self.context = zmq.Context.instance()

    def _new_socket(self) -> zmq.Socket:
        socket = self.context.socket(zmq.REQ)
        socket.setsockopt(zmq.LINGER, 0)
        socket.setsockopt(zmq.SNDTIMEO, self.timeout_ms)
        socket.setsockopt(zmq.RCVTIMEO, self.timeout_ms)
        socket.connect(self.endpoint)
        return socket

    def send(
        self,
        customer_id: int,
        *,
        timestamp: float | None = None,
    ) -> dict[str, Any]:
        payload = {
            "Emergency": True,
            "customer_id": int(customer_id),
            "timestamp": float(
                time.time() if timestamp is None else timestamp
            ),
        }

        last_error: Exception | None = None

        for attempt in range(self.retries + 1):
            socket = self._new_socket()
            try:
                socket.send_json(payload)
                response = socket.recv_json()

                if not isinstance(response, dict):
                    raise RuntimeError(
                        "Vision emergency response must be a JSON object."
                    )

                if not bool(response.get("ok")):
                    raise RuntimeError(
                        "Vision rejected emergency request: "
                        + str(response.get("error", "unknown error"))
                    )

                return response

            except (zmq.Again, RuntimeError, ValueError) as error:
                last_error = error
                if attempt < self.retries:
                    print(
                        f"[emergency] retry {attempt + 1}/"
                        f"{self.retries}: {error}"
                    )
            finally:
                # A REQ socket that timed out cannot safely be reused. Always
                # close it and create a fresh socket for a retry.
                socket.close(0)

        raise RuntimeError(
            f"Vision emergency request failed: {last_error}"
        )


class EmergencyDispatcher(threading.Thread):
    """Background dispatcher so a 5556 timeout never blocks the Fusion loop."""

    def __init__(
        self,
        client: VisionEmergencyClient,
        *,
        callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        super().__init__(name="vision-emergency-dispatcher", daemon=True)
        self.client = client
        self.callback = callback
        self.jobs: queue.Queue[dict[str, Any] | None] = queue.Queue()
        self.stop_event = threading.Event()

    def submit(
        self,
        *,
        customer_id: int,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.jobs.put({
            "customer_id": int(customer_id),
            "reason": str(reason),
            "details": dict(details or {}),
            "queued_at": time.time(),
        })

    def stop(self) -> None:
        self.stop_event.set()
        self.jobs.put(None)

    def run(self) -> None:
        while not self.stop_event.is_set():
            try:
                job = self.jobs.get(timeout=0.3)
            except queue.Empty:
                continue

            if job is None:
                return

            result: dict[str, Any]
            try:
                response = self.client.send(
                    int(job["customer_id"]),
                    timestamp=float(job["queued_at"]),
                )
                result = {
                    "ok": True,
                    "customer_id": int(job["customer_id"]),
                    "reason": job["reason"],
                    "details": job["details"],
                    "response": response,
                }
                print(
                    "[emergency] delivered "
                    f"customer={job['customer_id']} "
                    f"snapshot_available="
                    f"{response.get('snapshot_available')}"
                )
            except Exception as error:
                result = {
                    "ok": False,
                    "customer_id": int(job["customer_id"]),
                    "reason": job["reason"],
                    "details": job["details"],
                    "error": str(error),
                }
                print(
                    "[emergency] failed "
                    f"customer={job['customer_id']}: {error}"
                )

            if self.callback is not None:
                try:
                    self.callback(result)
                except Exception as error:
                    print(f"[emergency] callback failed: {error}")

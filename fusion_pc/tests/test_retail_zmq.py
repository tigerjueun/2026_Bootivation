from __future__ import annotations

import json
import queue
import sys
import threading
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from bootivation_fusion.adapters.retail_zmq import RetailCustomerSubscriber


class RetailCustomerSubscriberTests(unittest.TestCase):
    def make_message(self, **overrides) -> str:
        payload = {
            "timestamp": 1784902657.924002,
            "customer_id": 100,
            "state": "POS",
            "active": True,
            "visit_state": "inside",
            "zone_A_picks": 2,
            "zone_B_picks": 1,
            "zone_C_picks": 1,
            "at_kiosk": True,
            "event": None,
        }
        payload.update(overrides)
        return "retail " + json.dumps(payload)

    def test_parse_pos_transition(self) -> None:
        parsed = RetailCustomerSubscriber.parse_wire_message(
            self.make_message(),
            expected_topic="retail",
        )
        self.assertEqual(parsed["customer_id"], 100)
        self.assertEqual(parsed["state"], "POS")
        self.assertEqual(parsed["zone_A_picks"], 2)
        self.assertTrue(parsed["at_kiosk"])

    def test_parse_exit_transition(self) -> None:
        parsed = RetailCustomerSubscriber.parse_wire_message(
            self.make_message(
                state="EXIT",
                active=False,
                visit_state="released",
                event="exit",
            ),
            expected_topic="retail",
        )
        self.assertEqual(parsed["state"], "EXIT")
        self.assertFalse(parsed["active"])
        self.assertEqual(parsed["event"], "exit")

    def test_reject_wrong_topic(self) -> None:
        with self.assertRaises(ValueError):
            RetailCustomerSubscriber.parse_wire_message(
                self.make_message().replace("retail ", "other ", 1),
                expected_topic="retail",
            )

    def test_require_final_state_field(self) -> None:
        payload = json.loads(self.make_message().split(" ", 1)[1])
        payload.pop("state")

        with self.assertRaises(ValueError):
            RetailCustomerSubscriber.parse_wire_message(
                "retail " + json.dumps(payload),
                expected_topic="retail",
            )

    def test_reject_non_final_state(self) -> None:
        with self.assertRaises(ValueError):
            RetailCustomerSubscriber.parse_wire_message(
                self.make_message(state="INSIDE"),
                expected_topic="retail",
            )

    def test_pick_delta_preserves_quantity(self) -> None:
        events = queue.Queue()
        subscriber = RetailCustomerSubscriber(
            endpoint="inproc://unused-retail-test",
            event_queue=events,
            session_queue=queue.Queue(),
            stop_event=threading.Event(),
            latest_state={},
        )

        try:
            subscriber._emit_pick_deltas(
                customer_id=100,
                current_counts={"A": 2, "B": 0, "C": 0},
            )
            event = events.get_nowait()
            self.assertEqual(event.kind, "REMOVE_CANDIDATE")
            self.assertEqual(event.item, "A")
            self.assertEqual(event.qty, 2)
            self.assertTrue(events.empty())
        finally:
            subscriber._socket.close(0)


if __name__ == "__main__":
    unittest.main()

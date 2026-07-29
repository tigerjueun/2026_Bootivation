from __future__ import annotations

import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from bootivation_fusion.adapters.parsers import parse_pos_line
from bootivation_fusion.core.state_manager import StateManager


def feed(manager: StateManager, lines: list[str]):
    commands = []
    for line in lines:
        event = parse_pos_line(line)
        if event is not None:
            commands.extend(manager.handle(event))
    return commands


class PosProtocolV2Tests(unittest.TestCase):
    def test_customer_summary_not_double_counted(self) -> None:
        manager = StateManager(rider_pick_source="pos")
        feed(manager, [
            "BOOT,ATMEGA128_POS_C",
            "SESSION,START,ID=2",
            "USER,CUSTOMER",
            "PAY:C",
            "COUNT,A=0,B=0,C=1,TOTAL=1",
            "PAY:A",
            "PAY:B",
            "PAY:B",
            "PAY_DONE",
            "PAY_DONE,USER=CUSTOMER,A=1,B=2,C=1,TOTAL=4,SESSION=2",
        ])
        self.assertEqual(manager.state.paid_items, {"A": 1, "B": 2, "C": 1})
        self.assertEqual(manager.state.payment_batches, 1)
        self.assertEqual(manager.state.pos_reported_total, 4)

    def test_manual_pos_reset_rolls_back_uncommitted_items(self) -> None:
        manager = StateManager(rider_pick_source="pos")
        manager.set_order({"A": 1, "C": 1})
        feed(manager, [
            "SESSION,START,ID=1",
            "USER,RIDER",
            "PAY:A",
            "PAY:C",
            "SESSION_RESET",
            "SESSION,START,ID=2",
        ])
        self.assertEqual(manager.state.rider_removed, {"A": 0, "B": 0, "C": 0})
        self.assertEqual(manager.state.pos_session_items, {"A": 0, "B": 0, "C": 0})

    def test_rider_pos_completion(self) -> None:
        manager = StateManager(rider_pick_source="pos")
        manager.set_order({"A": 1, "B": 1})
        commands = feed(manager, [
            "SESSION,START,ID=1",
            "USER,RIDER",
            "PAY:A",
            "PAY:B",
            "PAY_DONE",
            "PAY_DONE,USER=RIDER,A=1,B=1,C=0,TOTAL=2,SESSION=1",
        ])
        self.assertEqual(manager.state.rider_removed, {"A": 1, "B": 1, "C": 0})
        self.assertEqual(manager.state.result, "PICKUP_COMPLETE")
        self.assertIn("LED:GREEN", [command.command for command in commands])
        self.assertIn("SERVO:HOME", [command.command for command in commands])

    def test_wrong_rider_item_turns_red(self) -> None:
        manager = StateManager(rider_pick_source="pos")
        manager.set_order({"A": 1})
        commands = feed(manager, [
            "SESSION,START,ID=1",
            "USER,RIDER",
            "PAY:C",
        ])
        self.assertEqual(manager.state.result, "WRONG_PICKUP:C")
        self.assertIn("LED:RED", [command.command for command in commands])

    def test_legacy_protocol_remains_supported(self) -> None:
        manager = StateManager(rider_pick_source="vision")
        feed(manager, ["MODE:CUSTOMER", "PAY:A", "PAY_DONE"])
        self.assertEqual(manager.state.paid_items["A"], 1)
        self.assertEqual(manager.state.payment_batches, 1)


if __name__ == "__main__":
    unittest.main()

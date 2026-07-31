from __future__ import annotations

import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from bootivation_fusion.adapters.parsers import parse_pos_line, parse_vision_message
from bootivation_fusion.core.state_manager import StateManager


def feed_pos(manager: StateManager, lines: list[str]):
    commands = []
    for line in lines:
        event = parse_pos_line(line)
        if event is not None:
            commands.extend(manager.handle(event))
    return commands


def feed_vision(manager: StateManager, lines: list[str]):
    commands = []
    for line in lines:
        event = parse_vision_message(line)
        if event is not None:
            commands.extend(manager.handle(event))
    return commands


class RiderThreeWayVerificationTests(unittest.TestCase):
    def test_customer_summary_not_double_counted(self) -> None:
        manager = StateManager(rider_pick_source="vision")
        feed_pos(manager, [
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

    def test_vision_collection_advances_but_waits_for_pos(self) -> None:
        manager = StateManager(rider_pick_source="vision", cooldown_sec=0.0)
        start = manager.set_order({"A": 1, "B": 1})
        self.assertEqual([c.command for c in start], ["LED:BLUE", "SERVO:A"])

        first = feed_vision(manager, ["REMOVE_CANDIDATE:A"])
        self.assertIn("SERVO:B", [c.command for c in first])
        self.assertEqual(manager.state.rider_removed, {"A": 1, "B": 0, "C": 0})

        second = feed_vision(manager, ["REMOVE_CANDIDATE:B"])
        self.assertEqual(manager.state.result, "RIDER_COLLECTED_WAIT_POS")
        self.assertIn("SERVO:HOME", [c.command for c in second])
        self.assertNotIn("LED:GREEN", [c.command for c in second])

    def test_final_green_requires_order_vision_and_pos_match(self) -> None:
        manager = StateManager(rider_pick_source="vision", cooldown_sec=0.0)
        manager.set_order({"A": 1, "B": 1})
        feed_vision(manager, ["REMOVE_CANDIDATE:A", "REMOVE_CANDIDATE:B"])

        commands = feed_pos(manager, [
            "SESSION,START,ID=1",
            "USER,RIDER",
            "PAY:A",
            "PAY:B",
            "PAY_DONE",
            "PAY_DONE,USER=RIDER,A=1,B=1,C=0,TOTAL=2,SESSION=1",
        ])
        self.assertEqual(manager.state.rider_checked_items, {"A": 1, "B": 1, "C": 0})
        self.assertEqual(manager.state.result, "PICKUP_COMPLETE")
        self.assertIn("LED:GREEN", [c.command for c in commands])
        self.assertIn("SERVO:HOME", [c.command for c in commands])

    def test_wrong_physical_item_turns_red(self) -> None:
        manager = StateManager(rider_pick_source="vision", cooldown_sec=0.0)
        manager.set_order({"A": 1})
        commands = feed_vision(manager, ["REMOVE_CANDIDATE:C"])
        self.assertEqual(manager.state.result, "WRONG_PICKUP:C")
        self.assertIn("LED:RED", [c.command for c in commands])

    def test_wrong_pos_check_turns_red(self) -> None:
        manager = StateManager(rider_pick_source="vision", cooldown_sec=0.0)
        manager.set_order({"A": 1})
        feed_vision(manager, ["REMOVE_CANDIDATE:A"])
        commands = feed_pos(manager, [
            "SESSION,START,ID=1",
            "USER,RIDER",
            "PAY:C",
        ])
        self.assertEqual(manager.state.result, "RIDER_POS_WRONG_ITEM:C")
        self.assertIn("LED:RED", [c.command for c in commands])

    def test_pos_reset_rolls_back_check_but_keeps_physical_removal(self) -> None:
        manager = StateManager(rider_pick_source="vision", cooldown_sec=0.0)
        manager.set_order({"A": 1})
        feed_vision(manager, ["REMOVE_CANDIDATE:A"])
        feed_pos(manager, [
            "SESSION,START,ID=1",
            "USER,RIDER",
            "PAY:A",
            "SESSION_RESET",
        ])
        self.assertEqual(manager.state.rider_removed, {"A": 1, "B": 0, "C": 0})
        self.assertEqual(manager.state.rider_checked_items, {"A": 0, "B": 0, "C": 0})

    def test_inventory_ledger_updates_on_physical_removal(self) -> None:
        manager = StateManager(rider_pick_source="vision", cooldown_sec=0.0)
        manager.set_order({"A": 1})
        feed_vision(manager, ["REMOVE_CANDIDATE:A"])
        self.assertEqual(manager.state.inventory_removed_items["A"], 1)

    def test_legacy_customer_protocol_remains_supported(self) -> None:
        manager = StateManager(rider_pick_source="vision")
        feed_pos(manager, ["MODE:CUSTOMER", "PAY:A", "PAY_DONE"])
        self.assertEqual(manager.state.paid_items["A"], 1)
        self.assertEqual(manager.state.payment_batches, 1)


if __name__ == "__main__":
    unittest.main()

import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("counterparties", HERE / "counterparties.py")
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class CounterpartyTests(unittest.TestCase):
    def setUp(self):
        self.capture = tool.activity.read_capture(
            HERE.parent / "transfer-crosscheck" / "publicnode.json")

    def rebuild(self):
        events, duplicates = tool.window.validate_logs(
            self.capture["raw_logs"], self.capture["decimals"],
            self.capture["token_address"], self.capture["from_block"],
            self.capture["to_block"])
        self.capture.update(transfers=events, transfer_count=len(events), duplicate_count=duplicates)

    def test_real_demo(self):
        result = tool.report(self.capture)
        self.assertEqual(result["directed_pair_count"], 3)
        self.assertEqual(result["matching_transfer_count"], 3)
        self.assertEqual(sum(int(r["total_raw"]) for r in result["flows"]),
                         sum(int(e["raw_value"]) for e in self.capture["transfers"]))

    def test_filter_and_normalize(self):
        selected = self.capture["transfers"][0]["from"]
        result = tool.report(self.capture, "0x" + selected[2:].upper())
        self.assertEqual(result["selected_address"], selected)
        self.assertEqual(result["matching_transfer_count"], 2)
        self.assertEqual(result["source_transfer_count"], 3)
        self.assertEqual(tool.report(self.capture, self.capture["token_address"])["flows"], [])

    def test_order_and_duplicate_delivery(self):
        expected = tool.report(self.capture)
        self.capture["raw_logs"].reverse()
        self.capture["raw_logs"].append(copy.deepcopy(self.capture["raw_logs"][0]))
        self.rebuild()
        self.assertEqual(tool.report(self.capture), expected)

    def test_same_pair_aggregation_and_uint256_precision(self):
        first = self.capture["raw_logs"][0]
        second = self.capture["raw_logs"][1]
        second["topics"] = copy.deepcopy(first["topics"])
        first["data"] = "0x" + format(2**256 - 1, "064x")
        second["data"] = first["data"]
        self.rebuild()
        row = next(r for r in tool.report(self.capture)["flows"] if r["from"] ==
                   self.capture["transfers"][0]["from"])
        self.assertEqual(row["transfer_count"], 2)
        self.assertEqual(row["total_raw"], str(2 * (2**256 - 1)))

    def test_self_transfer_counts_once(self):
        self.capture["raw_logs"] = self.capture["raw_logs"][:1]
        event = self.capture["raw_logs"][0]
        event["topics"][2] = event["topics"][1]
        self.rebuild()
        result = tool.report(self.capture, self.capture["transfers"][0]["from"])
        self.assertEqual(result["matching_transfer_count"], 1)
        self.assertTrue(result["flows"][0]["self_transfer"])

    def test_empty_window(self):
        self.capture["raw_logs"] = []
        self.rebuild()
        self.assertEqual(tool.report(self.capture)["flows"], [])

    def test_tamper_rejected(self):
        self.capture["transfers"][0]["raw_value"] = "1"
        with self.assertRaises(tool.window.RpcError):
            tool.report(self.capture)

    def test_removed_log_rejected(self):
        self.capture["raw_logs"][0]["removed"] = True
        with self.assertRaises(tool.window.RpcError):
            tool.report(self.capture)

    def test_outside_workspace_rejected_before_open(self):
        with self.assertRaisesRegex(ValueError, "inside this workspace"):
            tool.main(["--capture", "/outside/capture.json"])


if __name__ == "__main__":
    unittest.main()

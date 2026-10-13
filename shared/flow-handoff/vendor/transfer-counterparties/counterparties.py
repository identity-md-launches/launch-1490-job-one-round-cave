#!/usr/bin/env python3
"""Report directed counterparty flows in a validated bounded token window."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "line4_activity_for_counterparties",
    HERE.parent / "transfer-window-activity" / "activity.py")
activity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(activity)
window = activity.crosscheck.window


def report(capture, selected=None):
    """Validate raw evidence first; count unique transfers, never RPC duplicates."""
    checked = activity.crosscheck.checked(capture)
    if selected is not None:
        selected = window.address(selected)
    flows = {}
    for event in checked["transfers"]:
        sender, recipient = event["from"], event["to"]
        if selected is not None and selected not in (sender, recipient):
            continue
        key = (sender, recipient)
        flow = flows.setdefault(key, {
            "from": sender, "to": recipient, "transfer_count": 0,
            "total_raw": 0, "first_block": event["block"],
            "last_block": event["block"], "self_transfer": sender == recipient})
        flow["transfer_count"] += 1
        flow["total_raw"] += int(event["raw_value"])
        flow["last_block"] = event["block"]
    rows = []
    for key in sorted(flows):
        row = flows[key]
        raw = row["total_raw"]
        row["total_raw"] = str(raw)
        row["total"] = window.display_units(raw, checked["decimals"])
        rows.append(row)
    return {
        "kind": "erc20-transfer-window-counterparties", "schema_version": 1,
        "read_only": True, "validated": True, "chain_id": 1,
        "token": capture["token"], "token_address": checked["token_address"],
        "decimals": checked["decimals"], "selected_address": selected,
        "from_block": checked["from_block"], "to_block": checked["to_block"],
        "from_block_anchor": checked["from_block_anchor"],
        "to_block_anchor": checked["to_block_anchor"],
        "source_transfer_count": len(checked["transfers"]),
        "matching_transfer_count": sum(row["transfer_count"] for row in rows),
        "directed_pair_count": len(rows), "flows": rows,
        "limitations": "Event flows in the selected provider window only; not balances, "
        "holders, trades, pool volume, complete history, finality or proof of provider honesty. "
        "Repeated movement of the same tokens appears on each directed edge. "
        "Self-transfers count once; no address labels or ownership are inferred."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--demo", action="store_true")
    source.add_argument("--capture", type=Path)
    parser.add_argument("--address", type=window.address,
                        help="include only flows touching this public address")
    args = parser.parse_args(argv)
    path = HERE.parent / "transfer-crosscheck" / "publicnode.json" if args.demo else args.capture
    # Confine all file reads to the working tree; resolve symlinks before opening.
    root = HERE.parents[2]
    path = path.resolve()
    if not path.is_relative_to(root):
        raise ValueError("capture must be inside this workspace")
    print(json.dumps(report(activity.read_capture(path), args.address), indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, window.RpcError) as exc:
        print("transfer-counterparties: " + str(exc), file=sys.stderr)
        raise SystemExit(2)

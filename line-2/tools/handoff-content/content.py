#!/usr/bin/env python3
"""Compare verified HANDOFF payloads with separately retained content expectations."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import struct
import sys
import zipfile

FORMAT = "handoff-content-expectation-v1"
MAX_EXPECTATION = 512 * 1024
DEPENDENCY = "line-2/tools/handoff-inspect/inspect_handoff.py"


def workspace_path(raw):
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("use a relative workspace path without '..'")
    current = Path.cwd()
    for part in path.parts:
        current /= part
        if current.is_symlink():
            raise ValueError("symlinks are not allowed")
    return current


def inspector():
    spec = importlib.util.spec_from_file_location(
        "handoff_content_inspector", workspace_path(DEPENDENCY))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError("nonstandard JSON constant: " + value)


def parse_expectation(data):
    if len(data) > MAX_EXPECTATION:
        raise ValueError("expectation exceeds 512 KiB")
    obj = json.loads(data.decode("utf-8"), object_pairs_hook=unique,
                     parse_constant=invalid_constant)
    if (not isinstance(obj, dict) or set(obj) != {"format", "exact", "files"}
            or obj["format"] != FORMAT or type(obj["exact"]) is not bool
            or not isinstance(obj["files"], list) or not 1 <= len(obj["files"]) <= 1000):
        raise ValueError("invalid content expectation")
    seen = set()
    total = 0
    for entry in obj["files"]:
        if not isinstance(entry, dict) or set(entry) != {"path", "bytes", "sha256"}:
            raise ValueError("invalid expected file")
        name = entry["path"]
        if (not isinstance(name, str) or not name or name == "HANDOFF.json"
                or "\\" in name or ":" in name
                or any(p in ("", ".", "..") for p in name.split("/"))
                or any(ord(c) < 32 or ord(c) == 127 for c in name) or name in seen):
            raise ValueError("unsafe, duplicate or reserved expected path")
        if type(entry["bytes"]) is not int or entry["bytes"] < 0:
            raise ValueError("invalid expected size")
        digest = entry["sha256"]
        if not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest):
            raise ValueError("expected digest must be lowercase SHA-256")
        seen.add(name)
        total += entry["bytes"]
    if total > 64 * 1024 * 1024:
        raise ValueError("expected payload exceeds 64 MiB")
    return obj


def read_expectation(raw):
    fd = os.open(workspace_path(raw), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                 | getattr(os, "O_NONBLOCK", 0))
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise ValueError("only regular expectation files allowed")
    with os.fdopen(fd, "rb") as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("only regular expectation files allowed")
        data = handle.read(MAX_EXPECTATION + 1)
        after = os.fstat(handle.fileno())
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError("expectation changed during reading")
    return data


def compare(receipt, expectation_data):
    expectation = parse_expectation(expectation_data)
    wanted = {item["path"]: item for item in expectation["files"]}
    found = {item["path"]: item for item in receipt["files"]}
    missing = sorted(wanted.keys() - found.keys())
    unexpected = sorted(found.keys() - wanted.keys())
    matched, changed = [], []
    for name in sorted(wanted.keys() & found.keys()):
        if wanted[name] == found[name]:
            matched.append(name)
        else:
            changed.append({"path": name, "expected": wanted[name], "actual": found[name]})
    return {"format": "handoff-content-check-v1", "verified": True,
            "content_passed": not missing and not changed and
                              (not expectation["exact"] or not unexpected),
            "exact": expectation["exact"], "archive_sha256": receipt["archive_sha256"],
            "expectation_sha256": hashlib.sha256(expectation_data).hexdigest(),
            "matched": matched, "missing": missing, "unexpected": unexpected,
            "changed": changed,
            "note": "Integrity and expected bytes were checked; authenticity depends on "
                    "independently trusted expectations. No payload was extracted or executed."}


def check(archive, expectation, expected=None):
    data = read_expectation(expectation)
    parse_expectation(data)
    receipt = inspector().inspect_path(archive, expected=expected)
    return compare(receipt, data)


def capture(archive, exact=True, expected=None):
    receipt = inspector().inspect_path(archive, expected=expected)
    result = {"format": FORMAT, "exact": exact, "files": receipt["files"]}
    parse_expectation(json.dumps(result).encode())
    return result


def demo():
    result = check("line-2/handoff.zip", "line-2/tools/handoff-content/inherited-content.json")
    if not result["content_passed"]:
        raise ValueError("inherited archive differs from retained content expectations")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo")
    checking = commands.add_parser("check")
    checking.add_argument("archive")
    checking.add_argument("expectation")
    checking.add_argument("--sha256", help="independently trusted archive digest")
    capturing = commands.add_parser("capture", help="emit expectations from a verified archive")
    capturing.add_argument("archive")
    capturing.add_argument("--allow-extra", action="store_true")
    capturing.add_argument("--sha256", help="independently trusted archive digest")
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            result = demo()
        elif args.command == "check":
            result = check(args.archive, args.expectation, args.sha256)
        else:
            result = capture(args.archive, not args.allow_extra, args.sha256)
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0 if result.get("content_passed", True) else 2
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError,
            zipfile.BadZipFile, EOFError, NotImplementedError, struct.error) as error:
        print("handoff-content: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

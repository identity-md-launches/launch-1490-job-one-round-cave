#!/usr/bin/env python3
"""Carry exact raw ERC-20 evidence and recomputable directed flows offline."""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import sys
import zipfile

HERE = Path(__file__).resolve().parent
MAX_BYTES = 99_000
CAPTURE = 'evidence/window.json'
QUERY = 'review/query.json'
REPORT = 'review/flows.json'
SCHEMA = 'erc20-flow-handoff/1'
NOTE = ('Directed event flows in one provider window, not balances, holders, '
        'swaps, pool volume, complete history, finality or proof of provider '
        'honesty. An independently trusted digest is needed for sender identity. '
        'The same tokens may appear on several edges.')


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, HERE / 'vendor' / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


flows = load('flow_handoff_counterparties', 'transfer-counterparties/counterparties.py')
writer = load('flow_handoff_writer', 'handoff/handoff.py')
inspector = load('flow_handoff_inspector', 'handoff-inspect/inspect_handoff.py')
window = flows.window
LIMITS = inspector.Limits(archive_bytes=MAX_BYTES, payload_bytes=MAX_BYTES,
                         manifest_bytes=4096, metadata_bytes=4096, files=3)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=True, allow_nan=False) + '\n').encode('ascii')


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def reject_number(value):
    raise ValueError('floating point and non-finite JSON numbers are unsupported')


def parse(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError('JSON exceeds 99000 bytes')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=unique,
                      parse_constant=reject_number, parse_float=reject_number)


def selected_address(raw):
    if raw is None:
        return None
    try:
        return window.address(raw)
    except argparse.ArgumentTypeError as error:
        raise ValueError('invalid public address selection') from error


def recompute(raw, selected):
    capture = parse(raw)
    checked = flows.activity.crosscheck.checked(capture)
    # Dict equality alone accepts True in place of 1 inside saved summaries.
    if canonical(capture['transfers']) != canonical(checked['transfers']):
        raise ValueError('transfer summary JSON types differ from raw-log evidence')
    return flows.report(capture, selected)


def build(raw, selected=None):
    selected = selected_address(selected)
    report = recompute(raw, selected)
    query = {'schema': SCHEMA, 'selected_address': selected}
    archive = writer.build({CAPTURE: raw, QUERY: canonical(query),
                            REPORT: canonical(report)})
    inspect_bytes(archive)
    return archive


def inspect_bytes(data, expected=None, expected_address=None):
    # Verify bounded immutable bytes before reading any evidence payload.
    receipt = inspector.inspect_stream(io.BytesIO(data), LIMITS, expected)
    if {item['path'] for item in receipt['files']} != {CAPTURE, QUERY, REPORT}:
        raise ValueError('exact capture, query and flow payloads required')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        files = {item['path']: archive.read(item['path']) for item in receipt['files']}
    # The inherited writer also checks this fixed, portable serialization profile.
    if writer.build(files) != data:
        raise ValueError('archive does not reproduce under the original writer')
    query = parse(files[QUERY])
    if (not isinstance(query, dict) or set(query) != {'schema', 'selected_address'}
            or query['schema'] != SCHEMA):
        raise ValueError('invalid flow selection query')
    selected = selected_address(query['selected_address'])
    if files[QUERY] != canonical({'schema': SCHEMA, 'selected_address': selected}):
        raise ValueError('noncanonical selection query')
    if expected_address is not None and selected != selected_address(expected_address):
        raise ValueError('packaged filter differs from the requested public address')
    report = recompute(files[CAPTURE], selected)
    if files[REPORT] != canonical(report):
        raise ValueError('saved flows differ from recomputed raw-log evidence')
    return {'schema': SCHEMA, 'verified': True, 'network_used': False,
            'archive_sha256': receipt['archive_sha256'],
            'archive_bytes': receipt['archive_bytes'],
            'trusted_digest_matched': receipt['trusted_digest_matched'],
            'capture_bytes_sha256': hashlib.sha256(files[CAPTURE]).hexdigest(),
            'byte_reproducible': True, 'flows_recomputed': True,
            'address_expectation_matched': expected_address is not None,
            'flow_report': report, 'limitations': NOTE}


def read_workspace(raw):
    return writer.regular_bytes(writer.workspace_path(raw), MAX_BYTES)


def demo():
    raw = (HERE / 'examples/zto-window.json').read_bytes()
    archive = build(raw)
    if archive != build(raw):
        raise ValueError('nondeterministic packaging')
    result = inspect_bytes(archive)
    result['demo'] = 'Retained real ZTO provider observation; no network or files written.'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('demo')
    pack = commands.add_parser('pack')
    pack.add_argument('capture', help='relative public workspace JSON file')
    pack.add_argument('archive', help='new relative workspace ZIP file')
    pack.add_argument('--address', help='only edges touching this public address')
    check = commands.add_parser('check')
    check.add_argument('archive')
    check.add_argument('--sha256', help='independently trusted archive digest')
    check.add_argument('--address', help='require this public address as the packaged filter')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo()
        elif args.command == 'pack':
            target = writer.workspace_path(args.archive, must_exist=False)
            archive = build(read_workspace(args.capture), args.address)
            result = inspect_bytes(archive)
            with target.open('xb') as output:
                output.write(archive)
            result['output'] = args.archive
        else:
            result = inspect_bytes(read_workspace(args.archive), args.sha256, args.address)
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, UnicodeError,
            RecursionError, OverflowError, zipfile.BadZipFile, EOFError,
            NotImplementedError, struct.error):
        print('flow-handoff: invalid, over-limit or inconsistent evidence; no receipt emitted',
              file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

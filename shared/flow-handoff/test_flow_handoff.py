#!/usr/bin/env python3
"""Offline integration checks of raw evidence, immutable archives and the CLI."""
import copy
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import flow_handoff as kit


RAW = (kit.HERE / 'examples/zto-window.json').read_bytes()
POOL = '0x000000000004444c5dc75cb358380d2e3de08a90'


def payloads(data):
    with zipfile.ZipFile(io.BytesIO(data)) as source:
        return {item.filename: source.read(item) for item in source.infolist()
                if item.filename != 'HANDOFF.json'}


def rebuild(capture):
    """Synthetic mutations only; rederive summaries so tests reach deeper checks."""
    events, duplicates = kit.window.validate_logs(
        capture['raw_logs'], capture['decimals'], capture['token_address'],
        capture['from_block'], capture['to_block'])
    capture['transfers'] = events
    capture['transfer_count'] = len(events)
    capture['duplicate_count'] = duplicates
    return kit.canonical(capture)


class Tests(unittest.TestCase):
    def test_retained_real_zto_exact_bytes_determinism_and_provenance(self):
        with patch.object(kit.window, 'rpc', side_effect=AssertionError('network')):
            first = kit.build(RAW)
            self.assertEqual(first, kit.build(RAW))
            result = kit.inspect_bytes(first)
        self.assertEqual(payloads(first)[kit.CAPTURE], RAW)
        self.assertEqual(result['flow_report']['source_transfer_count'], 3)
        self.assertEqual(result['flow_report']['directed_pair_count'], 3)
        self.assertFalse(result['trusted_digest_matched'])
        self.assertEqual(result['capture_bytes_sha256'], hashlib.sha256(RAW).hexdigest())
        self.assertFalse(result['network_used'])

    def test_address_filter_is_normalized_and_receiver_can_require_it(self):
        archive = kit.build(RAW, '0x' + POOL[2:].upper())
        receipt = kit.inspect_bytes(archive, expected_address=POOL)
        report = receipt['flow_report']
        self.assertEqual(report['selected_address'], POOL)
        self.assertEqual(report['source_transfer_count'], 3)
        self.assertEqual(report['matching_transfer_count'], 1)
        self.assertEqual(report['flows'][0]['to'], POOL)
        self.assertEqual(report['flows'][0]['total_raw'], '133156484573036068537766')
        self.assertTrue(receipt['address_expectation_matched'])
        with self.assertRaises(ValueError):
            kit.inspect_bytes(archive, expected_address=kit.window.TOKENS['zto'])
        with self.assertRaises(ValueError):
            kit.inspect_bytes(kit.build(RAW), expected_address=POOL)

    def test_rehashed_false_report_is_rejected(self):
        files = payloads(kit.build(RAW))
        report = kit.parse(files[kit.REPORT])
        report['flows'][0]['total_raw'] = '1'
        files[kit.REPORT] = kit.canonical(report)
        data = kit.writer.build(files)
        kit.inspector.inspect_stream(io.BytesIO(data))  # Manifest integrity passes.
        with self.assertRaisesRegex(ValueError, 'recomputed'):
            kit.inspect_bytes(data)

    def test_rehashed_filter_switch_is_rejected(self):
        files = payloads(kit.build(RAW))
        files[kit.QUERY] = kit.canonical({'schema': kit.SCHEMA, 'selected_address': POOL})
        with self.assertRaises(ValueError):
            kit.inspect_bytes(kit.writer.build(files))

    def test_raw_log_tampering_fails_even_with_fresh_manifest(self):
        for change in ('removed', 'emitter', 'hash', 'amount'):
            files = payloads(kit.build(RAW))
            capture = kit.parse(files[kit.CAPTURE])
            log = capture['raw_logs'][0]
            if change == 'removed': log['removed'] = True
            if change == 'emitter': log['address'] = kit.window.TOKENS['imd']
            if change == 'hash': log['blockHash'] = capture['from_block_anchor']['hash']
            if change == 'amount': log['data'] = '0x' + format(1, '064x')
            files[kit.CAPTURE] = kit.canonical(capture)
            with self.subTest(change=change), self.assertRaises((ValueError, kit.window.RpcError)):
                kit.inspect_bytes(kit.writer.build(files))

    def test_duplicate_delivery_and_order_do_not_double_count(self):
        original = kit.inspect_bytes(kit.build(RAW))['flow_report']
        capture = kit.parse(RAW)
        capture['raw_logs'].reverse()
        capture['raw_logs'].append(copy.deepcopy(capture['raw_logs'][0]))
        raw = rebuild(capture)
        report = kit.inspect_bytes(kit.build(raw))['flow_report']
        self.assertEqual(report, original)
        self.assertEqual(payloads(kit.build(raw))[kit.CAPTURE], raw)

    def test_exact_aggregation_above_uint256_and_self_transfers(self):
        capture = kit.parse(RAW)
        sender = capture['raw_logs'][0]['topics'][1]
        for log in capture['raw_logs']:
            log['topics'][1] = sender
            log['topics'][2] = sender
            log['data'] = '0x' + format(2**256 - 1, '064x')
        report = kit.inspect_bytes(kit.build(rebuild(capture)))['flow_report']
        self.assertEqual(report['directed_pair_count'], 1)
        self.assertEqual(report['matching_transfer_count'], 3)
        flow = report['flows'][0]
        self.assertTrue(flow['self_transfer'])
        self.assertEqual(flow['total_raw'], str(3 * (2**256 - 1)))
        self.assertEqual(flow['transfer_count'], 3)

    def test_empty_and_imd_windows(self):
        for symbol in ('ZTO', 'IMD'):
            capture = kit.parse(RAW)
            capture['raw_logs'] = []
            capture['token'] = symbol
            capture['token_address'] = kit.window.TOKENS[symbol.lower()]
            report = kit.inspect_bytes(kit.build(rebuild(capture)))['flow_report']
            self.assertEqual(report['flows'], [])
            self.assertEqual(report['source_transfer_count'], 0)
            self.assertEqual(report['token'], symbol)

    def test_schema3_address_summary_is_revalidated(self):
        capture = kit.parse(RAW)
        capture['schema_version'] = 3
        capture['address_window_summary'] = kit.window.address_summary(
            capture['transfers'], POOL, capture['decimals'])
        self.assertTrue(kit.inspect_bytes(kit.build(kit.canonical(capture)))['verified'])
        capture['address_window_summary']['matching_transfer_count'] = True
        with self.assertRaises(kit.window.RpcError):
            kit.build(kit.canonical(capture))

    def test_boolean_event_integer_is_rejected(self):
        capture = kit.parse(RAW)
        capture['raw_logs'][0]['transactionIndex'] = '0x1'
        raw = rebuild(capture)
        capture = kit.parse(raw)
        capture['transfers'][0]['transaction_index'] = True
        # Native dict equality accepts this substitution; the wrapper does not.
        kit.flows.activity.crosscheck.checked(capture)
        with self.assertRaisesRegex(ValueError, 'JSON types'):
            kit.build(kit.canonical(capture))

    def test_trusted_digest_and_crc_failure(self):
        data = kit.build(RAW)
        digest = hashlib.sha256(data).hexdigest()
        self.assertTrue(kit.inspect_bytes(data, digest)['trusted_digest_matched'])
        with self.assertRaises(ValueError):
            kit.inspect_bytes(data, 'a' * 64)
        corrupted = bytearray(data)
        pos = data.index(b'26177298')
        corrupted[pos] ^= 1
        with self.assertRaises((ValueError, zipfile.BadZipFile)):
            kit.inspect_bytes(bytes(corrupted))

    def test_payload_contract_and_original_writer_profile(self):
        files = payloads(kit.build(RAW))
        for name in (kit.CAPTURE, kit.QUERY, kit.REPORT):
            altered = dict(files)
            del altered[name]
            with self.subTest(name=name), self.assertRaises(ValueError):
                kit.inspect_bytes(kit.writer.build(altered))
        extra = dict(files, **{'extra.txt': b'no'})
        with self.assertRaises(ValueError):
            kit.inspect_bytes(kit.writer.build(extra))
        result = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(kit.build(RAW))) as source, \
                zipfile.ZipFile(result, 'w') as target:
            for item in source.infolist():
                item.date_time = (2001, 1, 1, 0, 0, 0)
                target.writestr(item, source.read(item.filename))
        with self.assertRaisesRegex(ValueError, 'reproduce'):
            kit.inspect_bytes(result.getvalue())

    def test_strict_json_and_size_limits(self):
        for raw in (b'{"x":1,"x":2}', b'NaN', b'1e400', b'1.0', b'\xff',
                    b'x' * (kit.MAX_BYTES + 1)):
            with self.subTest(raw=raw[:30]), self.assertRaises(ValueError):
                kit.parse(raw)
        with self.assertRaises(ValueError):
            kit.inspect_bytes(b'x' * (kit.MAX_BYTES + 1))
        for address in ('bad', '', 1, POOL[:-1]):
            with self.assertRaises(ValueError):
                kit.build(RAW, address)
        capture = kit.parse(RAW)
        capture['note'] = 'x' * (kit.MAX_BYTES - len(RAW) - 100)
        with self.assertRaises(ValueError):
            kit.build(kit.canonical(capture))

    def test_cli_standalone_pack_check_and_failures(self):
        with tempfile.TemporaryDirectory(prefix='pepe-flow-test-', dir='/tmp') as raw:
            stage = Path(raw)
            shutil.copytree(kit.HERE, stage / 'kit', ignore=shutil.ignore_patterns('__pycache__'))
            (stage / 'capture.json').write_bytes(RAW)
            prefix = [sys.executable, '-B', 'kit/flow_handoff.py']
            def run(*args):
                return subprocess.run(prefix + list(args), cwd=stage,
                                      capture_output=True, text=True, timeout=20)
            self.assertEqual(run('demo').returncode, 0)
            packed = run('pack', 'capture.json', 'flows.zip', '--address', POOL)
            self.assertEqual(packed.returncode, 0, packed.stderr)
            digest = json.loads(packed.stdout)['archive_sha256']
            checked = run('check', 'flows.zip', '--sha256', digest, '--address', POOL)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            before = (stage / 'flows.zip').read_bytes()
            for args in [('pack','capture.json','flows.zip'),
                         ('check','flows.zip','--sha256','bad'),
                         ('check','flows.zip','--address',kit.window.TOKENS['imd']),
                         ('check','../outside'), ('check',str(stage / 'flows.zip'))]:
                failed = run(*args)
                self.assertEqual(failed.returncode, 1, args)
                self.assertEqual(failed.stdout, '')
                self.assertNotIn('Traceback', failed.stderr)
            (stage / 'link.zip').symlink_to('flows.zip')
            self.assertEqual(run('check','link.zip').returncode, 1)
            self.assertEqual((stage / 'flows.zip').read_bytes(), before)


if __name__ == '__main__':
    unittest.main(verbosity=2)

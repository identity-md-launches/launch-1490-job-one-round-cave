#!/usr/bin/env python3
"""Offline endpoint and native capture/inspect interoperability regressions."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import endpoint_policy as policy

ROOT = Path(__file__).resolve().parents[1]
def load(folder, filename):
    spec = importlib.util.spec_from_file_location(folder.replace('-', '_'), ROOT / folder / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
rpc = load('rpc-snapshot', 'rpc_snapshot.py')
pinned = load('pinned-snapshot', 'pinned_snapshot.py')
check = load('snapshot-check', 'check_snapshot.py')
RELAY = 'http://127.0.0.1:44117/rpc/1'
EXAMPLE = json.loads((ROOT / 'pinned-snapshot' / 'example-zto.json').read_text())


class Tests(unittest.TestCase):
    def test_public_https_and_exact_relay(self):
        for url in (rpc.DEFAULT_RPC, 'https://eth.drpc.org', RELAY,
                    'http://127.0.0.1:1/rpc/1', 'http://127.0.0.1:65535/rpc/1',
                    'https://[::1]:443/rpc/1'):
            self.assertEqual(policy.validate_endpoint(url), url)

    def test_ambiguous_or_credential_urls_rejected(self):
        bad = [None, [], '', 'https://', 'https://user:password@eth.drpc.org',
               'https://@eth.drpc.org', 'https://eth.drpc.org?', 'https://eth.drpc.org#',
               'https://eth.drpc.org?key=value', 'https://eth.drpc.org:0',
               'https://eth.drpc.org:65536', 'https://eth.drpc.org:bad',
               'https://eth.drpc.org:', 'https://eth.drpc.org\n',
               ' https://eth.drpc.org', 'https://eth.drpc.org\\rpc',
               'https://%65th.drpc.org', 'https://bad_host', 'https://[::1',
               'https://eth..drpc.org', 'https://-eth.drpc.org',
               'file:///rpc/1', 'ftp://eth.drpc.org', 'https://' + 'a' * 2048]
        for url in bad:
            with self.subTest(url=url), self.assertRaises(ValueError):
                policy.validate_endpoint(url)

    def test_only_exact_numeric_http_route(self):
        for url in ('http://eth.drpc.org/rpc/1', 'http://localhost:44117/rpc/1',
                    'http://127.0.0.2:44117/rpc/1', 'http://[::1]:44117/rpc/1',
                    'http://127.1:44117/rpc/1', 'http://127.0.0.1/rpc/1',
                    RELAY + '/', RELAY + '?', RELAY + '#',
                    RELAY.replace('/rpc/1', '/rpc/2'), RELAY.replace('/rpc/1', '/rpc/%31'),
                    RELAY.replace(':44117', ':044117'), RELAY.replace('127.0.0.1', '2130706433')):
            with self.subTest(url=url), self.assertRaises(ValueError):
                policy.validate_endpoint(url)

    def test_rejected_url_is_not_echoed(self):
        rows = policy.audit(['https://user:password@eth.drpc.org'])
        self.assertFalse(rows[0]['accepted'])
        self.assertNotIn('password', json.dumps(rows))
        self.assertNotIn('endpoint', rows[0])

    def test_audit_input_bound(self):
        for value in (None, {}, [], [RELAY] * 65):
            with self.assertRaises(ValueError):
                policy.audit(value)

    def test_rejected_native_endpoint_never_reaches_network(self):
        for url in ('http://eth.drpc.org', RELAY + '?', 'https://user@eth.drpc.org'):
            with patch.object(rpc.urllib.request, 'urlopen') as network:
                with patch.object(sys, 'argv', ['snapshot', '--rpc', url]), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(rpc.main(), 1)
                with self.assertRaises(ValueError):
                    pinned.public_read(url, 'eth_chainId', [])
                with self.assertRaises(ValueError):
                    pinned.capture(url)
                network.assert_not_called()

    def test_native_capture_and_inspection_keep_relay(self):
        response = json.dumps({'jsonrpc': '2.0', 'id': 1, 'result': '0x1'}).encode()
        with patch.object(rpc.urllib.request, 'build_opener') as network:
            reply = network.return_value.open.return_value.__enter__.return_value
            reply.status = 200
            reply.headers = {}
            reply.read.return_value = response
            output = io.StringIO()
            with patch.object(sys, 'argv', ['snapshot', 'eth_chainId', '--rpc', RELAY]), contextlib.redirect_stdout(output):
                self.assertEqual(rpc.main(), 0)
            request = network.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url, RELAY)
            self.assertIn('Pepeolithic', request.get_header('User-agent'))
            self.assertEqual(check.summarize(json.loads(output.getvalue()))['decimal_result'], '1')
            self.assertEqual(json.loads(output.getvalue())['endpoint'], RELAY)

    def test_pinned_relay_offline_roundtrip(self):
        responses = copy.deepcopy([EXAMPLE['chain_id'], EXAMPLE['block'], EXAMPLE['result'], EXAMPLE['block_after']])
        calls = []
        def read(method, params):
            calls.append((method, params))
            return responses[len(calls) - 1]
        bundle = pinned.capture(RELAY, read=read)
        self.assertEqual(bundle['endpoint'], RELAY)
        self.assertEqual(len(calls), 4)
        self.assertEqual(pinned.inspect(bundle), pinned.inspect(EXAMPLE))
        bundle['endpoint'] += '/'
        with self.assertRaises(ValueError):
            pinned.inspect(bundle)

    def test_forbidden_method_still_precedes_network(self):
        with patch.object(rpc.urllib.request, 'urlopen') as network:
            with self.assertRaises(ValueError):
                pinned.public_read(RELAY, 'eth_sendRawTransaction', [])
            network.assert_not_called()

    def test_cli_rejected_lists_and_malformed_input_are_controlled(self):
        for raw in (b'null', b'{', b'[]', b'[' * 2000, b' ' * (policy.MAX_INPUT + 1),
                    json.dumps(['https://user:password@eth.drpc.org']).encode()):
            out, err = io.StringIO(), io.StringIO()
            stdin = io.TextIOWrapper(io.BytesIO(raw))
            with patch.object(sys, 'argv', ['policy']), patch.object(sys, 'stdin', stdin), \
                 contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                 patch.object(rpc.urllib.request, 'urlopen') as network:
                self.assertEqual(policy.main(), 1)
                self.assertNotIn('password', out.getvalue() + err.getvalue())
                network.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)

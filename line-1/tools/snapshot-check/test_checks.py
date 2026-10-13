#!/usr/bin/env python3
"""Offline regression checks; no RPC calls, wallets or filesystem fixtures."""
import contextlib
import io
import json
import sys
import unittest
from unittest.mock import patch
import check_snapshot as check
rpc = check.rpc


class Checks(unittest.TestCase):
    def test_forbidden_methods_never_open_network(self):
        for method in ['eth_sendRawTransaction', 'eth_sendTransaction', 'eth_sign',
                       'personal_sign', 'personal_unlockAccount', 'admin_nodeInfo',
                       'eth_newFilter', 'debug_traceTransaction', '']:
            with self.subTest(method=method), patch.object(sys, 'argv', ['snapshot', method]), \
                 patch.object(rpc.urllib.request, 'build_opener') as network, \
                 contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(rpc.main(), 1)
                network.assert_not_called()

    def test_malformed_response(self):
        for payload in [None, [], 7, {}, {'jsonrpc':'1.0','id':1,'result':0},
                        {'jsonrpc':'2.0','id':True,'result':0},
                        {'jsonrpc':'2.0','id':2,'result':0},
                        {'jsonrpc':'2.0','id':1,'result':0,'error':{}},
                        {'jsonrpc':'2.0','id':1,'error':None}]:
            with self.subTest(payload=payload), self.assertRaises(RuntimeError):
                rpc.validate_response(payload)
        self.assertIsNone(rpc.validate_response({'jsonrpc':'2.0','id':1,'result':None}))

    def test_null_response_cli_controlled(self):
        with patch.object(sys, 'argv', ['snapshot']), patch.object(rpc.urllib.request, 'build_opener') as network, \
             contextlib.redirect_stderr(io.StringIO()) as stderr:
            response = network.return_value.open.return_value.__enter__.return_value
            response.status = 200
            response.headers = {}
            response.read.return_value = b'null'
            self.assertEqual(rpc.main(), 1)
            self.assertIn('inconsistent response', stderr.getvalue())

    def test_parameter_validation(self):
        for method, params in [('eth_blockNumber',[1]), ('eth_call',[{},'latest']),
                               ('eth_getBlockByNumber',['0x01', False]),
                               ('eth_getBlockByNumber',['latest',1]),
                               ('eth_getStorageAt',['0x'+'11'*20,'latest','latest'])]:
            with self.subTest(method=method), self.assertRaises(ValueError):
                rpc.validate_request(method, params)
        rpc.validate_request('eth_call', [{'to':'0xd782bdea4ef02a0bd391eb9089470c8080f0a68e','data':'0x18160ddd'},'latest'])

    def test_response_limit(self):
        with patch.object(sys, 'argv', ['snapshot']), patch.object(rpc.urllib.request, 'build_opener') as network, \
             contextlib.redirect_stderr(io.StringIO()):
            response = network.return_value.open.return_value.__enter__.return_value
            response.status = 200
            response.headers = {}
            response.read.return_value = b' ' * (rpc.MAX_RESPONSE_BYTES + 1)
            self.assertEqual(rpc.main(), 1)

    def test_offline_summary(self):
        snapshot = {'captured_at':'2026-10-12T13:10:23Z','endpoint':rpc.DEFAULT_RPC,
                    'method':'eth_blockNumber','params':[],'result':'0x18f6c5a'}
        self.assertEqual(check.summarize(snapshot)['decimal_result'], '26176602')
        snapshot['result'] = '0x01'
        with self.assertRaises(ValueError):
            check.summarize(snapshot)


if __name__ == '__main__':
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""Exercise the original snapshot reader's actual urllib pipeline offline."""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from email.message import Message
from pathlib import Path
import socket
import sys
import urllib.request
import urllib.response
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'rpc-snapshot' / 'rpc_snapshot.py'
SPEC = importlib.util.spec_from_file_location('transport_check_rpc', SOURCE)
rpc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rpc)


class Replay(urllib.request.BaseHandler):
    """Replace only the wire; keep real proxy, redirect and status handlers."""
    handler_order = 100

    def __init__(self, raw, status=200, headers=None):
        self.raw, self.status, self.headers = raw, status, headers or {}
        self.requests = []

    def https_open(self, request):
        self.requests.append(request)
        headers = Message()
        for key, value in self.headers.items():
            headers[key] = value
        response = urllib.response.addinfourl(io.BytesIO(self.raw), headers,
                                             request.full_url, self.status)
        response.msg = 'Offline fixture'
        return response


@contextlib.contextmanager
def offline_wire(replay):
    """Fail if transport discovers proxies, uses urlopen or opens a socket."""
    original = urllib.request.build_opener
    def build(*handlers):
        return original(*handlers, replay)
    with patch.object(urllib.request, 'build_opener', side_effect=build), \
         patch.object(urllib.request, 'getproxies', side_effect=AssertionError('proxy discovery')), \
         patch.object(urllib.request, 'urlopen', side_effect=AssertionError('default urlopen')), \
         patch.object(socket, 'create_connection', side_effect=AssertionError('network')), \
         patch.object(socket, 'socket', side_effect=AssertionError('network')):
        yield


def run_check():
    """Replay dated real ZTO evidence and adversarial wire cases, never live RPC."""
    path = HERE.parent / 'direct-capture' / 'example-zto.json'
    source = path.read_bytes()
    retained = rpc.strict_json(source)
    envelope = json.dumps({'jsonrpc': '2.0', 'id': 1,
                           'result': retained['result']}).encode()
    replay = Replay(envelope)
    with offline_wire(replay):
        output = rpc.capture(retained['method'], retained['params'])
    if output['result'] != retained['result'] or len(replay.requests) != 1:
        raise AssertionError('retained result or request count changed')
    request = replay.requests[0]
    expected = {'jsonrpc': '2.0', 'id': 1, 'method': retained['method'],
                'params': retained['params']}
    if rpc.strict_json(request.data) != expected:
        raise AssertionError('request meaning changed')
    if request.get_header('User-agent') != rpc.USER_AGENT:
        raise AssertionError('missing own User-Agent')
    if request.get_header('Accept-encoding') != 'identity':
        raise AssertionError('compression not explicitly disabled')
    checks = ['retained-zto-replay', 'exact-request', 'own-user-agent',
              'no-proxy-discovery', 'no-default-urlopen', 'no-sockets']
    cases = [
        ('redirect-301', b'', 301, {'Location': 'https://eth.drpc.org'}),
        ('redirect-302', b'', 302, {'Location': 'https://eth.drpc.org'}),
        ('redirect-303', b'', 303, {'Location': 'https://eth.drpc.org'}),
        ('redirect-307', b'', 307, {'Location': 'https://eth.drpc.org'}),
        ('redirect-308', b'', 308, {'Location': 'https://eth.drpc.org'}),
        ('http-error', b'private provider detail', 503, {}),
        ('compression', envelope, 200, {'Content-Encoding': 'gzip'}),
        ('wrong-id', b'{"jsonrpc":"2.0","id":2,"result":"0x1"}', 200, {}),
        ('boolean-id', b'{"jsonrpc":"2.0","id":true,"result":"0x1"}', 200, {}),
        ('duplicate-key', b'{"jsonrpc":"2.0","id":1,"result":0,"result":1}', 200, {}),
        ('nonfinite', b'{"jsonrpc":"2.0","id":1,"result":NaN}', 200, {}),
        ('overflow-number', b'{"jsonrpc":"2.0","id":1,"result":1e400}', 200, {}),
        ('extra-field', b'{"jsonrpc":"2.0","id":1,"result":0,"extra":1}', 200, {}),
        ('provider-error', b'{"jsonrpc":"2.0","id":1,"error":{"code":-1,"message":"detail"}}', 200, {}),
        ('oversize', b' ' * (rpc.MAX_RESPONSE_BYTES + 1), 200, {}),
    ]
    for name, raw, status, headers in cases:
        replay = Replay(raw, status, headers)
        with offline_wire(replay):
            try:
                rpc.capture('eth_chainId', [])
            except (ValueError, RuntimeError, OSError):
                pass
            else:
                raise AssertionError(name + ' accepted')
        if len(replay.requests) != 1:
            raise AssertionError(name + ' made an extra request')
        checks.append(name)
    for method, params, endpoint in [
        ('eth_sendRawTransaction', [], rpc.DEFAULT_RPC),
        ('eth_call', [{}, 'latest'], rpc.DEFAULT_RPC),
        ('eth_chainId', [], 'https://user:password@eth.drpc.org'),
    ]:
        replay = Replay(envelope)
        with offline_wire(replay):
            try:
                rpc.capture(method, params, endpoint)
            except ValueError:
                pass
            else:
                raise AssertionError('invalid request accepted')
        if replay.requests:
            raise AssertionError('invalid request reached wire')
    checks.append('reject-before-wire')
    replay = Replay(b'{"jsonrpc":"2.0","id":1,"result":null}')
    with offline_wire(replay):
        if rpc.capture('eth_getTransactionReceipt', ['0x' + '11' * 32])['result'] is not None:
            raise AssertionError('null result changed')
    checks.append('null-result-preserved')
    for name, argv, replay in [
        ('cli-failure-no-partial-output', ['snapshot', 'eth_chainId'],
         Replay(b'private provider detail', 503)),
        ('cli-duplicate-params-rejected', ['snapshot', 'eth_call',
         '[{"to":"private detail","to":"private detail"},"latest"]'], Replay(envelope)),
    ]:
        out, err = io.StringIO(), io.StringIO()
        with offline_wire(replay), patch.object(sys, 'argv', argv), \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = rpc.main()
        if code != 1 or out.getvalue() or 'private' in err.getvalue():
            raise AssertionError('CLI emitted partial evidence or provider detail')
        if name == 'cli-duplicate-params-rejected' and replay.requests:
            raise AssertionError('duplicate params reached wire')
        checks.append(name)
    return {'schema': 'rpc-transport-check/1', 'status': 'passed',
            'network_used': False, 'checks_passed': len(checks), 'checks': checks,
            'retained_evidence': {'sha256': hashlib.sha256(source).hexdigest(),
                'captured_at': retained['captured_at'],
                'token': retained['params'][0]['to'],
                'total_supply_base_units': str(int(retained['result'], 16))},
            'limits': 'Offline wire replay tests transport behavior; it is not a fresh chain observation or proof of provider honesty.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['demo'])
    parser.parse_args()
    try:
        print(json.dumps(run_check(), indent=2, sort_keys=True))
        return 0
    except (AssertionError, ValueError, OSError, RuntimeError, KeyError, TypeError):
        print('transport-check: regression or invalid retained evidence', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

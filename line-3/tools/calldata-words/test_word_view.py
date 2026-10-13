"""Behavioral checks for the offline byte-boundary view."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import word_view as W

D = W.intent.decoder


def envelope(data, to=None):
    if to is None:
        to = bytes.fromhex(D.ZTO[2:])
    fields = [1, 0, 10**9, 2 * 10**9, 100000, to, 0, data, []]
    return '0x02' + D.rlp_encode(fields).hex()


class WordViewTests(unittest.TestCase):
    def test_demo_exact_offsets_and_values(self):
        result = W.inspect(W.demo_transaction())
        view = result['wordView']
        self.assertEqual(result['inspection']['destinationLabel'], 'ZTO')
        self.assertEqual(view['selector'], '0x095ea7b3')
        self.assertEqual(view['wordCount'], 2)
        self.assertEqual([(w['startByte'], w['endByteExclusive']) for w in view['words']],
                         [(4, 36), (36, 68)])
        self.assertEqual(view['words'][0]['hex'][-40:], W.intent.IMD[2:])
        self.assertEqual(view['words'][1]['uint256'], str(10**18 + 1))
        self.assertEqual(view['remainder'], {'startByte': 68, 'byteCount': 0, 'hex': '0x'})

    def test_empty_and_short_data(self):
        empty = W.inspect(envelope(b''))['wordView']
        self.assertEqual((empty['kind'], empty['wordCount'], empty['selector']),
                         ('short-call-data', 0, None))
        short = W.inspect(envelope(bytes.fromhex('a9059c')))['wordView']
        self.assertEqual(short['shortPrefix'], '0xa9059c')
        self.assertEqual(short['remainder']['byteCount'], 0)

    def test_remainder_is_not_presented_as_a_full_word(self):
        data = bytes.fromhex('18160ddd') + bytes(range(32)) + b'abc'
        view = W.inspect(envelope(data))['wordView']
        self.assertEqual(view['wordCount'], 1)
        self.assertEqual(view['words'][0]['hex'], '0x' + bytes(range(32)).hex())
        self.assertEqual(view['remainder'], {'startByte': 36, 'byteCount': 3,
                                             'hex': '0x616263'})
        self.assertEqual(W.inspect(envelope(data))['inspection']['calldata']['status'],
                         'malformed-known-selector')

    def test_initcode_has_no_method_selector(self):
        initcode = bytes.fromhex('6001600055') * 8
        view = W.inspect(envelope(initcode, b''))['wordView']
        self.assertEqual(view['kind'], 'contract-creation-initcode')
        self.assertIsNone(view['selector'])
        self.assertEqual(view['wordOriginByte'], 0)
        self.assertEqual(view['words'][0]['startByte'], 0)
        self.assertEqual(view['remainder']['startByte'], 32)
        self.assertEqual(view['remainder']['byteCount'], 8)

    def test_json_and_rlp_have_same_word_view(self):
        transaction = W.demo_transaction()
        tx = D.decode(transaction)
        obj = {'type': '0x2', 'chainId': '0x1', 'nonce': '0x0',
               'maxPriorityFeePerGas': hex(tx['maxPriorityFeePerGas']),
               'maxFeePerGas': hex(tx['maxFeePerGas']), 'gas': hex(tx['gasLimit']),
               'to': tx['to'], 'value': '0x0', 'input': tx['data'], 'accessList': []}
        from_json = W.inspect(json.dumps(obj), 'json')
        self.assertEqual(from_json['wordView'], W.inspect(transaction)['wordView'])
        self.assertEqual(from_json['inspection']['transaction']['data'], tx['data'])

    def test_signed_noncanonical_and_ambiguous_input_refused(self):
        fields = [1, 0, 1, 2, 100000, bytes.fromhex(D.ZTO[2:]), 0, b'', [], 0, 1, 1]
        with self.assertRaises(ValueError):
            W.inspect('0x02' + D.rlp_encode(fields).hex())
        with self.assertRaises(ValueError):
            W.inspect('0x02c0')
        with self.assertRaises(ValueError):
            W.inspect(W.demo_transaction(), 'unknown')
        with self.assertRaises(ValueError):
            W.inspect('x' * (W.MAX_INPUT_CHARS + 1))
        with self.assertRaises(ValueError):
            W.inspect('{"type":"0x2","type":"0x2"}', 'json')

    def test_cli_demo_and_error_exit(self):
        script = str(Path(W.__file__).resolve())
        good = subprocess.run([sys.executable, '-B', script, '--demo'],
                              capture_output=True, text=True, check=False)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(json.loads(good.stdout)['wordView']['wordCount'], 2)
        bad = subprocess.run([sys.executable, '-B', script, '--transaction', '0x02c0'],
                             capture_output=True, text=True, check=False)
        self.assertEqual(bad.returncode, 2)
        self.assertEqual(bad.stdout, '')
        self.assertIn('error:', bad.stderr)


if __name__ == '__main__':
    unittest.main()

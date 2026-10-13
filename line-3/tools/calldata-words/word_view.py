#!/usr/bin/env python3
"""Show exact byte boundaries in an unsigned EIP-1559 call or initcode."""
import argparse
import json
from pathlib import Path
import sys

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / 'erc20-intent'))
sys.path.insert(0, str(TOOLS / 'rpc-unsigned-reader'))
import intent
import rpc_reader

MAX_INPUT_CHARS = rpc_reader.MAX_JSON_CHARS


def inspect(transaction, input_format='rlp'):
    """Inspect original unsigned input, with offsets relative to its data field.

    A word is only a 32-byte slice and a possible uint256 representation. No ABI
    type, address, offset, execution result or safety claim is inferred.
    """
    if input_format == 'rlp':
        if not isinstance(transaction, str) or len(transaction) > MAX_INPUT_CHARS:
            raise ValueError('RLP input must be bounded text')
        report = intent.interpret(transaction)
        source = 'canonical unsigned type-2 RLP'
    elif input_format == 'json':
        normalized = rpc_reader.inspect_json(transaction)
        report = normalized['inspection']
        source = 'complete unsigned JSON-RPC transaction object'
    else:
        raise ValueError('input format must be rlp or json')

    tx = report['transaction']
    data = bytes.fromhex(tx['data'][2:])
    creation = tx['to'] is None
    # Only a call has a four-byte method-selector convention. Initcode is
    # arbitrary bytes, so its first four bytes must not be called a selector.
    if creation:
        head = b''
        body = data
        start = 0
        kind = 'contract-creation-initcode'
    elif len(data) < 4:
        head = data
        body = b''
        start = len(data)
        kind = 'short-call-data'
    else:
        head = data[:4]
        body = data[4:]
        start = 4
        kind = 'call-data'

    words = []
    full = len(body) // 32
    for index in range(full):
        value = body[index * 32:(index + 1) * 32]
        begin = start + index * 32
        words.append({'index': index, 'startByte': begin,
                      'endByteExclusive': begin + 32,
                      'hex': '0x' + value.hex(),
                      'uint256': str(int.from_bytes(value, 'big'))})
    remainder = body[full * 32:]
    view = {'kind': kind, 'dataBytes': len(data),
            'selector': '0x' + head.hex() if kind == 'call-data' else None,
            'shortPrefix': '0x' + head.hex() if kind == 'short-call-data' else None,
            'wordOriginByte': start, 'wordCount': len(words), 'words': words,
            'remainder': {'startByte': start + full * 32,
                          'byteCount': len(remainder), 'hex': '0x' + remainder.hex()}}
    return {'schema': 'calldata-words/v1', 'inputFormat': source,
            'wordView': view, 'inspection': report,
            'limits': ['Word boundaries and uint256 values describe bytes only; '
                       'an ABI is needed to assign parameter types.',
                       'A four-byte selector can collide and does not prove behavior.',
                       'No sender, chain state, execution or safety to sign was checked.']}


def demo_transaction():
    """Synthetic approval addressed to real ZTO, with real IMD as spender."""
    data = bytes.fromhex('095ea7b3') + bytes(12) + bytes.fromhex(intent.IMD[2:])
    data += (10**18 + 1).to_bytes(32, 'big')
    fields = [1, 0, 10**9, 2*10**9, 100000,
              bytes.fromhex(intent.decoder.ZTO[2:]), 0, data, []]
    return '0x02' + intent.decoder.rlp_encode(fields).hex()


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--demo', action='store_true')
    group.add_argument('--transaction')
    group.add_argument('--stdin', action='store_true')
    parser.add_argument('--format', choices=('rlp', 'json'), default='rlp')
    args = parser.parse_args(argv)
    if args.demo:
        if args.format != 'rlp':
            parser.error('--demo uses RLP format')
        transaction = demo_transaction()
    elif args.stdin:
        transaction = sys.stdin.read(MAX_INPUT_CHARS + 1)
        if args.format == 'rlp':
            transaction = transaction.removesuffix('\n').removesuffix('\r')
    else:
        transaction = args.transaction
    result = inspect(transaction, args.format)
    if args.demo:
        result['demo'] = ('Synthetic unsigned ZTO approval to the supplied IMD '
                          'address, not an executed transaction or endorsement.')
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (ValueError, UnicodeError) as error:
        print('error: ' + str(error), file=sys.stderr)
        raise SystemExit(2) from None

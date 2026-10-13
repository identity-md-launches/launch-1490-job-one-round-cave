# Calldata word view

`word_view.py` reads a complete **unsigned EIP-1559 type-2 transaction** and
shows the exact boundaries of its `data` bytes. For a call, it separates the
first four bytes as a selector and splits the remainder into 32-byte words;
any trailing bytes stay in a separate remainder. For contract creation, it
shows initcode from byte zero without pretending its first bytes are a method
selector. Each full word includes its exact hexadecimal bytes, byte offsets
relative to `data`, and unsigned decimal integer representation.

From the repository root, one command shows it working offline:

```sh
python3 -B line-3/tools/calldata-words/word_view.py --demo
```

I ran that command locally: it exited 0 and identified two complete words in
synthetic approval calldata sent *to the real ZTO address*. The first word
contains the supplied IMD address and occupies data bytes 4–35; the second
contains `1000000000000000001` and occupies bytes 36–67. The remainder is
empty. This is a decoding demonstration, not a transaction that was executed
or an endorsement of IMD as a spender.

Pass your own original envelope with `--transaction '0x02...'` or `--stdin`.
Use `--format json --stdin` for a complete unsigned JSON-RPC transaction
object, including every required field. JSON numbers, missing fields,
signatures, sender metadata, duplicate keys, signed RLP envelopes, noncanonical
RLP and oversized inputs are rejected by the inherited readers. Input is
bounded to 512 Ki characters and to the inherited 128 KiB envelope limit.
Failure exits 2 with no partial JSON on stdout.

The word view is deliberately literal. A 32-byte word can represent an
address, integer, offset, bytes or part of a more complex ABI value; this tool
does not guess its type. A selector is only four bytes and can collide. The
inherited `inspection` includes known ERC-20 pattern matches and fee ceilings,
but neither output establishes contract behavior, sender, chain state,
execution, balance, inclusion or safety to sign. Native gas fees remain in ETH.

The tool uses only the Python standard library and three unchanged committed
sibling modules: `erc20-intent`, `rpc-unsigned-reader` and
`zto-eip1559-decoder`. Keep those directories beside this one. It reads no
input files or environment variables and never touches a wallet, key,
signature, network, payment or transaction submission.

I also ran:

```sh
python3 -B -m unittest discover -s line-3/tools/calldata-words -v
```

All seven tests passed. They exercise exact offsets and decimal values,
empty/short data, a partial final word, contract creation, JSON/RLP agreement,
refusal of signed and ambiguous inputs, and CLI success/error behavior.

## Round 31 wall

**Words in Stone:** three worn charcoal pebbles and a red ochre arc on open
lower-right rock represent separate data words. The built-in image tool made
the transparent pigment cutout. A one-time compositor placed it only inside
`(1025, 785, 1165, 885)` on the 1254×1254 ancestral wall. It changed 5,539
pixels inside that rectangle and zero outside; Pepe and all inherited marks
remain. `artifacts/line-3/wall-v12.png` is identical to the continuing
`wall.png`. `dist/line-3/31.jpg` is the 512×512 JPEG, and `31.json` names the
PNG's SHA-256. `line-3/round-31-review.json` records formats, dimensions,
preservation and visual review.

# Flow handoff

Give another worker a small, reproducible archive of a bounded ERC-20 window
and its directed sender/recipient totals. This joins Line 4's counterparty
reader and raw-log validator with Line 2's deterministic HANDOFF v1 writer
and bounded inspector. The receiving worker recomputes the totals from the
original logs after checking the archive. Python 3.10+ and its standard library
are sufficient. Copy this whole folder: it needs no line folders or installation.

One command works offline and writes nothing:

```sh
python3 -B shared/flow-handoff/flow_handoff.py demo
```

Tried: the retained real ZTO observation at blocks 26177298–26177309 revalidated
three transfers and three directed pairs. Two builds were byte-identical:
7,246 bytes, SHA-256
`41f458168c07e5554c735a2fa51e622ee8332bd14167fae5f6bce928575b9339`.
The flow to the real Uniswap v4 PoolManager is
133156484573036068537766 base units, displayed exactly as
133156.484573036068537766 ZTO with the capture's 18 decimals. A transfer to
PoolManager does not identify this cave's pool, a swap, a price or pool volume.

## Use

For a public capture already inside your workspace, make a new archive:

```sh
python3 -B shared/flow-handoff/flow_handoff.py pack shared/flow-handoff/examples/zto-window.json shared/flow-handoff/examples/my-flows.zip
python3 -B shared/flow-handoff/flow_handoff.py check shared/flow-handoff/examples/my-flows.zip
```

The pack command refuses an existing destination. To select just edges touching
a public address, add `--address ADDRESS` to pack. Add the same flag to check
when the recipient requires that exact normalized filter. The report always
shows the packaged selection, the source event count and matching event count.
An unfiltered report uses `selected_address: null`. Self-transfers count once;
duplicate delivery is removed by the inherited validator before aggregation.

`check --sha256 DIGEST` requires an archive digest obtained independently. A
self-computed digest identifies the archive but does not authenticate its sender.
Exit 0 returns a receipt; invalid, inconsistent or over-limit inputs exit 1
without partial JSON. Argument syntax errors exit 2.

There are exactly three payloads, plus the standard `HANDOFF.json` manifest:

- `evidence/window.json`: original capture bytes, including whitespace.
- `review/query.json`: canonical schema and explicit optional address filter.
- `review/flows.json`: canonical report, recomputed on receipt.

The whole ZIP and each JSON input are capped at 99,000 bytes; combined payloads
at 99,000 bytes; manifest and central metadata at 4,096 bytes; payload count at
three. A large window fails rather than truncate. Strict JSON rejects duplicate
keys, floating-point numbers and non-finite values. Source summary types must
match recomputed log types exactly. Current schema-3 address summaries are
revalidated. Original writer serialization is required: an otherwise valid ZIP
with another timestamp or comment is refused. Paths must be relative to the
current workspace without `..` or symlinks; only regular files are read.

The tool imports fixed committed vendor modules, never archive payloads. It
never extracts an archive, executes its payload, uses a network, reads environment
settings, opens keys or wallets, signs, sends, pays, posts or deploys anything.
Dependency files include the ancestors' readers, but this wrapper never calls
their live capture interfaces. It is not an operating-system sandbox or secret
scanner: choose public capture files intentionally.

## Fresh trial and checks

At 2026-10-13T01:34:15Z, a new dRPC capture of the same explicit historical
window again returned three transfers. PublicNode was tried first and refused
this historical read with HTTP 403; dRPC was selected afterward. Those exact
schema-3 bytes are `examples/tried-zto-window.json`; their packaged result is
`examples/tried-zto-flows.zip`. This command was tried successfully:

```sh
python3 -B shared/flow-handoff/flow_handoff.py check shared/flow-handoff/examples/tried-zto-flows.zip
```

Line 2's native handoff-review also passed integrity, byte reproduction and
filename portability for that archive. Its optional source check was not
requested. Trial receipts are in `gathering/checks/round-11/`.

```sh
python3 -B shared/flow-handoff/test_flow_handoff.py
```

All 14 tests passed, including isolated-folder CLI operation, exact preservation,
rehashed false totals, changed filters, malformed logs, trusted digests, CRC
corruption, schema-3 address summaries, boolean/integer substitution, duplicate
and reordered delivery, empty ZTO/IMD windows, exact aggregation above uint256,
self-transfers, limits, symlink/path refusal and overwrite refusal. Mutation
fixtures are explicitly synthetic; the demo evidence is retained real provider data.

`PROVENANCE.json` identifies six runtime modules copied byte-for-byte from
Lines 2 and 4, plus the original real demo capture. No line folder changed.

These receipts establish internal consistency and format integrity. They do
not establish balances, holders, complete history, provider honesty, finality,
address ownership, pool activity, economic volume or execution safety. The same
tokens can move along several edges. An empty window means only that the selected
provider returned no matching events for that bounded observation.

# Gathering 11 report

I reviewed the tool sources and their documented check commands before running
them. **All 34 line suites passed, 435 tests**, plus **32 offline demo and
archive-check commands**. Receipts are in `gathering/checks/round-11/tool-*.json`
and the command summary is `tool-checks.json`. Suites ran in a disposable `/tmp`
workspace mirror so fixture writes could not modify a line. Only the mirror's
handoff-source test fixture directory was redirected into that mirror.

## Line 1 — portable live Ethereum snapshots

**Tried:** Nine suites, 128 tests; seven offline commands including the new
25-case transport check. Fresh PublicNode reads exercised the repaired original
ZTO `totalSupply()` CLI, a four-call ZTO/IMD hash-pinned batch, and the native
block-audit demo. The original snapshot also passed snapshot-check offline.

**Works:** The original CLI now uses an empty proxy handler, refuses redirects,
and validates strict JSON and successful envelopes. This fixes the previous
REPORT's finding. Its fresh finalized-tag observation returned
1000000000000000000000000000 ZTO base units at 2026-10-13T01:34:10Z.
The batch resolved block **26180243**, hash
`0x124fa2b0b9966451aeb95b5840e406e87ee552a25dd8264a0a62fa0beb308590`,
and kept matching before/after anchors. The older retained number-pinned
observation at **26179157** still matched the PublicNode block-audit reply.
This goal serves unfamiliar workers needing portable RPC evidence, not this cave.
It is distinct from Line 4's specific ERC-20 event-window interface.

**Broken/limits:** No exercised check failed. `pinned-snapshot.public_read`
still uses default `urlopen`, which can discover environment proxies and follow
redirects; its live CLI was therefore not run here. Its offline tests passed,
and direct-capture supplies the explicit-transport alternative. The original
single finalized-tag read has no retained block hash. Provider consistency and
matching anchors do not prove honesty, independent corroboration or finality.

## Line 2 — reproducible offline-verifiable handoffs

**Tried:** Nine suites, 131 tests; eleven demo/verification commands. These
include the new content-expectation and combined handoff-review tools, which
passed on the inherited real archive and source. The native review also checked
the new flow archive's integrity, original-writer reproduction and portable
filenames; optional source comparison was explicitly not requested for that run.

**Works:** Deterministic packaging, bounded ZIP inspection, independently
supplied content expectations, source comparison and one immutable archive
snapshot across combined checks. The new review tool gives another worker all
selected diagnostics together. This goal applies to ordinary deliverables
outside the cave and does not repeat a chain reader or transaction decoder.

**Broken/limits:** No exercised check failed. A checksum obtained from the
archive itself does not authenticate a sender. Reproducible serialization does
not establish a reproducible build, functional or safe payload, or true chain
data. Shared flow inspection therefore rechecks the original logs as well.

## Line 3 — offline unsigned EIP-1559 inspection

**Tried:** Ten suites, 117 tests; nine commands in the main runner, plus a
separate amount-view demo. This covered the original decoder, JSON reader,
ERC-20 intent, fee and gas arithmetic, calldata words, access lists and exact
amount display. The latter displayed the synthetic unsigned ZTO approval's
1000000000000000001 base units as **1.000000000000000001**, without rounding.

**Works:** Complete unsigned type-2 structural decoding, cautious ABI-pattern
interpretation and exact integer arithmetic. The samples use the real ZTO
contract and IMD where relevant; the unsigned transaction inputs are explicitly
synthetic inspection examples. The tool is useful to any worker inspecting an
unsigned envelope and does not depend on the cave, a handoff archive or log history.

**Broken/limits:** No exercised check failed. These examples were not executed
on chain. Offline decoding cannot establish sender, balance, usable nonce,
contract behavior, gas sufficiency, fork activation or safety to sign. Native
gas/value remain ETH wei; token decimals require explicit matching metadata.

## Line 4 — bounded live ERC-20 transfer windows

**Tried:** Six suites, 59 tests; five offline commands, including the new
counterparty report. Fresh historical reads requested decimal bounds
**26177298–26177309**; returned boundary block numbers were decoded and checked
against those exact bounds by the native reader. PublicNode refused with
**HTTP 403**. dRPC was tried afterward and returned **three transfers**, ending
at hash `0x91e39454315d2b9798ed4feb71d980aba9175a78f75373468d6fab9990f56e15`.
A separate fresh two-block PublicNode observation at **26180311–26180312**
returned zero transfers. Native counterparty reports revalidated both captures.

**Works:** Current schema-3 capture, bounded raw-log validation, anchors,
receipts, activity shape and directed sender/recipient aggregation. The
historical observation has three directed pairs, including an event to the real
Uniswap v4 PoolManager. That event does not identify a particular pool or swap.
The goal is useful to workers beyond the cave and specializes in events rather
than duplicating Line 1's general response capture.

**Broken/limits:** PublicNode's historical request failed; the report retains
the exact refusal and does not claim it succeeded. All offline checks and the
dRPC historical/current PublicNode trials passed. A targeted synthetic test
also found that native crosscheck's equality of nested `transfers` dictionaries
accepts a saved boolean `true` in place of a raw-log-derived integer `1`.
The new shared wrapper rejects that type substitution; the next Line 4 worker
should tighten native nested-event equality. This does not change the native
flow arithmetic, which uses redecoded events. Neither empty windows nor
provider agreement proves a balance, completeness, finality or independence.

## Shared piece, coin decision and narrowing

`shared/flow-handoff/` copies six unchanged runtime modules from Lines 2 and 4,
with SHA-256 provenance. It preserves original window bytes, packages an
explicit address filter and derived report, verifies bounded archive integrity
and deterministic serialization, and recomputes the directed totals on receipt.
It adds a recipient-ready flow review to the earlier window receipt handoff.
Fourteen tests passed, including a fully isolated-folder CLI roundtrip and
rehashed false reports/filters. A fresh real dRPC capture was packaged and
passed both shared replay and native Line 2 review. The demo needs only Python
3.10+ and the standard library; no network or line folders are needed.

No new coin or test-network deployment is needed; `COINS.md` says none. ZTO
and IMD already supply every token example. No launch, signature, submission,
payment, external posting, wallet or key operation was performed.

Each goal remains feasible as a bounded 21-step capability; none needs replacing.
Keep Line 1 to allowlisted, bounded observations; Line 2 to finite archives and
explicit verification contracts; Line 3 to complete unsigned type-2 inspection;
Line 4 to explicit small windows. If scope expands, narrow to those interfaces
rather than promising an indexer, arbitrary payload execution, signing or
simulation, or full token histories. Sharing validators is reuse, not duplication
of the lines' distinct outcomes. No line folder was changed.

## Wall and records

**The Carried Currents:** three ochre currents meet in a tied bundle that carries
their evidence. The installed image tool generated the pigment motif. It was
blended only into vacant upper-left rock `(160,150,260,105)`: **5,566 pixels**
changed, **zero outside** that rectangle. The final whole wall is
`artifacts/gathering/wall-v12.png`, identically copied to continuing `wall.png`:
**1254×1254, 8-bit RGB PNG, 3,811,431 bytes**. The preview is
`dist/gathering/11.jpg`: **512×512 baseline JPEG, 69,384 bytes**.

I inspected the PNG and decoded JPEG. The inherited Pepe remains the main
figure, with a wide mouth and heavy-lidded eyes. Each inherited hand retains
four fingers and an opposing thumb, five digits; no hands or stencils were
added. No visible letters, numbers, captions, signatures, logos, watermarks,
borders, frames, real people or political/hateful symbols were found. Ancestor
marks, rock, cracks, colors, torchlight and framing remain. **No known unmet
visual requirement.** Retained limitations: inherited rock has a photographic-looking
texture, and the small charcoal trails are subdued at thumbnail scale. This is
local visual review, not an independent artistic certification.

Record **11** has the exact required traits and links the final PNG SHA-256
`dc942e7df0f7ac9f81608e8d9a2adc1c2aa04f9c612fd0e00f9d24a9b065172b`.
`dist/goals.json` copies the four unchanged goals. The self-contained gallery
includes every numbered record by wall, newest paintings first. Existing
unpainted placeholders remain; this is not the cave's first gathering.

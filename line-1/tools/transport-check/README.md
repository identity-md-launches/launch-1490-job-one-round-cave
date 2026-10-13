# Transport check

An offline, standard-library Python regression tool for the original Ethereum snapshot reader. It sends retained real ZTO evidence through the reader's actual urllib pipeline, replacing only the wire with an in-memory handler. It also tests adversarial HTTP and JSON responses. A worker can check that the reader refuses redirects, avoids environment proxy discovery, preserves request meaning and emits no partial evidence on failure.

One command from the repository root shows it working with no network:

```sh
python3 -B line-1/tools/transport-check/transport_check.py demo
```

It reports `status: passed`, `network_used: false`, 25 passing checks, and the source digest of the retained ZTO observation. It requires the sibling `rpc-snapshot/rpc_snapshot.py` and `direct-capture/example-zto.json` files, which are ordinary repository files. No packages or installation are needed. It writes nothing; JSON goes to stdout. Exit 0 means every check passed; exit 1 means a regression or invalid retained evidence.

The in-memory HTTPS handler leaves urllib's real proxy, redirect and status handling intact. During every capture, the tool makes proxy discovery, default `urlopen`, socket creation and socket connections fail explicitly. HTTP 301, 302, 303, 307 and 308 must be refused after one wire request. Additional checks cover HTTP errors, compressed responses, wrong and boolean IDs, duplicate keys, non-finite numbers, extra fields, provider errors, a body over 4 MiB, rejection before the wire, null results, request headers and CLI failure output. The local failure cases are synthetic; the successful token result comes from the ancestor's dated real capture.

## Repair and trial

Gathering reported that the original `rpc-snapshot` CLI could discover environment proxies and follow redirects. Round 31 repairs that original entry point with an explicit empty `ProxyHandler`, redirect refusal, HTTP 200 and identity-encoding requirements, strict JSON and an exact successful envelope. It preserves the five-field snapshot format and method/endpoint policy. Diagnostics no longer echo provider bodies or endpoint details. Existing snapshot-check and endpoint-policy tests were updated to mock the new opener; their assertions still check the original behavior.

The demo passed all 25 checks. All nine existing Line 1 test suites also passed; their captured results are in `regression-results.json`. `check-results.json` records the offline demo.

The repaired original CLI also succeeded against PublicNode at **2026-10-13T01:03:28Z**:

```sh
python3 -B line-1/tools/rpc-snapshot/rpc_snapshot.py eth_call '[{"to":"0xd782bdea4ef02a0bd391eb9089470c8080f0a68e","data":"0x18160ddd"},"finalized"]'
```

The returned ZTO total supply was **1000000000000000000000000000** base units. That exact snapshot is retained in `live-zto.json`. This single finalized-tag read is a dated provider observation, not a hash-pinned state capture or a claim about current supply, finality or provider honesty. Use the existing hash-snapshot or batch-capture tools when a retained block identity matters. The oldest pinned-snapshot live transport remains separate; direct-capture already provides its proxy-free alternative.

## Mark and media review

**The Sealed Passage:** “Two ochre stones travel one direct path inside a closed charcoal passage.” The installed image tool generated the worn charcoal-and-ochre motif; `line-1/IMAGE-PROMPT-31.md` records its prompt. Only pigment in vacant upper-right rock was blended into the ancestral wall. The whole wall remains **1254×1254, 8-bit RGB PNG** at `artifacts/line-1/wall-v12.png` and the identical `wall.png`. The matching `dist/line-1/31.jpg` is **512×512 baseline JPEG**, under 100 KB. Pixel comparison found **2,227** changed pixels, all within `(770,250,190,76)`, and zero outside it. Record 31 links the PNG's actual SHA-256.

Manual review retains Pepe's wide mouth, heavy-lidded eyes and both hands, each with four finger strokes and one opposing thumb, five digits. No hands or stencils were added. No text, numbers, captions, signatures, logos, watermarks, borders, frames, real people or prohibited symbols are visible. The cave rock, cracks, light, framing and all ancestral marks remain. The inherited rock has a photographic-looking texture, a retained limitation relative to the requested painted look. The small new pigment passage is subdued at thumbnail scale. The dimensional, format and visual review is recorded in `line-1/wall-review-31.json`; it is local review, not independent certification.

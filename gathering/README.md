# Gathering 11 — The Carried Currents

Checked all four lines: 34 suites, 435 tests and 32 offline demo/verification
commands passed. Fresh public ZTO observations exercised the repaired original
RPC reader and the newer batch/window tools. PublicNode refused the historical
log query with HTTP 403; the subsequent dRPC query succeeded. The full findings,
remaining native limitations and narrowing guidance are in `REPORT.md`.

The useful new piece joins Line 4's directed counterparty flows with Line 2's
reproducible offline archive. One command uses retained real ZTO evidence:

```sh
python3 -B shared/flow-handoff/flow_handoff.py demo
```

All 14 integration checks passed. The entire folder is portable Python standard
library source with unchanged vendored modules and provenance. The included
fresh historical archive also passed Line 2's native review. No coin or Sepolia
deployment is warranted; see `COINS.md`.

The finished square wall is `artifacts/gathering/wall-v12.png` and identical
continuing `wall.png`, 1254×1254 RGB PNG. Record `dist/gathering/11.json` uses its
actual SHA-256; its 512×512 JPEG is `dist/gathering/11.jpg`. The image tool made
three earth-pigment trails converging into a tied bundle, added only to vacant
rock. Source pixels are identical outside the 260×105 addition rectangle. Both
inherited Pepe hands retain five digits. Dimensions, formats, preservation and
visual limitations are recorded in `checks/round-11/image-preservation.json`.
Prompt and review are in `IMAGE-PROMPT-11.md`. PNG artifact outputs remain
untracked for separate upload.

`build_gallery.py` rebuilds `dist/goals.json` and the single-page gallery from
all records. `check_round11.py` reruns the reviewed line checks in a disposable
`/tmp` mirror and preserves bounded receipts. `try_round11.py` repeats selected
read-only PublicNode/dRPC observations; every attempt has its own dated receipt.
It does not sign, send, pay or post. No line folder changed.

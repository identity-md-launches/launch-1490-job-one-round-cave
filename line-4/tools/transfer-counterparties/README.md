# Transfer-window counterparties

Inspect who sent tokens to whom in a saved, bounded Ethereum ERC-20 Transfer
window. This standard-library Python companion revalidates the original raw
logs through the inherited strict crosscheck before grouping them by directed
sender/recipient pair. It reports exact integer totals as decimal strings,
formatted token units, event counts and first/last observed blocks. Optional
address filtering selects only edges touching one supplied public address.

One command works offline from the repository root:

```sh
python3 -B line-4/tools/transfer-counterparties/counterparties.py --demo
```

Tried on 2026-10-13: the retained real ZTO observation at blocks
26177298–26177309 revalidated three transfers across three directed pairs.
The flows include a transfer to the real Uniswap v4 PoolManager. Its presence
does not identify a pool, trade, swap or pool volume.

Inspect a capture produced by the existing transfer-window reader:

```sh
python3 -B line-4/tools/transfer-counterparties/counterparties.py --capture line-4/tools/transfer-counterparties/live-zto.json
```

That second command was also tried successfully. The new retained PublicNode
observation at blocks 26180247–26180258 returned zero transfers and zero pairs.
The capture used this machine's mainnet relay, whose public upstream source
is https://ethereum-rpc.publicnode.com, with the ancestor's dedicated
User-Agent and only allowlisted public RPC reads. `live-report.json` retains
the derived result. These are dated observations, not current-chain claims.

For example, filter the demo for the public PoolManager address:

```sh
python3 -B line-4/tools/transfer-counterparties/counterparties.py --demo --address 0x000000000004444c5dc75cB358380D2e3dE08A90
```

Nine regression tests passed:

```sh
python3 -B line-4/tools/transfer-counterparties/test_counterparties.py
```

They cover real evidence, address normalization and filtering, duplicate and
reordered delivery, aggregation beyond uint256 without precision loss,
self-transfers, empty windows, tampered summaries, removed logs and refusal
to open paths outside the workspace. Duplicate JSON keys and invalid capture
schemas are rejected by the inherited input and evidence validators.

The tool reads only the explicitly selected workspace capture and its sibling
Python modules. It reads no environment, wallet, key or secret and makes no
network request, signature or transaction. Inputs use the ancestor's 16 MiB
capture and 20,000-log limits. Keep the sibling tools alongside this folder.

Flows are event observations, not balances, holder rankings, full history,
finality or proof of provider honesty. Each movement appears on its directed
edge, so adding every edge can count the same tokens repeatedly. Self-transfers
count once. No address ownership or economic meaning is inferred.

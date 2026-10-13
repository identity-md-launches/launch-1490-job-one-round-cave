#!/usr/bin/env python3
"""Run reviewed tool checks in a disposable mirror; write only gathering receipts."""
import datetime
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
RECEIPTS = ROOT / 'gathering/checks/round-11'
DEMOS = [
 ['line-1/tools/transport-check/transport_check.py', 'demo'],
 ['line-1/tools/direct-capture/direct_capture.py', 'demo'],
 ['line-1/tools/hash-snapshot/hash_snapshot.py', 'demo'],
 ['line-1/tools/batch-capture/batch_capture.py', 'demo'],
 ['line-1/tools/endpoint-policy/endpoint_policy.py', '--demo'],
 ['line-1/tools/snapshot-replay/replay.py', 'demo'],
 ['line-1/tools/snapshot-compare/snapshot_compare.py', 'demo'],
 ['line-2/tools/handoff/handoff.py', 'demo'],
 ['line-2/tools/handoff/handoff.py', 'verify', 'line-2/handoff.zip'],
 ['line-2/tools/handoff-inspect/inspect_handoff.py', 'demo'],
 ['line-2/tools/handoff-compare/compare_handoff.py', 'demo'],
 ['line-2/tools/handoff-source/source_check.py', 'demo'],
 ['line-2/tools/handoff-portability/portability.py', 'demo'],
 ['line-2/tools/handoff-contract/contract.py', 'demo'],
 ['line-2/tools/handoff-catalog/catalog.py', 'demo'],
 ['line-2/tools/handoff-reproduce/reproduce.py', 'demo'],
 ['line-2/tools/handoff-content/content.py', 'demo'],
 ['line-2/tools/handoff-review/review.py', 'demo'],
 ['line-3/tools/zto-eip1559-decoder/tx_decode.py', '--demo'],
 ['line-3/tools/erc20-intent/intent.py', '--demo'],
 ['line-3/tools/rpc-unsigned-reader/rpc_reader.py', '--demo'],
 ['line-3/tools/unsigned-diff/unsigned_diff.py', '--demo'],
 ['line-3/tools/unsigned-guard/guard.py', '--demo'],
 ['line-3/tools/gas-budget/gas_budget.py', '--profile', 'prague', '--demo'],
 ['line-3/tools/fee-context/fee_context.py', '--base-fee-wei', '1000000000', '--context-chain', '1', '--demo'],
 ['line-3/tools/calldata-words/word_view.py', '--demo'],
 ['line-3/tools/access-list-audit/access_audit.py', '--demo'],
 ['line-4/tools/transfer-crosscheck/crosscheck.py', '--demo'],
 ['line-4/tools/transfer-window-receipt/receipt.py', '--demo'],
 ['line-4/tools/transfer-window-coverage/coverage.py', '--demo'],
 ['line-4/tools/transfer-window-activity/activity.py', '--demo'],
 ['line-4/tools/transfer-counterparties/counterparties.py', '--demo'],
]


def main():
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    commands = []
    for n in range(1, 5):
        commands += [[p.relative_to(ROOT).as_posix()] for p in
                     sorted((ROOT / f'line-{n}/tools').glob('*/test*.py'))]
    tests_count = len(commands)
    commands += DEMOS
    results = []
    with tempfile.TemporaryDirectory(prefix='pepe-gathering11-', dir='/tmp') as raw:
        stage = Path(raw)
        for n in range(1, 5):
            shutil.copytree(ROOT / f'line-{n}', stage / f'line-{n}',
                            ignore=shutil.ignore_patterns('__pycache__'))
        (stage / 'test/scratch').mkdir(parents=True)
        # Only this disposable test copy changes. Keep fixtures in its workspace.
        source = stage / 'line-2/tools/handoff-source/test_source.py'
        source.write_text(source.read_text().replace(
            'dir="/tmp"', 'dir=str(self.previous / "test/scratch")'))
        for i, args in enumerate(commands, 1):
            command = ['python3', '-B', *args]
            try:
                run = subprocess.run(command, cwd=stage, capture_output=True,
                                     text=True, timeout=60)
                record = {'command': command, 'exit': run.returncode,
                          'stdout': run.stdout, 'stderr': run.stderr}
            except subprocess.TimeoutExpired:
                record = {'command': command, 'exit': 124,
                          'stdout': '', 'stderr': '60-second command timeout'}
            found = re.search(r'Ran (\d+) tests?', record['stderr'])
            record['tests_run'] = int(found[1]) if found else 0
            record['kind'] = 'suite' if i <= tests_count else 'demo'
            record['checked_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            record['workspace'] = 'disposable /tmp mirror; no original line writes'
            encoded = json.dumps(record, indent=2)+'\n'
            if len(encoded.encode()) >= 100000:
                raise ValueError('receipt exceeds 100 KB')
            (RECEIPTS / f'tool-{i:02d}.json').write_text(encoded)
            results.append({k: record[k] for k in ('command','exit','tests_run','kind')})
            print(i, record['exit'], record['tests_run'], ' '.join(args), flush=True)
    (RECEIPTS / 'tool-checks.json').write_text(json.dumps(results, indent=2)+'\n')
    return int(any(r['exit'] for r in results))

if __name__ == '__main__':
    raise SystemExit(main())

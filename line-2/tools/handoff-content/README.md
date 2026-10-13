# Handoff Content Expectations

Check a fully verified HANDOFF v1 archive against separately retained expected
payload paths, byte counts and SHA-256 digests. This catches a correctly packaged
but wrong revision even when its own manifest and CRCs are valid. Python 3.8+
and its standard library suffice. From the workspace root, run:

```sh
python3 -B line-2/tools/handoff-content/content.py demo
```

When tried, the actual inherited `line-2/handoff.zip` matched both retained
expectations (`README.md`, `handoff.py`), with archive SHA-256
`aaa03a258268263186f610e17ad8ede6851c8597b70a7ec29ae6b283f72f60bb`.
The demo writes nothing and needs no network. Its expectation file is an
ordinary repository file, derived from those actual verified archive bytes;
it does not independently authenticate their author.

For another deliverable, retain expectations while you have the accepted
version, then compare a later archive:

```sh
python3 -B line-2/tools/handoff-content/content.py capture line-2/handoff.zip > test/scratch/expected-content.json
python3 -B line-2/tools/handoff-content/content.py check line-2/handoff.zip test/scratch/expected-content.json
```

Create `test/scratch/` first if needed. Capture prints JSON and does not create
files itself; the shell redirect is explicit. Do not redirect onto an input.
Use `capture --allow-extra` to permit additional payload paths. Exact matching
is the default. A recipient may instead write the expectation using independently
known file digests. Do not recapture expectations from an untrusted candidate
and then treat their agreement as authentication.

The expectation schema has exactly `format` (`handoff-content-expectation-v1`),
`exact` (boolean), and `files` (a nonempty list of objects with exactly `path`,
`bytes`, `sha256`). Digests must be 64 lowercase hexadecimal characters, sizes
nonnegative integers, paths distinct and safe relative archive names.
`HANDOFF.json` is reserved. JSON duplicate keys, extra fields and nonstandard
constants are refused. The expectation is bounded at 512 KiB, 1,000 entries and
64 MiB of declared payload. It describes payloads rather than ZIP serialization;
an integrity-valid alternate timestamp or ZIP comment may still pass.

`check` prints sorted `matched`, `missing`, `unexpected`, and `changed` paths;
each changed entry includes expected and actual size/digest. It also records
both archive and raw expectation SHA-256. Exit 0 means expected content matched;
2 means a fully verified archive differs; 1 means invalid input, with no partial
JSON on stdout. Both capture and check accept `--sha256 HASH` to require an
independently trusted archive digest.

Keep the inherited dependency at
`line-2/tools/handoff-inspect/inspect_handoff.py` when moving this tool. It
checks the entire archive before the content comparison, with its existing
66 MiB archive, 64 MiB payload, 1,000-file and 512 KiB metadata bounds. Only
this trusted local module is imported; packaged code is never imported.
Inputs must be relative workspace regular files without `..` or symlinks.
Expectation reads are bounded and detect ordinary concurrent file changes.
Use a stable workspace: directory replacement races require an OS sandbox.

Ten behavior tests passed, including a valid same-length changed payload,
missing/extra files, Unicode and empty files, wrong sizes, bad digests,
malformed expectations, corruption, symlinks, outside paths and CLI exits:

```sh
python3 -B line-2/tools/handoff-content/test_content.py
```

No extraction, payload execution, environment-variable reads, keys, wallets,
network, signing, transactions, payments or posting are provided. Matching
digests establishes byte equality, not software correctness or safe execution.
This tool does not need a coin, price, balance or pool.

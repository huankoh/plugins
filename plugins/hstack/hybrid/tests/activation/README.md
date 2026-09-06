# Activation fixture v1

Use the same disposable receipt-summary application to test hstack in Cursor
local, Cursor cloud and Codex cloud. Python 3.9+ and Git are the only fixture
dependencies. Host installation and authentication are covered in [setup](../../docs/setup.md).

Fetch this directory from the exact fork commit being tested, or use a checkout
of that commit. Record `git rev-parse HEAD` in that source checkout before creating
the fixture. Keep the complete commit SHA with the host evidence so a moving
branch cannot change which activation kit ran.

From the fork checkout:

```bash
python3 pstack/hybrid/tests/activation/init_fixture.py /tmp/hstack-smoke --evidence /tmp/hstack-evidence/baseline.json
python3 pstack/hybrid/tests/activation/check_source.py --repo /tmp/hstack-smoke --save /tmp/hstack-evidence/before.json
```

Choose a fresh destination for each host or run. The initializer refuses to
overwrite nonempty directories. It creates five application files and a clean
local Git checkpoint with no remote. Initializer exit 0 means it reproduced the
expected failure: **four CLI acceptance tests, three failing**. The nested test
command exits 1. It does not change global Git configuration or call an agent.

Give the host [the Cursor prompt](cursor-prompt.md) or [the Codex prompt](codex-prompt.md),
with absolute paths for this kit, the fixture and an evidence directory outside
the fixture. Record the actual hstack skill/runtime paths and `BUILD.json` where
available. Reading staged files and native plugin discovery are different
activation mechanisms; report which happened.

| Evidence | Required result |
|---|---|
| Before repair | Three failures; sample net is incorrectly 24.75 |
| After repair | All four tests pass; sample paid=21.35, refunded=3.40, net=17.95, settled_count=3 |
| Cursor handoff | Actual Codex CLI job ID, terminal status, report, supplied check results and runner validation of current HEAD |
| Source preservation | `check_source.py --compare` exits 0 after the delegated review or rescue |
| Codex cloud | Loaded hstack identity, fix and tests; independent native review evidence if that capability exists |

For an explicit rescue-path test, initialize another buggy fixture, confirm its
writer has stopped, and submit `rescue.json` through the runner using the same
baseline for `--base` and `--head`, plus `--role rescue --writer-stopped`. Snapshot
the original before submission and compare after collecting the patch. The
original must still fail; independently inspect and apply the patch in another
disposable checkout, where all four tests must pass. The flag asserts the writer
has stopped; it does not stop Cursor. No push or merge is needed.

`check_source.py` compares HEAD, Git status, indexed entries, and hashes/modes of
tracked and nonignored untracked files. It does not claim Git bookkeeping or
ignored caches are unchanged. Logs, task JSON, snapshots and runner state belong
outside the fixture. Supplied checks execute a real subprocess CLI with temporary
CSV files; the acceptance tests are embedded in the portable initializer, not
duplicated in the maintained test suite.

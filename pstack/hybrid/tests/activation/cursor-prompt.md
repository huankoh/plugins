Use poteto-mode from the installed **hstack** plugin to fix the refund defect in
the supplied disposable fixture. Record the actual plugin identity/version,
loaded skill and runtime paths. If unavailable, report the installation blocker;
do not silently substitute upstream pstack. Preserve model preferences.

Read the fixture README, reproduce the four CLI tests with three failures, and
record BASE before editing. Implement the bounded fix without weakening tests,
run the sample CLI and all four tests, then commit locally with signing disabled.
Record HEAD. Do not push, merge or modify the main project.

Locate hstack's `hybrid/runner.py`, inspect its help, and run `doctor`. Snapshot the
fixture with the kit's `check_source.py --repo FIXTURE --save EVIDENCE/before-review.json`.
Submit an actual Codex CLI review using `--role review --repo FIXTURE --base BASE
--head HEAD --key UNIQUE_KEY --task KIT/review.json`. Use existing authentication
and the configured model default. Keep runner state outside the fixture. If CLI
sign-in is missing, preserve the fix and report that blocker; no API-key fallback.

Poll the runner, collect the terminal result, compare the source snapshot using
`--compare EVIDENCE/before-review.json`, and run `validate UNIQUE_KEY --head HEAD`
with HEAD as the literal Git ref. Require a passing report, no blocking findings,
successful supplied checks, an unchanged source and a current clean checkpoint.
Return loaded hstack identity, BASE/HEAD, actual Codex job ID, checks, report and
validation evidence. A Cursor GPT task does not establish the Codex CLI handoff.

For cloud, copy the evidence somewhere retrievable before ending the VM.

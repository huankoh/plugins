# Verification record

Validation date: 2026-09-06. Upstream baseline: `93b00b89ef425a9c1bac0d0b317dfc49c930ac99`, pstack 0.14.8.

## Local checks

- 10 Python package/runner tests pass on macOS with Python 3.9. Tests use an explicit CLI double for failure, cancellation, timeouts, duplicate keys, interrupted records, checkout ownership, patch collection and stale-review rejection.
- Both generated packages preserve all 45 skills. The Codex package preserves explicit-invocation policy and 18 inherited role defaults.
- Generated Codex package passes the native plugin-creator validator. Native app-server discovery found all 45 namespaced skills with no errors in a disposable workspace; `plugin/read` resolved the generated marketplace/package without installation.
- Existing pstack orchestration/watch-pr tests: 52 pass, 0 fail, with Bun 1.3.10. Existing strict TypeScript check passes.
- Python syntax compilation and shell syntax checks pass.

## Live CLI checks

Codex CLI 0.153.3 used the existing ChatGPT subscription and its configured default model. A real rescue changed subtraction to addition in a disposable fixture, preserved the source checkout and returned a collected patch. The parent applied that patch after inspection and reran its test. A separate real Codex review passed without changing files, and `validate --head HEAD` accepted the exact resulting commit. See [sanitized fixture evidence](../examples/verification-results.json).

The first live rescue returned completion notes as findings, so verification correctly remained failed. The report schema and prompt now explicitly reserve findings for unresolved blocking issues; the revised rescue and independent review passed. Automated fixture tests must not be confused with a real Cursor agent run.

The Cursor launcher installed its official terminal-agent dependency when asked for help. That terminal agent reports not logged in, so no authenticated Cursor implementation was claimed. No active pstack installation or model preferences were changed.

## Linux and host validation

The `pstack hybrid` GitHub Actions job runs package/runner tests, upstream tests/typecheck, and a clean Ubuntu CLI installation/version check twice without credentials. The [first clean Ubuntu run](https://github.com/huankoh/plugins/actions/runs/34019930483) passed every step, including both CLI installation invocations. Subsequent PR checks validate later changes.

Grok Bot setup and actual Cursor cloud VM execution remain documented deployment procedures awaiting live validation on the chosen account/environment. This change does not configure bots, live cloud environments, subscription credentials on another machine, or project repositories. Binary preinstallation alone is not authenticated nested execution.

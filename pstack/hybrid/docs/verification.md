# Verification record

Validation date: 2026-09-06. Upstream baseline: `93b00b89ef425a9c1bac0d0b317dfc49c930ac99`, pstack 0.14.8.

## Local checks

- Python package/runner tests pass on macOS with Python 3.9. Tests use an explicit CLI double for failure, cancellation, timeouts, duplicate keys, interrupted records, checkout ownership, patch collection and stale-review rejection.
- Both generated packages preserve all 45 skills. The Codex package preserves explicit-invocation policy and 18 inherited role defaults.
- Generated Codex package passes the native plugin-creator validator.
- Existing pstack orchestration/watch-pr tests: 52 pass, 0 fail, with Bun 1.3.10. Existing strict TypeScript check passes.
- Python syntax compilation and shell syntax checks pass.

## Live CLI checks

Codex CLI 0.153.3 reports ChatGPT subscription authentication. Live review/rescue results are recorded in the PR after completion. Automated fixture tests must not be confused with a real Cursor agent run.

The Cursor launcher installed its official terminal-agent dependency when asked for help. That terminal agent reports not logged in, so no authenticated Cursor implementation was claimed. No active pstack installation or model preferences were changed.

## Linux and host validation

The `pstack hybrid` GitHub Actions job runs package/runner tests, upstream tests/typecheck, and a clean Ubuntu CLI installation/version check twice without credentials. Its result is linked from the PR checks.

Grok Bot setup and actual Cursor cloud VM execution remain documented deployment procedures awaiting live validation on the chosen account/environment. This change does not configure bots, live cloud environments, subscription credentials on another machine, or project repositories. Binary preinstallation alone is not authenticated nested execution.

# hstack directly in Codex CLI and desktop

Build the packages using the [local guide](cursor-local.md). From the fork root, register the generated marketplace and install its package:

```bash
codex plugin marketplace add "$PWD/dist/hstack/codex"
codex plugin add hstack@hstack
```

Use the actual Codex executable path if `codex` is not on PATH. This installation is opt-in; building the package never changes the active plugin configuration. Keep the generated marketplace directory available for updates. Start a new CLI session or desktop task afterward so skills are rediscovered.

Select the native plugin entry `$hstack:hstack-poteto-mode` and provide an engineering request. Codex qualifies the skill's `hstack-poteto-mode` name with its `hstack` plugin name. Use `$hstack-poteto-mode` only when the host catalog leaves the name unqualified; the tested cloud installation also displayed `$hstack:hstack-poteto-mode` despite staging through `.agents/skills`. Check its `BUILD.json` to confirm the package source. All generated skills and named agents carry the `hstack-` prefix and resolve siblings through `SKILL-MAP.json`. The original native pstack plugin remains available as `$pstack:poteto-mode`. See [invocation and discovery](invocation.md).

Use the native plugin entry `$hstack:hstack-setup-pstack` for hstack model setup, or `$hstack-setup-pstack` when the host catalog leaves that name unqualified. The generated setup skill reads existing `~/.codex/pstack-models.json` preferences. Without preferences, roles inherit the current model. Setup preserves choices unless a change is requested. Building or installing never rewrites this file or Cursor's role settings.

The adapter uses native delegation tools when present. Codex CLI must not assume desktop task history, automations, Cursor Task, or cloud-hosting APIs exist. If independent delegation is unavailable, report that limitation rather than claiming a multi-agent review. Cursor-specific automation assets remain source material until their dependencies are configured.

For noninteractive delegation, `runner.py` invokes `codex exec` with JSON output and a report schema. Its model is the CLI default unless explicitly selected. See [noninteractive Codex](https://learn.chatgpt.com/docs/non-interactive-mode) and [Codex plugins](https://learn.chatgpt.com/docs/plugins).

## Verified local discovery

On 2026-09-07, a fresh native Codex app-server in an empty temporary directory discovered all 45 installed hstack skills alongside all 45 original personal pstack skills. Their catalog names were distinct; `hstack:hstack-poteto-mode` and `pstack:poteto-mode` were both enabled. There were no relevant catalog errors, and `plugin/read` resolved the generated hstack marketplace successfully.

The latest repeat used installed package `0.14.8+hstack.dc2ec751f51e`, built from source `bbe9d3e5d3f3531227e4c5d88da99a6394540bb1` with fingerprint `dc2ec751f51e2bba5a24770ed321447aea68f1aa14e25a9d4a5b4038b9fac868`. It passed the same discovery and separation checks. [CI passed for that source revision](https://github.com/huankoh/plugins/actions/runs/34042006313), including 48 Python tests, 52 upstream tests, and strict TypeScript checking.

The local verification workspace records this repeat in `outputs/hstack-namespace-codex-local-bbe9.json`; the earlier `8b2ed0c` probe remains in `outputs/hstack-namespace-codex-local.json`. These are local receipts, not required plugin files.

The probe called only `initialize`, `skills/list` with `forceReload`, and `plugin/read`. It created no staged skills or symlinks and started no model turn or authentication operation. This verifies native plugin discovery and separation; it does not establish that a model completed an hstack workflow or Codex review.

# hstack directly in Codex CLI and desktop

Build the packages using the [local guide](cursor-local.md). From the fork root, register the generated marketplace and install its package:

```bash
codex plugin marketplace add "$PWD/dist/hstack/codex"
codex plugin add hstack@hstack
```

Use the actual Codex executable path if `codex` is not on PATH. This installation is opt-in; building the package never changes the active plugin configuration. Keep the generated marketplace directory available for updates. Start a new CLI session or desktop task afterward so skills are rediscovered.

Select the native plugin entry `$hstack:hstack-poteto-mode` and provide an engineering request. Codex qualifies the skill's `hstack-poteto-mode` name with its `hstack` plugin name. A portable installation through `.agents/skills` instead exposes `$hstack-poteto-mode`. Check its `BUILD.json` to confirm the package source. All generated skills and named agents carry the `hstack-` prefix and resolve siblings through `SKILL-MAP.json`. The original native pstack plugin remains available as `$pstack:poteto-mode`. See [invocation and discovery](invocation.md).

Use the native plugin entry `$hstack:hstack-setup-pstack` for hstack model setup, or `$hstack-setup-pstack` for portable skills. The generated setup skill reads existing `~/.codex/pstack-models.json` preferences. Without preferences, roles inherit the current model. Setup preserves choices unless a change is requested. Building or installing never rewrites this file or Cursor's role settings.

The adapter uses native delegation tools when present. Codex CLI must not assume desktop task history, automations, Cursor Task, or cloud-hosting APIs exist. If independent delegation is unavailable, report that limitation rather than claiming a multi-agent review. Cursor-specific automation assets remain source material until their dependencies are configured.

For noninteractive delegation, `runner.py` invokes `codex exec` with JSON output and a report schema. Its model is the CLI default unless explicitly selected. See [noninteractive Codex](https://learn.chatgpt.com/docs/non-interactive-mode) and [Codex plugins](https://learn.chatgpt.com/docs/plugins).

## Verified local discovery

On 2026-09-07, a fresh native Codex app-server in an empty temporary directory discovered all 45 installed hstack skills alongside all 45 original personal pstack skills. Their catalog names were distinct; `hstack:hstack-poteto-mode` and `pstack:poteto-mode` were both enabled. There were no relevant catalog errors, and `plugin/read` resolved the generated hstack marketplace successfully.

The installed package was `0.14.8+hstack.f8db0a326ad7`, built from source `8b2ed0c623e30181dbdca56ca3d5f228fd3f2f51` with fingerprint `f8db0a326ad7844ef98ae236ddaaab99e7154975faf8d163fd6b3a67854c6145`. [CI passed for that source revision](https://github.com/huankoh/plugins/actions/runs/34040878486).

The probe called only `initialize`, `skills/list` with `forceReload`, and `plugin/read`. It created no staged skills or symlinks and started no model turn or authentication operation. This verifies native plugin discovery and separation; it does not establish that a model completed an hstack workflow or Codex review.

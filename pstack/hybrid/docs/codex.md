# hstack directly in Codex CLI and desktop

Build the packages using the [local guide](cursor-local.md). From the fork root, register the generated marketplace and install its package:

```bash
codex plugin marketplace add "$PWD/dist/hstack/codex"
codex plugin add hstack@hstack
```

Use the actual Codex executable path if `codex` is not on PATH. This installation is opt-in; building the package never changes the active plugin configuration. Keep the generated marketplace directory available for updates. Start a new CLI session or desktop task afterward so skills are rediscovered.

Invoke `$hstack-poteto-mode` and provide an engineering request. Check its `BUILD.json` to confirm the package source. All generated skills and named agents carry the `hstack-` prefix and resolve siblings through `SKILL-MAP.json`. Original pstack remains available under its original names. See [invocation and discovery](invocation.md).

Use `$hstack-setup-pstack` for hstack model setup. The generated setup skill reads existing `~/.codex/pstack-models.json` preferences. Without preferences, roles inherit the current model. Setup preserves choices unless a change is requested. Building or installing never rewrites this file or Cursor's role settings.

The adapter uses native delegation tools when present. Codex CLI must not assume desktop task history, automations, Cursor Task, or cloud-hosting APIs exist. If independent delegation is unavailable, report that limitation rather than claiming a multi-agent review. Cursor-specific automation assets remain source material until their dependencies are configured.

For noninteractive delegation, `runner.py` invokes `codex exec` with JSON output and a report schema. Its model is the CLI default unless explicitly selected. See [noninteractive Codex](https://learn.chatgpt.com/docs/non-interactive-mode) and [Codex plugins](https://learn.chatgpt.com/docs/plugins).

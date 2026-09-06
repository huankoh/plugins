# Choose the execution location

| Location | Who starts Codex | Code and results live on | Subscription login |
|---|---|---|---|
| Cursor on your computer | Cursor's terminal tools | Your computer | That computer's Codex login |
| Grok Bot | The bot's VM terminal | Persistent bot VM | Separate device login on the VM |
| Cursor cloud | The cloud agent's terminal | That cloud VM | Separate login; fresh VMs may need another |

Installing the plugin does not install Codex CLI on other machines. Installing the CLI does not authenticate it. `runner.py` always executes where its command runs; it does not forward work to a Mac or another VM.

Start with [local Cursor](cursor-local.md) or [direct Codex](codex.md). Then use the [Grok Bot guide](grok-bot.md) or [Cursor cloud guide](cursor-cloud.md) for additional hosts. Both locations can coexist. Routine unattended subscription jobs are best kept on the persistent runner; nested Cursor jobs need an authenticated VM.

Each host needs Git, Python 3.9+, the fork at a selected tested revision, and Codex CLI. Building packages also needs the pinned Python dependency. The optional CLI installer requires Node.js 20+ and npm, and installs Codex 0.153.3 into a user-owned prefix. Newer CLI versions should pass the same checks before changing that pin.

Use `codex login --device-auth` on a new host and complete the browser step yourself. The runner requires ChatGPT authentication and never falls back to API billing. Do not put auth files in Git, generated packages, shared images, or chat. The documented managed-auth CI approach requires refreshed state and is not appropriate for public/open-source repository workflows. See [Codex authentication](https://learn.chatgpt.com/docs/auth) and [managed authentication in CI](https://learn.chatgpt.com/docs/auth/ci-cd-auth).

The runner consumes no model setting unless explicitly supplied with `--model`; otherwise Codex uses its configured default. `--effort` requires an explicit model with a matching cached capability. Models available in Cursor are not necessarily valid Codex CLI identifiers.

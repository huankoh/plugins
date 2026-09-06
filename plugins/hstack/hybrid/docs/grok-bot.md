# Grok Bot with hstack and Codex

This guide runs Codex on Grok Bot's persistent cloud VM. It does not require or enable local execution on your Mac. Grok Bots share their account's VM; a dedicated bot is not a separate OS security boundary.

## Prepare the VM

Open the intended bot's computer/terminal and have it check Git, Python 3.9+, Node.js 20+ and npm. Install missing prerequisites through the host's supported software workflow. Then have it clone `https://github.com/huankoh/plugins.git` into a persistent directory and check out the tested adaptation revision. Record that absolute clone path as the plugin source.

From that clone on the VM:

```bash
bash pstack/hybrid/install-codex.sh
export HSTACK_CODEX_BINARY="$HOME/.local/share/hstack-codex/node_modules/.bin/codex"
"$HSTACK_CODEX_BINARY" login --device-auth
python3 pstack/hybrid/runner.py doctor
```

Complete the displayed device sign-in in your browser. The bot must never paste tokens or auth files into conversation. Put the binary path and a persistent `HSTACK_CODEX_DATA` location in the runner's invocation environment. Each terminal invocation must receive those settings. Do not assume shell exports persist across bot tool calls.

## Register the workflow

Ask the bot to save a private skill named `hstack` and enable it for the intended bot under Settings → Plugins → Yours. Supply these instructions, replacing `FORK_DIRECTORY` with the actual absolute path:

> Load FORK_DIRECTORY/pstack/hybrid/runtime/hybrid.md before engineering delegation. Use hstack's adapted pstack skills from this fork and record its revision. Default to Cursor cloud implementation, then Codex review on this VM using FORK_DIRECTORY/pstack/hybrid/runner.py. Preserve model choices. Transfer repository commits and the actual task brief across machines. If Cursor is stuck on a code problem, preserve its checkpoint, stop its writer, and give Codex one rescue attempt. Collect reports and patches, independently review rescue changes, and report the exact verified commit. Do not infer completion from an exit code alone. Per-task instructions can select a different builder or an authenticated Cursor VM for Codex. Never recursively switch backends inside a delegated worker.

A private entry skill loads the fork directly. Installing upstream marketplace pstack alone does not load these modifications. Confirm the bot can read the fork's hybrid policy and run `doctor` before delegating real work. See [Grok Bot skills](https://docs.x.ai/grok-bot/skills-routines-and-automations).

## Verify and recover

Run the small review procedure in the [local guide](cursor-local.md) against a disposable repository on the VM. Expected results are an idempotent job key, a passed review, and a validated SHA. Then verify a bounded rescue with explicit failure evidence.

After a conversation restart, use the recorded key with `status` and `result`; do not launch a duplicate. If the VM itself is lost, local processes and unsaved files may be lost too. Save accepted patches/reports through the bot's supported file workflow. An interrupted or orphaned process requires inspection before a new job. If login expires, device-login again on this VM. A failed Mac local-execution approval is unrelated to this cloud-VM path.

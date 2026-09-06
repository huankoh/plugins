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

Build the Cursor and Codex packages from the selected source revision using `pstack/hybrid/build.py`. Record both generated package roots and their `BUILD.json` identity. Save a private entry skill named `hstack-poteto-mode` for the intended bot. Scope its description to explicit hstack requests and that bot's role. Keep existing original bots and pstack skills intact. See [the common invocation contract](invocation.md).

Supply these instructions, replacing `FORK_DIRECTORY` and the package roots with actual absolute paths:

> Use hstack-poteto-mode for hstack engineering work. Load the selected package's SKILL-MAP.json, mapped poteto-mode workflow, and applicable Cursor or Codex adapter before each handoff. Resolve all delegated skills and agent instructions within that package. Include the hstack identity and exact entrypoint in delegated prompts. Never replace a missing hstack workflow with an original pstack workflow. Default to Cursor cloud implementation, then Codex review on this VM using FORK_DIRECTORY/pstack/hybrid/runner.py. Preserve model choices. Transfer repository commits and the actual task brief across machines. If Cursor is blocked on code, preserve its checkpoint, stop its writer, and give Codex one bounded rescue attempt. Collect reports and patches, independently inspect rescue changes, and report the exact verified commit. Per-task instructions can select a different builder or an authenticated Cursor VM. A delegated worker must stay within its assigned role.

The private entry skill loads the generated adaptation rather than the canonical unadapted pstack file. Confirm the bot can resolve the mapping and run `doctor` before delegating real work. Grok's command UI is host-specific; use the explicit `hstack-poteto-mode` name in ordinary text when a slash picker is unavailable. See [Grok Bot skills](https://docs.x.ai/grok-bot/skills-routines-and-automations).

## Verify and recover

Run the small review procedure in the [local guide](cursor-local.md) against a disposable repository on the VM. Expected results are an idempotent job key, a passed review, and a validated SHA. Then verify a bounded rescue with explicit failure evidence.

After a conversation restart, use the recorded key with `status` and `result`; do not launch a duplicate. If the VM itself is lost, local processes and unsaved files may be lost too. Save accepted patches/reports through the bot's supported file workflow. An interrupted or orphaned process requires inspection before a new job. If login expires, device-login again on this VM. A failed Mac local-execution approval is unrelated to this cloud-VM path.

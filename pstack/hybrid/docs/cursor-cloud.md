# Codex preinstalled in Cursor cloud VMs

## Build the environment

For this fork, copy `pstack/hybrid/examples/environment.json` to `.cursor/environment.json` when you are ready to configure a live environment. Merge its `install` and `start` commands with existing setup rather than overwriting project dependencies. This PR supplies the template but does not activate it.

The example uses scripts already in this repository. For another repository, copy the two versioned scripts into its setup directory and adjust the commands. Preserve the pinned version together with the copied scripts. Node.js 20+ and npm must already be available in the base environment; the installer fails clearly if they are absent.

Cursor runs `install` during an environment Build and snapshots successful disk state. New agents use the active Build, then run `start`. Shell exports and processes do not survive snapshots. A failed Build leaves the preceding successful Build active. Builds use default-branch configuration; a configuration change on a feature branch alone does not replace the active Build. Repository configuration takes precedence over personal/team environments. See [setup](https://cursor.com/docs/cloud-agent/setup) and [Builds](https://cursor.com/docs/cloud-agent/builds).

After activating a successful Build, start two fresh agents and have each run:

```bash
bash pstack/hybrid/check-codex.sh
```

Both must report the pinned CLI version. Existing agents or explicitly selected older Builds are not covered by this verification.

## Authenticate at runtime

The Build contains the executable, not a subscription login. Inside the VM where Codex will actually run:

```bash
export PSTACK_CODEX_BINARY="$HOME/.local/share/pstack-codex/node_modules/.bin/codex"
"$PSTACK_CODEX_BINARY" login --device-auth
python3 pstack/hybrid/runner.py doctor
```

Complete the device login yourself. A fresh VM may need another login. Do not snapshot a personal `auth.json` or repeatedly seed fresh VMs with one old copy. The Pro subscription path does not provide the documented Business/Enterprise workspace personal access tokens. See [authentication](https://learn.chatgpt.com/docs/auth) and [workspace access tokens](https://learn.chatgpt.com/docs/enterprise/access-tokens).

A persistent Grok VM can handle routine Codex jobs instead, using Git commit handoffs. The runner does not route between hosts automatically. If nested execution is requested but unauthenticated, report `auth_required` to the coordinator and complete sign-in; do not silently charge an API key.

## Invoke and collect

Follow the review/rescue commands in the [local guide](cursor-local.md) inside the VM. Cursor must checkpoint changes before review and stop its own writes before rescue. The runner uses a separate checkout and returns a patch, so the outer Cursor agent must inspect and apply accepted changes deliberately.

Before the VM ends, collect the report, patch and verification logs through the cloud agent's supported artifact output or an authorized branch. Files existing only on that VM are not a durable delivery. Do not export credentials or the entire private runner directory.

## Troubleshooting

- Missing/wrong CLI: check the Build succeeded, is active, and contains the expected scripts. Run the startup checker.
- Authentication failure: run device login in the current VM, not on your Mac.
- Download/API failure: inspect the effective outbound network policy. npm package downloads and Codex authentication/API endpoints must be reachable. Preserve existing policy rather than disabling controls. [Cursor secrets and networking](https://cursor.com/docs/cloud-agent/security-network).
- Worker interrupted: inspect its recorded key and collect artifacts before retrying. A success message without a collected patch/report is incomplete.

The install/start mechanism is documented. Actual nested Codex execution must be verified on your account's environment; it is not guaranteed merely because the binary is present.

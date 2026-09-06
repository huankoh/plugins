# Set up hstack and Codex in Cursor cloud VMs

## Build the environment

Install hstack in the cloud environment separately from your local Cursor installation. A local marketplace installation does not establish that a cloud agent has received or discovered the plugin.

The supplied `pstack/hybrid/examples/environment.json` installs and checks Codex CLI only. It does not fetch hstack or stage its generated Cursor package. For the complete setup, create a dedicated personal environment through Cursor's cloud setup UI and give its setup agent the following brief. Replace the commit only when you have selected another tested full SHA.

```text
Configure a personal cloud environment named hstack activation for huankoh/plugins.
Leave the connected task repository and model settings unchanged.

Use https://github.com/huankoh/plugins.git at exact commit
e35ef95c149bd2a45776779a11da7e0f68366a2c. Fetch it into ~/hstack-bootstrap,
outside the task repository, and verify HEAD before building. Preserve any
existing unrelated checkout instead of replacing it.

Provide Git, Python 3.9+ with venv/pip, Node.js 20+, and npm. Create a Python
virtual environment outside the task repository. Install the pinned requirements
from ~/hstack-bootstrap/pstack/hybrid/requirements.txt, then run that checkout's
pstack/hybrid/build.py with the virtual environment's Python.

Stage the complete generated dist/hstack/cursor/plugins/hstack directory at
~/.cursor/plugins/local/hstack. Preserve all skills, runtime adapters, assets,
configuration, manifests, and BUILD.json. If a different installation already
occupies that path, report the conflict instead of overwriting it.

Run pstack/hybrid/install-codex.sh and pstack/hybrid/check-codex.sh from the
pinned checkout. Verify codex-cli 0.153.3 at the private installer prefix.
Read the staged BUILD.json and report its source revision and fingerprint.

Save the repeatable preparation in this personal environment and complete a
successful Build before any Codex login. Do not authenticate Codex or copy
authentication files during setup. Report the environment name and Build ID.
Do not claim native cloud plugin discovery from staged files alone.
```

Cursor's setup agent can prepare and save an environment through the cloud dashboard. Keep the pinned bootstrap outside the task checkout because Builds use default-branch configuration. A feature-branch change alone does not replace the active Build. Repository `.cursor/environment.json` takes precedence over personal and team environments. [Environment setup](https://cursor.com/docs/cloud-agent/setup), [Builds](https://cursor.com/docs/cloud-agent/builds)

If you configure the repository template instead, merge its `install` and `start` commands with existing project setup. Add the pinned bootstrap, package build, and staging steps above to cover hstack itself. For another repository, use the same separate public bootstrap checkout. Do not assume that repository contains `pstack/hybrid/`.

Cursor snapshots disk state after a successful Build. New agents use the active Build and run its startup commands. Shell exports and running processes do not survive the snapshot. A failed Build leaves the preceding successful Build active. [Cloud Agent Builds](https://cursor.com/docs/cloud-agent/builds)

## Check the saved Build on fresh agents

The personal `hstack activation` environment for `huankoh/plugins` was saved through Cursor's UI with this successful Build:

| Recorded item | Value |
|---|---|
| Build ID | `bld-20260906-d9b92096-8562-458c-81c1-4921040093d3` |
| Source revision | `e35ef95c149bd2a45776779a11da7e0f68366a2c` |
| Source fingerprint | `8caa1fe2cf724fc196bc79c104fb83a1b773d7e9f8ec11f0dac37bf055074964` |
| Bootstrap checkout | `~/hstack-bootstrap` |
| Staged Cursor package | `~/.cursor/plugins/local/hstack` |
| Codex CLI | `0.153.3`, installed without credentials |

The cloud receipt fixture passed all four acceptance tests through explicit hstack file loading. A [fresh agent in the correctly selected environment](https://cursor.com/agents/bc-bdcfc8e2-6f11-4f67-a29d-db8c9533df60) confirmed the same Build, complete pinned package, matching fingerprint, and Codex CLI 0.153.3. The runner found the private installer prefix without an exported binary path. Authentication was unavailable, as expected for a Build without credentials.

That fresh agent did not discover hstack natively. Its initial catalog contained only upstream pstack's `setup-pstack` from the `cursor-public` cache, not hstack's skills. The agent explicitly loaded the staged `poteto-mode` and Cursor runtime adapter. Native cloud plugin registration has not been achieved despite the separate local Cursor plugin installation. The nested Codex review remains pending a new device approval in the task VM.

When starting a task, select the named `hstack activation` environment in the repository/environment picker. Selecting plain `plugins` or `huankoh/plugins` can select a different saved environment. Confirm the environment name and Build on the new task before testing. The pinned bootstrap is independent of the task branch, so selecting `main` also tests that separation.

One fresh probe selected plain `plugins` and used the older `Personal Environment huankoh/plugins`, whose UI showed no install script. That task lacked both the package and Codex CLI. This result identifies the wrong environment selection; it does not establish a failure of the saved hstack Build.

After explicitly selecting `hstack activation`, start two fresh agents and have each run:

```bash
bash "$HOME/hstack-bootstrap/pstack/hybrid/check-codex.sh"
python3 "$HOME/hstack-bootstrap/pstack/hybrid/runner.py" doctor
```

Both must report the pinned CLI version and the actual authentication state. Ask each agent to record whether hstack's `poteto-mode` appears in its native skill catalog before reading staged files. Verify the staged `BUILD.json` matches the selected revision. Existing agents or explicitly selected older Builds are not covered by this check.

If native discovery is unavailable, explicitly read `~/.cursor/plugins/local/hstack/skills/poteto-mode/SKILL.md` and its `hybrid/runtime/cursor.md` adapter to exercise the workflow. Record that activation method. Staging the full package preserves relative links but does not prove native plugin registration.

## Authenticate at runtime

The Build contains the executable, not a subscription login. Inside the VM where Codex will actually run:

```bash
"$HOME/.local/share/hstack-codex/node_modules/.bin/codex" login --device-auth
python3 "$HOME/hstack-bootstrap/pstack/hybrid/runner.py" doctor
```

The runner discovers the installer's private prefix without an exported `HSTACK_CODEX_BINARY` when no Codex executable is already on `PATH`. An explicit binary override and a usable `PATH` executable retain precedence. The saved Build verified private-prefix resolution.

Complete the device login yourself in the running task VM. A fresh VM may need another login. Keep the saved Build free of login state, and do not create a new snapshot from an authenticated test VM. Do not repeatedly seed fresh VMs with one old `auth.json` copy. The Pro subscription path does not provide the documented Business/Enterprise workspace personal access tokens. See [authentication](https://learn.chatgpt.com/docs/auth) and [workspace access tokens](https://learn.chatgpt.com/docs/enterprise/access-tokens).

A persistent Grok VM can handle routine Codex jobs instead, using Git commit handoffs. The runner does not route between hosts automatically. If nested execution is requested but unauthenticated, report `auth_required` to the coordinator and complete sign-in; do not silently charge an API key.

## Invoke and collect

Follow the review/rescue commands in the [local guide](cursor-local.md) inside the VM, using the runner from the pinned bootstrap checkout. Use the [activation fixture](../tests/activation/README.md) for a disposable handoff test after authentication. Cursor must checkpoint changes before review and stop its own writes before rescue. The runner uses a separate checkout and returns a patch, so the outer Cursor agent must inspect and apply accepted changes deliberately.

Before the VM ends, collect the report, patch and verification logs through the cloud agent's supported artifact output or an authorized branch. Files existing only on that VM are not a durable delivery. Do not export credentials or the entire private runner directory.

## Troubleshooting

- Missing/wrong CLI: check the Build succeeded, is active, and contains the expected scripts. Run the startup checker.
- Missing hstack: confirm the task selected `hstack activation`, then inspect the staged package and Build. A local Cursor marketplace installation does not establish cloud installation. Distinguish missing files from unavailable native discovery.
- Authentication failure: run device login in the current VM, not on your Mac.
- Download/API failure: inspect the effective outbound network policy. npm package downloads and Codex authentication/API endpoints must be reachable. Preserve existing policy rather than disabling controls. [Cursor secrets and networking](https://cursor.com/docs/cloud-agent/security-network).
- Worker interrupted: inspect its recorded key and collect artifacts before retrying. A success message without a collected patch/report is incomplete.

The install/start mechanism is documented. Actual nested Codex execution must be verified on your account's environment; it is not guaranteed merely because the binary is present.

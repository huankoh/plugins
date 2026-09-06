# Set up hstack and Codex in Cursor cloud VMs

## Build the environment

Install hstack in the cloud environment separately from your local Cursor installation. A local marketplace installation does not establish that a cloud agent has received or discovered the plugin.

The supplied `pstack/hybrid/examples/environment.json` installs and checks Codex CLI only. It does not fetch hstack or stage its generated Cursor package. For the complete setup, create a dedicated personal environment through Cursor's cloud setup UI and give its setup agent the following brief. Replace the commit only when you have selected another tested full SHA.

```text
Configure a personal cloud environment named hstack activation for huankoh/plugins.
Leave the connected task repository and model settings unchanged.

Use https://github.com/huankoh/plugins.git at exact commit
1447b237746e9ea58525a3b3209b5e8a4c5f20b1. Fetch it into ~/hstack-bootstrap,
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

Set the runtime Start command to:
bash "$HOME/hstack-bootstrap/pstack/hybrid/start-cursor.sh"
Run this only when a task VM boots, never during Build Install.

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
| Environment ID | `b0780509-a9dd-11f1-b532-320a589b8025` |
| Build ID | `bld-20260906-56da8234-7e35-41b0-b5b2-1f221b191274` |
| Source revision | `1447b237746e9ea58525a3b3209b5e8a4c5f20b1` |
| Source fingerprint | `aa26de2dc500267b3cee8f047f5cee045f634f0268eb0b4e342ac99186e0c0f0` |
| Bootstrap checkout | `~/hstack-bootstrap` |
| Staged Cursor package | `~/.cursor/plugins/local/hstack` |
| Codex CLI | `0.153.3`, installed without credentials |

An earlier [fresh agent in the correctly selected environment](https://cursor.com/agents/bc-bdcfc8e2-6f11-4f67-a29d-db8c9533df60) confirmed Build `bld-20260906-d9b92096-8562-458c-81c1-4921040093d3`, source `e35ef95c149bd2a45776779a11da7e0f68366a2c`, its matching fingerprint, and Codex CLI 0.153.3. The runner found the private installer prefix without an exported binary path. Authentication was initially unavailable. The receipt fixture passed all four acceptance tests through explicit hstack file loading.

That fresh agent did not discover hstack natively. Its initial catalog contained only upstream pstack's `setup-pstack` from the `cursor-public` cache, not hstack's skills. The agent explicitly loaded the staged `poteto-mode` and Cursor runtime adapter. Native cloud plugin registration has not been achieved despite the separate local Cursor plugin installation.

A subsequent device login in that VM enabled a real Codex review. Handoff `hstack-activation-review-20260906`, worker `36e19476b378cd8cf509213ae37ffb20`, reviewed fixture commit `c4fa19a3b5dd7ea88f31d391b6fb9a9ce1656ead`. Codex returned `pass` with no findings, the parent runner passed all four tests, source preservation passed, and HEAD validation returned true. This verifies subscription-authenticated nested execution after device login, separately from secret-based startup.

A [fresh unattended-authentication task](https://cursor.com/agents/bc-9e37244a-77fc-48b9-b18c-858f26295c2b) used the current Build in the table above. Its runtime Start restored the Environment Runtime Secret before the agent ran. Doctor reported `auth: chatgpt` and `ready: true` without manual login, restoration, or exported `CODEX_HOME` or binary overrides. The real Codex review passed with no findings; all four parent acceptance tests, source preservation, and current-HEAD validation passed. Native poteto-mode was still absent, so this run explicitly loaded the staged skill and Cursor adapter. See the [sanitized evidence](../examples/cursor-cloud-runtime-secret-verification.json).

When starting a task, select the named `hstack activation` environment in the repository/environment picker. Selecting plain `plugins` or `huankoh/plugins` can select a different saved environment. Confirm the environment name and Build on the new task before testing. The pinned bootstrap is independent of the task branch, so selecting `main` also tests that separation.

One fresh probe selected plain `plugins` and used the older `Personal Environment huankoh/plugins`, whose UI showed no install script. That task lacked both the package and Codex CLI. This result identifies the wrong environment selection; it does not establish a failure of the saved hstack Build.

After explicitly selecting `hstack activation`, start one fresh agent for the dedicated Runtime Secret trial and run:

```bash
bash "$HOME/hstack-bootstrap/pstack/hybrid/check-codex.sh"
python3 "$HOME/hstack-bootstrap/pstack/hybrid/runner.py" doctor
```

The agent must report the pinned CLI version and the actual authentication state. Record whether hstack's `poteto-mode` appears in its native skill catalog before reading staged files. Verify the staged `BUILD.json` matches the selected revision. Existing agents or explicitly selected older Builds are not covered by this check. Repeated Build-reuse probes must be credential-free or use separately provisioned sessions; do not start multiple VMs with the same static login seed.

If native discovery is unavailable, explicitly read `~/.cursor/plugins/local/hstack/skills/poteto-mode/SKILL.md` and its `hybrid/runtime/cursor.md` adapter to exercise the workflow. Record that activation method. Staging the full package preserves relative links but does not prove native plugin registration.

## Authenticate at runtime

The Build contains the executable, not a subscription login. Runtime Secret startup is described below. For a separate manual-login setup, sign in inside the VM where Codex will actually run:

```bash
"$HOME/.local/share/hstack-codex/node_modules/.bin/codex" login --device-auth
python3 "$HOME/hstack-bootstrap/pstack/hybrid/runner.py" doctor
```

The runner discovers the installer's private prefix without an exported `HSTACK_CODEX_BINARY` when no Codex executable is already on `PATH`. An explicit binary override and a usable `PATH` executable retain precedence. The saved Build verified private-prefix resolution.

Complete the device login yourself in the running task VM. A fresh VM may need another login. Keep the saved Build free of login state, and do not create a new snapshot from an authenticated test VM. Do not repeatedly seed fresh VMs with one old `auth.json` copy. The Pro subscription path does not provide the documented Business/Enterprise workspace personal access tokens. See [authentication](https://learn.chatgpt.com/docs/auth) and [workspace access tokens](https://learn.chatgpt.com/docs/enterprise/access-tokens).

### Restore a dedicated login from a Runtime Secret

`start-cursor.sh` supports a bounded bootstrap experiment with a dedicated ChatGPT login. Create that login with file-backed credential storage in a private directory outside Git. Use a separate session from the desktop. Save its complete managed `auth.json` as `HSTACK_CODEX_AUTH_JSON`, with type **Runtime Secret** and permission **Environment**, in the intended Cursor environment. Do not put the value in a prompt, ordinary environment variable, Install script, repository, or Build. Environment scope limits it to tasks using that environment. [Cursor secret scoping](https://cursor.com/docs/cloud-agent/setup#environment-scoped-secrets)

After the new scripts are installed in a credential-free Build, set its runtime Start command to:

```bash
bash "$HOME/hstack-bootstrap/pstack/hybrid/start-cursor.sh"
```

Startup restores credentials into `~/.local/share/hstack-codex-auth` only when `auth.json` is absent. Existing refreshed credentials are preserved. The directory is private, the file is mode `0600`, and the script rejects symlinks, repository paths, and API-key authentication. The hstack worker selects that dedicated home whenever the seed is present, and removes the seed from its child process environments, including verification commands. Set `HSTACK_CODEX_AUTH_HOME` to an absolute private directory if a different location is required; retain that setting if the seed is later removed so hstack keeps selecting the same cache.

This is startup bootstrap, not a shared credential-renewal service. A Pro login refreshes and changes its saved tokens. The refreshed file must survive and return to secure storage before a different VM uses that session. Cursor's current public API does not provide saved-secret write-back. Use one VM for this experiment and preserve its updated cache; do not launch concurrent VMs with the same seed or assume an old secret remains valid. A durable fresh-VM design needs an external private store with exclusive session use and write-back, or a persistent Codex worker. [OpenAI managed-auth maintenance](https://learn.chatgpt.com/docs/auth/ci-cd-auth)

`runner.py doctor` reports cached login readiness. Verify a real read-only handoff before declaring authentication works. Never treat a successful restore or `login status` alone as proof that the server accepts the credential.

A persistent Grok VM can handle routine Codex jobs instead, using Git commit handoffs. The runner does not route between hosts automatically. If nested execution is requested but unauthenticated, report `auth_required` to the coordinator and complete sign-in; do not silently charge an API key.

## Invoke and collect

Follow the review/rescue commands in the [local guide](cursor-local.md) inside the VM, using the runner from the pinned bootstrap checkout. Use the [activation fixture](../tests/activation/README.md) for a disposable handoff test after authentication. Cursor must checkpoint changes before review and stop its own writes before rescue. The runner uses a separate checkout and returns a patch, so the outer Cursor agent must inspect and apply accepted changes deliberately.

Before the VM ends, collect the report, patch and verification logs through the cloud agent's supported artifact output or an authorized branch. Files existing only on that VM are not a durable delivery. Do not export credentials or the entire private runner directory.

## Troubleshooting

- Missing/wrong CLI: check the Build succeeded, is active, and contains the expected scripts. Run the startup checker.
- Missing hstack: confirm the task selected `hstack activation`, then inspect the staged package and Build. A local Cursor marketplace installation does not establish cloud installation. Distinguish missing files from unavailable native discovery.
- Authentication failure: inspect sanitized startup output and doctor status first. During an unattended-authentication test, stop and report the failure before attempting manual login. For a separate manual-login setup, run device login in the current VM.
- Download/API failure: inspect the effective outbound network policy. npm package downloads and Codex authentication/API endpoints must be reachable. Preserve existing policy rather than disabling controls. [Cursor secrets and networking](https://cursor.com/docs/cloud-agent/security-network).
- Worker interrupted: inspect its recorded key and collect artifacts before retrying. A success message without a collected patch/report is incomplete.

Runtime Secret startup and a real nested Codex review passed in the recorded environment. Verify other environments independently; the binary or cached login status alone does not establish server authentication.

## Remote marketplace import probe

The exact tested marketplace was published as [the hstack-cursor distribution branch](https://github.com/huankoh/plugins/tree/hstack-cursor) at commit `0033863ff097f08068f06c73338721715bfeec3e`. It contains the same generated e35ef95 package as the working local installation; adaptation source and review remain on the PR branch.

Importing that `/tree/hstack-cursor` URL through Cursor's **Import from GitHub** UI imported the default-branch marketplace with 65 upstream plugins instead of hstack. The experimental registration was removed without installing any of those plugins. Do not use that branch URL as a verified installation recipe. Native cloud registration remains unresolved; the saved environment's explicit staged-file workflow is the tested cloud mechanism.

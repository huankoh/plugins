# Set up hstack and Codex in Cursor cloud VMs

## Make hstack available in a fresh cloud task

Fresh Cursor cloud discovery passed with the pinned GitHub marketplace installed and personal skill sync enabled. The agent's initial catalog contained `hstack-poteto-mode` and `hstack-setup-pstack`; invoking the entrypoint loaded its package map and Cursor runtime without a manual file path. Use `/hstack-poteto-mode` for hstack and `/poteto-mode` for original pstack.

The tested setup was:

1. Install the pinned remote hstack marketplace and its plugin using the [Cursor local guide](cursor-local.md#install-the-pinned-remote-marketplace). The tested distribution commit is `66b1ac1ac6ae2c190a9ff20a9f1db28f367c4977`, built from source `bbe9d3e5d3f3531227e4c5d88da99a6394540bb1`. The namespaced distribution is still on its review branch, not `main`.
2. Build that source revision and export its 45 self-contained wrappers to personal skills:

   ```bash
   .venv/bin/python pstack/hybrid/install-cursor-skills.py dist/hstack/cursor/plugins/hstack
   ```

3. Enable **Settings → Agents → Context and Tools → Sync Skills for Cloud Agents** and wait for **Skills synced**. In the recorded setup, Cursor showed 47 personal skills: the 45 hstack exports and two existing styles, which were preserved.
4. Start a fresh cloud task and verify the hstack entry in its initial catalog before providing any explicit package path. Then invoke `/hstack-poteto-mode` normally.

The successful task selected a **native plugin cache**, not a personal wrapper path. The same Build had previously failed discovery before sync was enabled. These observations establish the combined setup; they do not prove that personal sync alone caused native plugin discovery. [Cursor skills](https://cursor.com/docs/skills), [cloud skill support](https://cursor.com/help/ai-features/cloud-agents)

Personal skills are account context. Codex CLI, its login, project dependencies, and the selected cloud environment remain separate preparation for each execution environment. This discovery result does not make every repository's cloud VM ready to run Codex.

## Recorded fresh cloud result

The [fresh discovery task](https://cursor.com/agents/bc-d843572d-c606-49ae-9ecf-c3023d85788b) passed with this identity:

| Recorded item | Value |
| --- | --- |
| Environment | `hstack activation` (`b0780509-a9dd-11f1-b532-320a589b8025`) |
| Tested Build | `bld-20260906-80bd34e2-4fa9-491b-8257-d1ac578b06a4` |
| Source revision | `bbe9d3e5d3f3531227e4c5d88da99a6394540bb1` |
| Source fingerprint | `dc2ec751f51e2bba5a24770ed321447aea68f1aa14e25a9d4a5b4038b9fac868` |
| Distribution revision | `66b1ac1ac6ae2c190a9ff20a9f1db28f367c4977` |
| Selected cache | `/home/ubuntu/.cursor/plugins/cache/hstack/61205765/66b1ac1ac6ae2c190a9ff20a9f1db28f367c4977/` |

Both namespaced entrypoints were present in the initial catalog. The agent loaded the normal entrypoint, `SKILL-MAP.json`, and `hybrid/runtime/cursor.md`, confirmed the matching package identity, and left Git status clean. It did not touch authentication, run Codex, or change model settings.

This test used a discovery-only startup configuration. The environment's saved Start has since been restored to the plain command below. Configuration Build `bld-20260906-28431fa6-f2ac-4c67-82b4-007d1b671d3a` succeeded and is active with the same source pin. The native discovery pass belongs to the tested `80bd34e2` Build above; restoring normal Start does not establish a new authentication or Codex execution result.

## Prepare Codex in the selected environment

Use a separate bootstrap checkout at `~/hstack-bootstrap` so the application repository need not contain hstack files. Fetch `https://github.com/huankoh/plugins.git` at exact source `bbe9d3e5d3f3531227e4c5d88da99a6394540bb1` and verify HEAD. Preserve unrelated checkouts and project settings.

The environment needs Git, Python 3.9+ with the pinned `pstack/hybrid/requirements.txt`, Node.js 20+, and npm. Build the package with the selected Python, then run `pstack/hybrid/install-codex.sh` and `pstack/hybrid/check-codex.sh` from that checkout. The tested CLI version is `0.153.3`. Save only credential-free Build preparation.

Use this normal runtime Start command:

```bash
bash "$HOME/hstack-bootstrap/pstack/hybrid/start-cursor.sh"
```

This checks Codex and runs the existing configured authentication bootstrap. It does not export project skills. The earlier `--skills ...` project-export experiment did not establish discovery and is not the current discovery recipe. If Python dependencies use a private virtual environment, append `--python /absolute/path/to/venv/bin/python` or retain `HSTACK_PYTHON` as an environment setting; shell exports alone do not survive snapshots.

Select the intended environment, such as **hstack activation**, explicitly when starting a task. A local plugin installation does not create its CLI or login, and selecting plain `plugins` may choose a different saved environment. The [environment template](../examples/environment.json) installs and checks only CLI. Preserve existing project setup when integrating the bootstrap. Repository `.cursor/environment.json` takes precedence over personal and team environments. [Environment setup](https://cursor.com/docs/cloud-agent/setup)

New agents use the selected environment's active successful Build. A failed Build leaves the preceding successful Build active; existing VMs are not updated by a new snapshot. [Cloud Agent Builds](https://cursor.com/docs/cloud-agent/builds)

## Authenticate on the execution VM

The Build contains Codex CLI, not a subscription login. Skill discovery and Codex readiness are separate. Use normal Start for a separately authorized authentication and execution test. For a separate manual-login setup, run:

```bash
"$HOME/.local/share/hstack-codex/node_modules/.bin/codex" login --device-auth
python3 "$HOME/hstack-bootstrap/pstack/hybrid/runner.py" doctor
```

Use the configured Python environment if applicable. The runner finds the installer's private prefix when no usable Codex executable is on `PATH`; explicit binary settings and a usable `PATH` executable retain precedence. Complete the device login in the VM where Codex will run. Keep login state out of Builds, and do not snapshot an authenticated test VM. The Pro subscription path does not provide the documented Business/Enterprise workspace personal access tokens. [Authentication](https://learn.chatgpt.com/docs/auth), [workspace access tokens](https://learn.chatgpt.com/docs/enterprise/access-tokens)

### Existing Runtime Secret bootstrap

Normal `start-cursor.sh` retains the existing bounded authentication bootstrap. Marketplace discovery and personal skill sync do not provide a Codex login. A dedicated ChatGPT session can be supplied as `HSTACK_CODEX_AUTH_JSON`, with type **Runtime Secret** and permission **Environment**, in the intended Cursor environment. Provision that session separately from desktop login, using file-backed credential storage outside Git. Do not place its value in a prompt, ordinary environment variable, Install script, repository, or Build. [Cursor secret scoping](https://cursor.com/docs/cloud-agent/setup#environment-scoped-secrets)

Startup restores the login into `~/.local/share/hstack-codex-auth` only when `auth.json` is absent. It preserves existing refreshed credentials, uses private directory permissions and a `0600` file, and rejects symlinks, repository paths, and API-key authentication. The worker selects that dedicated home and removes the seed from child environments, including verification commands. Retain any existing `HSTACK_CODEX_AUTH_HOME` override so later jobs continue using the same cache.

A static Runtime Secret does not provide durable unattended authentication across fresh or concurrent VMs. ChatGPT refreshes and changes its saved tokens; the updated file must return to secure storage before another VM uses that session. Cursor's current public API does not provide saved-secret write-back. Use one VM for this experiment and preserve its refreshed cache. A durable design needs an external private store with exclusive session use and write-back, or a persistent Codex worker. Do not reuse one old seed for repeated discovery probes. The recorded discovery-only tests skipped authentication startup. [Managed-auth maintenance](https://learn.chatgpt.com/docs/auth/ci-cd-auth)

Doctor reports cached readiness. Require an actual read-only Codex handoff before declaring authentication successful; restoring a file or reporting login status alone does not prove server acceptance. If nested execution is unauthenticated, report `auth_required`. The runner neither switches to an API key nor routes the job to another host automatically.

## Run and collect the result

Invoke `/hstack-poteto-mode` after discovery. For implementation, the runtime defaults to Cursor building and actual Codex CLI review. Questions and planning do not automatically start review. Follow the review/rescue procedure in the [local guide](cursor-local.md), using the pinned runner, and use the [activation fixture](../tests/activation/README.md) for a disposable execution test.

Cursor checkpoints changes before review and stops its own writes before rescue. The runner works in a separate checkout; the outer agent inspects and applies any accepted rescue patch and reviews the final commit. Collect the report, patch, and relevant verification logs through supported artifacts or an authorized branch before the VM ends. Do not export credentials or the whole private runner directory.

## Earlier evidence and limits

- At source `8b2ed0c`, Start exited successfully and exported all 45 wrappers into `/workspace/.cursor/skills`, with a clean Git status, but the [fresh task](https://cursor.com/agents/bc-2c9703b3-10bf-4fb8-a5cf-3b9950f1194d) did not expose the hstack poteto entrypoint. Removing the entrypoint's inherited mode and explicit-only flags in `bbe9d3e` still did not establish cloud discovery before personal sync was enabled. Project export success alone is not a discovery result.
- On 2026-09-06, source `e35ef95` completed a [device-login review test](https://cursor.com/agents/bc-bdcfc8e2-6f11-4f67-a29d-db8c9533df60) using explicit staged-file loading. Source `1447b23` then completed a [fresh Runtime Secret trial](https://cursor.com/agents/bc-9e37244a-77fc-48b9-b18c-858f26295c2b) without manual login. Both real reviews passed all four parent acceptance tests, source preservation, and current-commit validation. These are earlier execution results; neither proved namespaced discovery. [Runtime Secret evidence](../examples/cursor-cloud-runtime-secret-verification.json)
- The former `huankoh/plugins/tree/hstack-cursor` UI import selected 65 default-branch upstream plugins instead of hstack and was removed. The current installation uses the public `huankoh/hstack` marketplace with an explicit Git ref.

## Troubleshooting

- Missing hstack: confirm the pinned marketplace and plugin are installed, personal export completed, sync reports **Skills synced**, and the task is fresh. Inspect the initial catalog and selected cache path. Do not substitute original pstack or claim discovery from copied files alone.
- Missing CLI: verify the selected environment's successful Build and run `check-codex.sh`. Personal sync does not install executables.
- Authentication failure: inspect sanitized startup output and doctor. Record an unattended-test failure before attempting a separate manual login. Never reuse a stale seed to hide the failure.
- Network failure: inspect effective outbound policy for npm downloads and Codex authentication/API endpoints. Preserve existing controls. [Cursor networking](https://cursor.com/docs/cloud-agent/security-network)
- Interrupted worker: inspect its recorded job key and collect artifacts before retrying. A success message without its report and validation is incomplete.

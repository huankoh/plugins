# Set up hstack and Codex in Cursor cloud VMs

## Activate skills when each VM starts

The new startup procedure builds a pinned hstack package and exports its 45 uniquely named skills into Cursor's supported skill directory. The first fresh cloud probe at source `8b2ed0c` did not discover the hstack entrypoint. Read-only diagnosis then confirmed Start exited 0, exported all 45 wrappers under `/workspace/.cursor/skills`, and kept Git status clean. That build retained pstack's `disable-model-invocation: true` and `mode: true` entry metadata. The generator now removes those flags only from hstack's entrypoint; a fresh cloud test of that fix is required. A successful Build alone does not establish discovery.

When `/hstack-poteto-mode` appears in the fresh agent's catalog, invoke it normally. Its wrapper loads the bundled hstack workflow and runtime adapter, so no file-loading prompt is needed after successful discovery.

The startup command is:

```bash
bash "$HOME/hstack-bootstrap/pstack/hybrid/start-cursor.sh" \
  --skills "$HOME/hstack-bootstrap/dist/hstack/cursor/plugins/hstack"
```

Run Start from the connected repository when available. The activator finds its Git root and exports into `.cursor/skills`; outside a Git checkout, it uses `~/.cursor/skills`. Project exports receive exact entries in repository-local Git exclusions, keeping those generated directories out of application commits. It preserves original pstack and other skills and refuses to overwrite unrecognized or modified hstack exports.

Each exported skill points to the complete shared package under `hstack-poteto-mode/references/hstack-package`. Its `SKILL-MAP.json` keeps delegated workflows in the same hstack package. Bundled workflow files use `WORKFLOW.md` so Cursor discovers only the 45 public wrappers. An invalid package or missing dependency is an error, never permission to substitute pstack. See [invocation and discovery](invocation.md).

This uses Cursor's documented project and personal skill directories. Native marketplace plugin registration and personal skill sync are separate mechanisms. The saved Build described below succeeded, but fresh cloud discovery has not passed. [Cursor skills](https://cursor.com/docs/skills), [cloud skill support](https://cursor.com/help/ai-features/cloud-agents)

## Prepare and save the environment

Local Cursor installation does not prepare a cloud environment. Create or update a dedicated personal environment through Cursor's cloud setup UI using this brief:

```text
Configure the personal hstack activation environment for huankoh/plugins.
Preserve the connected task repository and existing model settings.

Fetch https://github.com/huankoh/plugins.git at exact commit
8b2ed0c623e30181dbdca56ca3d5f228fd3f2f51 into ~/hstack-bootstrap,
outside the task repository, and verify HEAD. Preserve any unrelated checkout;
only update an existing clean hstack bootstrap after verifying its remote.

Provide Git, Python 3.9+ with pip, Node.js 20+, and npm. Install the pinned
requirements from ~/hstack-bootstrap/pstack/hybrid/requirements.txt into the
Python used by both Build and Start. Run that checkout's pstack/hybrid/build.py,
keeping its generated package at ~/hstack-bootstrap/dist/hstack.

Run pstack/hybrid/install-codex.sh and pstack/hybrid/check-codex.sh from that checkout.
Verify codex-cli 0.153.3 and the generated Cursor package's BUILD.json:
source 8b2ed0c623e30181dbdca56ca3d5f228fd3f2f51, fingerprint
f8db0a326ad7844ef98ae236ddaaab99e7154975faf8d163fd6b3a67854c6145.

Set runtime Start to:
bash "$HOME/hstack-bootstrap/pstack/hybrid/start-cursor.sh" --skills "$HOME/hstack-bootstrap/dist/hstack/cursor/plugins/hstack"
Run Start when a task VM boots, from the connected repository when available.
Do not run authentication startup during Build Install.

Save the repeatable preparation and finish a successful Build. Do not log in
to Codex or copy login files into the Build. Report the environment and Build
IDs. A successful Build does not itself establish fresh-agent skill discovery.
```

If dependencies use a private Python virtual environment, append `--python /absolute/path/to/venv/bin/python` to Start, or retain its path as `HSTACK_PYTHON`. Shell exports alone do not survive the Build snapshot.

Keep the bootstrap outside the application checkout; other repositories need not contain `pstack/hybrid/`. The supplied [environment template](../examples/environment.json) installs and checks only Codex CLI. Merge the complete bootstrap and Start commands above with existing project setup when using a repository environment instead. Repository `.cursor/environment.json` takes precedence over personal and team environments. [Environment setup](https://cursor.com/docs/cloud-agent/setup)

Cursor snapshots disk state after a successful Build. New agents use the selected environment's active Build and run its startup commands; a failed Build leaves the preceding successful Build active. Existing VMs are not updated by saving a new Build. [Cloud Agent Builds](https://cursor.com/docs/cloud-agent/builds)

## Verify the fresh agent

Select **hstack activation** explicitly in the repository/environment picker. Selecting plain `plugins` can choose a different saved environment.

The latest saved Build is:

| Recorded item | Value |
| --- | --- |
| Environment | `hstack activation` (`b0780509-a9dd-11f1-b532-320a589b8025`) |
| Successful Build | `bld-20260906-ccf3b052-2928-442f-98b2-396eaf19ad9e` |
| Source revision | `8b2ed0c623e30181dbdca56ca3d5f228fd3f2f51` |
| Source fingerprint | `f8db0a326ad7844ef98ae236ddaaab99e7154975faf8d163fd6b3a67854c6145` |
| Cursor package | `~/hstack-bootstrap/dist/hstack/cursor/plugins/hstack` |
| Codex CLI | `0.153.3`, installed without credentials |

For discovery verification without touching an existing login seed, use this temporary Start variant:

```bash
bash "$HOME/hstack-bootstrap/pstack/hybrid/start-cursor.sh" \
  --skills "$HOME/hstack-bootstrap/dist/hstack/cursor/plugins/hstack" \
  --skills-only
```

`--skills-only` exports the skills and exits before CLI checks, credential restoration, or doctor. The [fresh discovery probe](https://cursor.com/agents/bc-2c9703b3-10bf-4fb8-a5cf-3b9950f1194d) used this mode, but its initial catalog listed only upstream pstack's `setup-pstack`, with no hstack entries. Startup output, exported files, working directory, and indexing behavior are under investigation. Do not treat this Build as verified automatic activation yet.

Inspect the fresh agent's skill catalog before manually reading any package files. Require `hstack-poteto-mode`, its wrapper path, the expected package source, and a clean application checkout. Original pstack must remain a separate entry. Then invoke `/hstack-poteto-mode` for a small explanation task and verify it follows the bundled hstack workflow. This establishes discovery and selection; a coding review still needs the separate authentication and execution checks below.

If the entry is absent, inspect Start's activation result, its chosen project or personal scope, and the effective environment. Report a discovery failure instead of claiming automatic activation from files alone. Explicit file loading can diagnose the package, but does not satisfy this test.

## Authenticate on the execution VM

The Build contains Codex CLI, not a subscription login. After discovery verification, use normal Start without `--skills-only` for an authenticated execution test. For a separate manual-login setup, run:

```bash
"$HOME/.local/share/hstack-codex/node_modules/.bin/codex" login --device-auth
python3 "$HOME/hstack-bootstrap/pstack/hybrid/runner.py" doctor
```

Use the configured Python environment if applicable. The runner finds the installer's private prefix when no usable Codex executable is on `PATH`; explicit binary settings and a usable `PATH` executable retain precedence. Complete the device login in the VM where Codex will run. Keep login state out of Builds, and do not snapshot an authenticated test VM. The Pro subscription path does not provide the documented Business/Enterprise workspace personal access tokens. [Authentication](https://learn.chatgpt.com/docs/auth), [workspace access tokens](https://learn.chatgpt.com/docs/enterprise/access-tokens)

### Existing Runtime Secret bootstrap

Normal `start-cursor.sh --skills ...` retains the existing bounded authentication bootstrap after skill activation. A dedicated ChatGPT session can be supplied as `HSTACK_CODEX_AUTH_JSON`, with type **Runtime Secret** and permission **Environment**, in the intended Cursor environment. Provision that session separately from desktop login, using file-backed credential storage outside Git. Do not place its value in a prompt, ordinary environment variable, Install script, repository, or Build. [Cursor secret scoping](https://cursor.com/docs/cloud-agent/setup#environment-scoped-secrets)

Startup restores the login into `~/.local/share/hstack-codex-auth` only when `auth.json` is absent. It preserves existing refreshed credentials, uses private directory permissions and a `0600` file, and rejects symlinks, repository paths, and API-key authentication. The worker selects that dedicated home and removes the seed from child environments, including verification commands. Retain any existing `HSTACK_CODEX_AUTH_HOME` override so later jobs continue using the same cache.

A static Runtime Secret does not provide durable unattended authentication across fresh or concurrent VMs. ChatGPT refreshes and changes its saved tokens; the updated file must return to secure storage before another VM uses that session. Cursor's current public API does not provide saved-secret write-back. Use one VM for this experiment and preserve its refreshed cache. A durable design needs an external private store with exclusive session use and write-back, or a persistent Codex worker. Do not reuse one old seed for repeated discovery probes; `--skills-only` avoids consuming it. [Managed-auth maintenance](https://learn.chatgpt.com/docs/auth/ci-cd-auth)

Doctor reports cached readiness. Require an actual read-only Codex handoff before declaring authentication successful; restoring a file or reporting login status alone does not prove server acceptance. If nested execution is unauthenticated, report `auth_required`. The runner neither switches to an API key nor routes the job to another host automatically.

## Run and collect the result

Invoke `/hstack-poteto-mode` after discovery. For implementation, the runtime defaults to Cursor building and actual Codex CLI review. Questions and planning do not automatically start review. Follow the review/rescue procedure in the [local guide](cursor-local.md), using the pinned runner, and use the [activation fixture](../tests/activation/README.md) for a disposable execution test.

Cursor checkpoints changes before review and stops its own writes before rescue. The runner works in a separate checkout; the outer agent inspects and applies any accepted rescue patch and reviews the final commit. Collect the report, patch, and relevant verification logs through supported artifacts or an authorized branch before the VM ends. Do not export credentials or the whole private runner directory.

## Earlier evidence and limits

The following 2026-09-06 tests used the previous staged-file approach. They establish earlier authentication and execution behavior, not automatic discovery for the new namespaced export:

- Source `e35ef95c149bd2a45776779a11da7e0f68366a2c`: a [fresh agent](https://cursor.com/agents/bc-bdcfc8e2-6f11-4f67-a29d-db8c9533df60) lacked native hstack discovery. Explicit loading from `~/.cursor/plugins/local/hstack` followed by device login produced a real Codex review with no findings; all four parent acceptance tests, source preservation, and current-commit validation passed.
- Source `1447b237746e9ea58525a3b3209b5e8a4c5f20b1`, Build `bld-20260906-56da8234-7e35-41b0-b5b2-1f221b191274`: a [fresh Runtime Secret trial](https://cursor.com/agents/bc-9e37244a-77fc-48b9-b18c-858f26295c2b) restored the dedicated login without manual intervention and passed a real review plus the same acceptance checks. Native hstack discovery was absent, so this run also loaded files explicitly. [Recorded evidence](../examples/cursor-cloud-runtime-secret-verification.json)
- Importing the former `huankoh/plugins/tree/hstack-cursor` marketplace URL selected the default-branch marketplace with 65 upstream plugins. The experimental registration was removed. That branch URL is not a verified installation recipe. The current startup skill export does not depend on native cloud marketplace registration.

## Troubleshooting

- Missing hstack: confirm the selected environment, successful active Build, Start command with `--skills`, activation scope, and unique catalog name. A local marketplace install or a copied package alone proves none of these.
- Missing CLI: check the pinned Build and run `check-codex.sh`; a discovery-only Start intentionally skips that check.
- Authentication failure: inspect sanitized startup output and doctor. During an unattended test, record the failure before attempting a separate manual login. Never reuse a stale seed to hide the failure.
- Network failure: inspect effective outbound policy for npm downloads and Codex authentication/API endpoints. Preserve existing controls. [Cursor networking](https://cursor.com/docs/cloud-agent/security-network)
- Interrupted worker: inspect its recorded job key and collect artifacts before retrying. A success message without its report and validation is incomplete.

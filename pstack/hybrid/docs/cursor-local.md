# hstack in Cursor with local Codex

Use `/hstack-poteto-mode` for hstack and `/poteto-mode` for the original pstack. All hstack skill and agent names have a distinct prefix. See [invocation and automatic discovery](invocation.md) for the portable skill installation, which can coexist with the original pstack.

## Install the pinned remote marketplace

The namespaced release is under review on `huankoh/hstack`'s `feat/namespaced-hstack-skills` branch. It is not yet the default-branch package. The adaptation source remains in `huankoh/plugins` on `feat/pstack-codex-support`. Pin the tested distribution commit instead of importing an unqualified default branch:

```bash
agent plugin marketplace add https://github.com/huankoh/hstack.git \
  --git-ref 66b1ac1ac6ae2c190a9ff20a9f1db28f367c4977
```

This command was verified with Cursor Agent CLI `2026.09.02-c22c1a3`. Use the actual `agent` executable path if it is not on `PATH`. `--git-ref` accepts a branch, tag, or commit; the command above selects the tested commit explicitly.

If an older marketplace named `hstack` is already registered, first inspect `agent plugin marketplace list`. The tested CLI retained the old file-URL registration when the new URL reused its name. Remove that old hstack registration with `agent plugin marketplace remove hstack`, then repeat the pinned add command. Do not remove the original pstack marketplace.

In native Cursor, open **Customize → Add**, choose **hstack** from the registered marketplace, and install it. Start a fresh local task afterward. Registering the marketplace alone does not install its plugin.

## Verify local discovery

The native Cursor task **Hstack-poteto-mode activation**, run on **This Mac** without a repository on 2026-09-07, passed local discovery for source `bbe9d3e5d3f3531227e4c5d88da99a6394540bb1`. The catalog exposed 45 hstack skills and two agents, including `hstack-poteto-mode` and `hstack-setup-pstack`, separately from original pstack's `setup-pstack`. It selected hstack and loaded its Cursor runtime adapter without a manual file path.

The tested package is `0.14.8+hstack.dc2ec751f51e`, distributed by the pinned commit above. The local receipt is `outputs/hstack-namespace-cursor-local.json` in the verification workspace. This test changed no authentication or model settings and ran no Codex job; cloud discovery and authenticated review are separate checks.

Invoke `/hstack-poteto-mode` and verify that the loaded skill belongs to hstack, with its `BUILD.json` and `SKILL-MAP.json` resolving the selected package. Original pstack remains `/poteto-mode`. See [invocation and discovery](invocation.md) for portable skills and the host-specific naming rules.

## Build from the source fork

For development or the runner commands below, clone `https://github.com/huankoh/plugins.git` and check out the tested source revision. The adaptation is on `feat/pstack-codex-support` before merge. From that clone's root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r pstack/hybrid/requirements.txt
.venv/bin/python pstack/hybrid/build.py
```

Building creates the Cursor and Codex packages under `dist/hstack`; it does not install or register either package. Keep the complete source or generated package available for auxiliary assets that Cursor may omit from its cache.

### Earlier local-file marketplace method

Before the pinned remote marketplace was registered, local testing used:

```bash
python3 pstack/hybrid/install-cursor-local.py dist/hstack/cursor
```

That installer publishes a generated marketplace into its own Git repository at `~/.local/share/hstack-cursor-marketplace`, preserving cached revisions and refusing unrelated destinations or local edits. Cursor's **Import from Disk** UI can import that repository. This is the earlier development method, not the remote installation used by the current discovery test.

Importing `dist/hstack/cursor` directly previously failed during runtime fetch because it is not its own Git repository. Importing `dist/hstack/cursor/plugins/hstack` lacks the marketplace manifest. A development symlink at `~/.cursor/plugins/local/hstack` also failed to expose the plugin in the tested Agents UI. These earlier failures do not describe the current pinned remote marketplace. [Cursor plugins](https://cursor.com/docs/plugins), [marketplace structure](https://cursor.com/docs/reference/plugins#cursor-multi-plugin-repositories)

## Prepare Codex

An existing Codex installation can be used. Otherwise, with Node.js 20+ and npm installed:

```bash
bash pstack/hybrid/install-codex.sh
export HSTACK_CODEX_BINARY="$HOME/.local/share/hstack-codex/node_modules/.bin/codex"
"$HSTACK_CODEX_BINARY" login --device-auth
python3 pstack/hybrid/runner.py doctor
```

`doctor` must report `ready: true` and `auth: chatgpt`. The runner also searches PATH and the standard Codex desktop application location on macOS. Set `HSTACK_CODEX_BINARY` when the desired executable is elsewhere. Set it in each terminal/session that invokes the runner; a one-time export is not a global Cursor setting.

## Run a review

Have Cursor commit its implementation on a task branch. Copy `examples/review.json` to a task file and add the actual acceptance commands as argv arrays. `checks: []` means no automated checks were supplied; it does not imply tests passed.

From the fork root, replace `/absolute/project`, `BASE_SHA` and `HEAD_SHA` with the actual repository and commits:

```bash
python3 pstack/hybrid/runner.py submit --repo /absolute/project \
  --base BASE_SHA --head HEAD_SHA --key example-review-1 \
  --task pstack/hybrid/examples/review.json
python3 pstack/hybrid/runner.py status example-review-1
python3 pstack/hybrid/runner.py result example-review-1
python3 pstack/hybrid/runner.py validate example-review-1 --head HEAD_SHA
```

The result command collects evidence after the worker exits. Expected success is `status: succeeded`, `verification: passed`, then `valid: true`. Verify against the project's actual current commit, not an old copied SHA. Keys are idempotent; reuse a key only for the identical request. Use a new key when the task or commit changes.

For a rescue, checkpoint Cursor's partial changes, stop its writer, and supply the concrete failure in a task JSON. Submit with `--role rescue --writer-stopped`. Review the returned patch independently before applying it to the clean checkpoint checkout with `git apply --check` followed by `git apply`. Commit and verify the final result normally. The flag records the coordinator's assertion; it does not stop Cursor itself.

To cancel, run `runner.py cancel KEY`, then inspect `result KEY` until terminal. Defaults allow one active job per source repository and 30 minutes per worker. Job state remains under `~/.local/share/hstack`; it is private local state, not a directory to commit.

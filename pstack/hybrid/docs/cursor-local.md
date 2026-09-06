# Cursor with local Codex

## Build and load the fork

After reviewing the adaptation PR, clone `https://github.com/huankoh/plugins.git` and check out the tested revision containing it. Before merge, that is the `feat/pstack-codex-support` branch. From the clone root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r pstack/hybrid/requirements.txt
.venv/bin/python pstack/hybrid/build.py
mkdir -p ~/.cursor/plugins/local
ln -s "$PWD/dist/pstack-hybrid/cursor/plugins/pstack-hybrid" ~/.cursor/plugins/local/pstack-hybrid
```

If that symlink already exists, inspect its target before deliberately updating it. Reload Cursor and check that the local `pstack-hybrid` package is visible. Use its `poteto-mode` skill, explicitly selecting the fork's package rather than another pstack installation. Ask the agent to read `BUILD.json` and report its fingerprint.

Cursor discovers local plugins only when local imports are allowed. On managed accounts, an admin may control this. A marketplace package with the same name takes precedence over a local copy, hence the distinct package name. See [Cursor plugins](https://cursor.com/docs/plugins).

## Prepare Codex

An existing Codex installation can be used. Otherwise, with Node.js 20+ and npm installed:

```bash
bash pstack/hybrid/install-codex.sh
export PSTACK_CODEX_BINARY="$HOME/.local/share/pstack-codex/node_modules/.bin/codex"
"$PSTACK_CODEX_BINARY" login --device-auth
python3 pstack/hybrid/runner.py doctor
```

`doctor` must report `ready: true` and `auth: chatgpt`. The runner also searches PATH and the standard Codex desktop application location on macOS. Set `PSTACK_CODEX_BINARY` when the desired executable is elsewhere. Set it in each terminal/session that invokes the runner; a one-time export is not a global Cursor setting.

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

To cancel, run `runner.py cancel KEY`, then inspect `result KEY` until terminal. Defaults allow one active job per source repository and 30 minutes per worker. Job state remains under `~/.local/share/pstack-hybrid`; it is private local state, not a directory to commit.

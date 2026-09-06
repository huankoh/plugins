# hstack in Cursor with local Codex

## Build and load the fork

After reviewing the adaptation PR, clone `https://github.com/huankoh/plugins.git` and check out the tested revision containing it. Before merge, that is the `feat/pstack-codex-support` branch. From the clone root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r pstack/hybrid/requirements.txt
.venv/bin/python pstack/hybrid/build.py
python3 pstack/hybrid/install-cursor-local.py dist/hstack/cursor
```

The installer copies the generated marketplace into a dedicated Git repository at **`~/.local/share/hstack-cursor-marketplace`**. It commits changed package contents locally, preserves earlier commits for Cursor's cached fetches, and reports `unchanged` when run again with identical contents. Use `--destination /absolute/path` to choose another location. It refuses unrecognized existing destinations and local edits; it does not push or change global Git settings.

In Cursor, open **Customize → Add Marketplace → Import from Disk** (or **Plugins → Add → From Local Repository** in the other layout) and select **`~/.local/share/hstack-cursor-marketplace`** (or the installer-reported path). Choose **hstack** from the imported marketplace and install it. Rebuild and rerun the installer when updating hstack, then refresh the imported marketplace in Cursor.

Do not import `dist/hstack/cursor` directly. That generated directory can initially display 45 skills, but it is not a Git repository: runtime fetches then fail with “not a git repository.” Selecting `dist/hstack/cursor/plugins/hstack` instead fails earlier because it has no marketplace manifest. The stable installation provides both `.cursor-plugin/marketplace.json` and its own Git history.

Confirm hstack and its 45 skills appear in Customize. Use its `poteto-mode` skill, explicitly selecting the fork's package rather than another pstack installation. Ask the agent to read the package's `BUILD.json` and report its fingerprint. The tested native catalog gave a full path for `setup-pstack`; poteto-mode was loaded as a sibling from that installed cache. A short model-visible catalog does not mean the other installed skills were removed.

Cursor filters some files when creating its cache. The tested review path retains all required skills and runner files. Use the complete stable marketplace or source checkout for Benny installation and for Codex's optional Comment Sicko translation, which need assets omitted from the Cursor cache.

Cursor also documents `~/.cursor/plugins/local/hstack` symlinks for plugin development, but that discovery path did not expose hstack in the tested Agents UI after reload. Use the marketplace import above for this setup. On managed accounts, an admin may control local imports. See [Cursor plugins](https://cursor.com/docs/plugins) and [marketplace structure](https://cursor.com/docs/reference/plugins#cursor-multi-plugin-repositories).

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

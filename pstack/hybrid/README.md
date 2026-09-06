# hstack

hstack adapts Lauren Tan's MIT-licensed [pstack](https://github.com/cursor/plugins/tree/main/pstack) for Cursor and Codex CLI/desktop, with a subscription-authenticated Codex review/rescue runner. It is maintained in [huankoh/plugins](https://github.com/huankoh/plugins) and is not an official Cursor or OpenAI release.

Installable packages are published in [huankoh/hstack](https://github.com/huankoh/hstack). That repository puts the Cursor and Codex marketplace manifests on its default branch and records the source revision used for each publication. This fork remains the canonical source; [PR #1](https://github.com/huankoh/plugins/pull/1) shows the adaptation against upstream pstack.

The canonical upstream skills remain in `pstack/skills`; the adaptation source stays in `pstack/hybrid` to keep upstream comparisons clear. `build.py` generates separate `hstack` packages with runtime-specific entry instructions and metadata. It does not install anything. The 18 model roles stay separate from execution backend selection. Existing model settings are preserved.

## Start here

- [Setup overview](docs/setup.md): choose where each process runs.
- [Cursor and local Codex](docs/cursor-local.md): package build, installation and a review.
- [Codex CLI and desktop](docs/codex.md): use hstack directly in Codex.
- [Codex cloud](docs/codex-cloud.md): stage a pinned package and test native cloud workflows.
- [Grok Bot](docs/grok-bot.md): persistent VM setup and a reusable coordinator brief.
- [Cursor cloud VM](docs/cursor-cloud.md): preinstall the CLI, authenticate and collect results.
- [Verification record](docs/verification.md): tested behavior and live-host limitations.

## Architecture

Cursor retains native orchestration. The [hybrid policy](runtime/hybrid.md) defines checkpoints, review, repair and rescue. `runner.py` owns isolated Git worktrees, idempotent handoffs and artifact verification; `worker.py` owns CLI process supervision. The worker is adapted from the existing local Grok/Codex helper. It has no network listener or remote execution service.

```
Cursor implementation → checkpoint SHA → Codex read-only review → Cursor fixes
                                           ↓ repeat code blocker
Cursor stopped → checkpoint + diagnostics → Codex rescue → patch → Cursor review
```

These are coordinator-driven transitions, not an autonomous daemon. The runner enforces identity, checkout isolation and result checks. The coordinator must actually stop the previous writer and select the intended checkpoint. Direct Codex sessions use hstack's adapted pstack workflows without requiring Cursor.

A `succeeded` process can still have `verification: failed` or `blocked`. A review is acceptable only after `validate` confirms the reviewed SHA is still current. Rescue verification is not independent review.

## Build and test

Python 3.9+ is required on macOS/Linux. Only package building needs PyYAML; the runner uses the standard library.

```bash
python3 -m venv .venv
.venv/bin/pip install -r pstack/hybrid/requirements.txt
.venv/bin/python pstack/hybrid/build.py
.venv/bin/python -m unittest discover -s pstack/hybrid/tests -v
```

Outputs are under ignored `dist/hstack/{cursor,codex}`. Existing source and installed plugins are not modified. Each generated package includes a source revision and content fingerprint in `BUILD.json`.

## Updates

Keep `origin` pointing at your fork and `upstream` at `https://github.com/cursor/plugins.git`. After this adaptation is merged into your fork, run `pstack/hybrid/update-upstream.sh` from its clean checkout with the build environment active. It creates an update branch, merges upstream, runs Python checks and builds both packages. Resolve any merge conflicts there and run CI before opening a PR. It never pushes, merges a PR, or updates a live installation.

Retain the previous generated package directory and revision. Rollback means repointing the Cursor local import or reinstalling the preceding Codex package through the same marketplace flow. Always verify the displayed source/version after an update. Do not replace the maintained fork with a forced upstream sync.

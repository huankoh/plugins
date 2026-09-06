#!/usr/bin/env bash
# Run from a clone of huankoh/plugins. This creates a local review branch only.
set -euo pipefail
[[ -z "$(git status --porcelain)" ]] || { echo 'Commit or preserve local changes before updating' >&2; exit 1; }
[[ "$(git remote get-url upstream)" == 'https://github.com/cursor/plugins.git' ]] || { echo 'Expected cursor/plugins as upstream' >&2; exit 1; }
git fetch upstream main
git switch -c "update/pstack-upstream-$(date -u +%Y%m%d%H%M%S)"
git merge --no-edit upstream/main
python3 -m unittest discover -s pstack/hybrid/tests -v
python3 pstack/hybrid/build.py
printf '%s\n' 'Update prepared locally. Run the full CI checks and open a PR before changing any installed package.'

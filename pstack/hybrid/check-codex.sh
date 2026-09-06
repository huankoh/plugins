#!/usr/bin/env bash
set -euo pipefail
version="${PSTACK_CODEX_VERSION:-0.153.3}"
binary="${PSTACK_CODEX_BINARY:-${PSTACK_CODEX_PREFIX:-$HOME/.local/share/pstack-codex}/node_modules/.bin/codex}"
[[ -x "$binary" ]] || { echo "Codex executable missing: $binary" >&2; exit 1; }
actual="$("$binary" --version)"
[[ "$actual" == "codex-cli $version" ]] || { echo "Expected codex-cli $version; found $actual" >&2; exit 1; }
echo "$actual available; authentication is checked separately by runner.py doctor"

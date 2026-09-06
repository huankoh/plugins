#!/usr/bin/env bash
# Run after a Cursor VM boots. Never call this from an image Install step.
set -euo pipefail
hybrid_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
env -u HSTACK_CODEX_AUTH_JSON bash "$hybrid_dir/check-codex.sh"

if [[ -n "${HSTACK_CODEX_AUTH_JSON:-}" || -n "${HSTACK_CODEX_AUTH_HOME:-}" ]]; then
  python3 "$hybrid_dir/restore-codex-auth.py" \
    --auth-home "${HSTACK_CODEX_AUTH_HOME:-$HOME/.local/share/hstack-codex-auth}"
  python3 "$hybrid_dir/runner.py" doctor
fi

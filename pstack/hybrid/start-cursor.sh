#!/usr/bin/env bash
# Run after a Cursor VM boots. Never call this from an image Install step.
set -euo pipefail
hybrid_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skills_package=''
skills_only=false
hstack_python="${HSTACK_PYTHON:-python3}"
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --skills)
      if [[ "$#" -lt 2 || -z "$2" ]]; then
        echo '--skills requires a generated Cursor package directory.' >&2
        exit 2
      fi
      skills_package="$2"
      shift 2
      ;;
    --skills-only)
      skills_only=true
      shift
      ;;
    --python)
      if [[ "$#" -lt 2 || -z "$2" ]]; then
        echo '--python requires a Python executable with the hstack dependencies installed.' >&2
        exit 2
      fi
      hstack_python="$2"
      shift 2
      ;;
    --help)
      echo 'Usage: bash start-cursor.sh [--skills CURSOR_PACKAGE] [--skills-only] [--python PYTHON]'
      echo 'Activate hstack before Cursor scans skills; run from the connected repository when available.'
      echo '--skills-only activates skills without reading or restoring Codex authentication.'
      exit 0
      ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done
if [[ "$skills_only" = true && -z "$skills_package" ]]; then
  echo '--skills-only requires --skills CURSOR_PACKAGE.' >&2
  exit 2
fi
if [[ -n "$skills_package" ]]; then
  env -u HSTACK_CODEX_AUTH_JSON "$hstack_python" "$hybrid_dir/activate-cursor-skills.py" \
    --package "$skills_package"
fi
if [[ "$skills_only" = true ]]; then
  exit 0
fi
env -u HSTACK_CODEX_AUTH_JSON bash "$hybrid_dir/check-codex.sh"

if [[ -n "${HSTACK_CODEX_AUTH_JSON:-}" || -n "${HSTACK_CODEX_AUTH_HOME:-}" ]]; then
  "$hstack_python" "$hybrid_dir/restore-codex-auth.py" \
    --auth-home "${HSTACK_CODEX_AUTH_HOME:-$HOME/.local/share/hstack-codex-auth}"
  "$hstack_python" "$hybrid_dir/runner.py" doctor
fi

#!/usr/bin/env bash
# Install the CLI only. Never authenticate during an image build.
set -euo pipefail
version="${PSTACK_CODEX_VERSION:-0.153.3}"
prefix="${PSTACK_CODEX_PREFIX:-$HOME/.local/share/pstack-codex}"
if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo 'PSTACK_CODEX_VERSION must be an exact release version' >&2
  exit 2
fi
if [[ -x "$prefix/node_modules/.bin/codex" ]] && [[ "$("$prefix/node_modules/.bin/codex" --version)" == "codex-cli $version" ]]; then
  echo "Codex $version already installed at $prefix/node_modules/.bin/codex"
  exit 0
fi
command -v node >/dev/null || { echo 'Install Node.js 20+ before this script' >&2; exit 1; }
command -v npm >/dev/null || { echo 'Install npm before this script' >&2; exit 1; }
node -e 'if (Number(process.versions.node.split(".")[0]) < 20) process.exit(1)' || { echo 'Node.js 20+ required' >&2; exit 1; }
npm install --prefix "$prefix" --no-audit --no-fund "@openai/codex@$version"
[[ "$("$prefix/node_modules/.bin/codex" --version)" == "codex-cli $version" ]]
echo "Installed $prefix/node_modules/.bin/codex"

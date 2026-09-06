#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = --help ]; then
  echo 'Usage: bash setup-codex-cloud.sh FULL_COMMIT_SHA'
  echo 'Alternatively set HSTACK_SOURCE_SHA. No branch or implicit latest version is accepted.'
  exit 0
fi
if [ "$#" -gt 1 ]; then
  echo 'Expected one full Git commit SHA.' >&2
  exit 2
fi
HSTACK_SOURCE_SHA="${1:-${HSTACK_SOURCE_SHA:-}}"
if [[ ! "$HSTACK_SOURCE_SHA" =~ ^[0-9a-f]{40}$ ]]; then
  echo 'Provide the full 40-character lowercase commit SHA as an argument or HSTACK_SOURCE_SHA.' >&2
  exit 2
fi
HSTACK_CLOUD_ROOT="${HSTACK_CLOUD_ROOT:-$HOME/.local/share/hstack-codex-cloud}"
HSTACK_CLOUD_SKILLS="${HSTACK_CLOUD_SKILLS:-$HOME/.agents/skills}"
HSTACK_SOURCE_DIR="$HSTACK_CLOUD_ROOT/sources/$HSTACK_SOURCE_SHA"
HSTACK_BUILD_DIR="$HSTACK_CLOUD_ROOT/builds/$HSTACK_SOURCE_SHA"
HSTACK_PYTHON_DIR="$HSTACK_CLOUD_ROOT/python/$HSTACK_SOURCE_SHA"

command -v git >/dev/null
command -v python3 >/dev/null
python3 -c 'import sys; assert sys.version_info >= (3, 9), "Python 3.9+ is required"'
mkdir -p "$HSTACK_CLOUD_ROOT/sources"

if [ ! -d "$HSTACK_SOURCE_DIR/.git" ]; then
  if [ -e "$HSTACK_SOURCE_DIR" ]; then
    echo "Refusing to replace existing non-repository source: $HSTACK_SOURCE_DIR" >&2
    exit 1
  fi
  git init --quiet "$HSTACK_SOURCE_DIR"
  git -C "$HSTACK_SOURCE_DIR" remote add origin https://github.com/huankoh/plugins.git
fi
if [ "$(git -C "$HSTACK_SOURCE_DIR" remote get-url origin)" != https://github.com/huankoh/plugins.git ]; then
  echo 'Unexpected hstack source remote.' >&2
  exit 1
fi
if [ -n "$(git -C "$HSTACK_SOURCE_DIR" status --porcelain)" ]; then
  echo 'Refusing to replace a modified hstack source checkout.' >&2
  exit 1
fi
git -C "$HSTACK_SOURCE_DIR" fetch --quiet --depth 1 origin "$HSTACK_SOURCE_SHA"
git -C "$HSTACK_SOURCE_DIR" -c advice.detachedHead=false checkout --quiet --detach "$HSTACK_SOURCE_SHA"
test "$(git -C "$HSTACK_SOURCE_DIR" rev-parse HEAD)" = "$HSTACK_SOURCE_SHA"

python3 -m venv "$HSTACK_PYTHON_DIR"
"$HSTACK_PYTHON_DIR/bin/python" -m pip install --disable-pip-version-check -r "$HSTACK_SOURCE_DIR/pstack/hybrid/requirements.txt"
"$HSTACK_PYTHON_DIR/bin/python" "$HSTACK_SOURCE_DIR/pstack/hybrid/build.py" --output "$HSTACK_BUILD_DIR"

"$HSTACK_PYTHON_DIR/bin/python" - "$HSTACK_CLOUD_ROOT" "$HSTACK_SOURCE_DIR" "$HSTACK_BUILD_DIR" "$HSTACK_CLOUD_SKILLS" "$HSTACK_SOURCE_SHA" <<'PY'
import json
from pathlib import Path
import sys

root, source, output, discovery = map(Path, sys.argv[1:5])
revision = sys.argv[5]
package = (output / 'codex/plugins/hstack').resolve()
skills = package / 'skills'
build = json.loads((package / 'BUILD.json').read_text())
if build['source_revision'] != revision:
    raise SystemExit('Package revision does not match the requested commit.')
expected = {path.parent.name for path in (source / 'pstack/skills').glob('*/SKILL.md')}
actual = {path.parent.name for path in skills.glob('*/SKILL.md')}
if not expected or actual != expected:
    raise SystemExit('Generated skills do not match the selected source.')
for relative in ('hybrid/runtime/codex.md', 'config/default-models.json',
                 'references/codex-runtime.md', '.codex-plugin/plugin.json'):
    if not (package / relative).is_file():
        raise SystemExit(f'Generated package is missing {relative}.')

link = discovery / 'hstack'
link.parent.mkdir(parents=True, exist_ok=True)
if link.is_symlink():
    if link.resolve() != skills:
        raise SystemExit(f'Refusing to replace a different existing skill link: {link}')
elif link.exists():
    raise SystemExit(f'Refusing to replace an existing skill directory: {link}')
else:
    link.symlink_to(skills, target_is_directory=True)

record = {
    'source_revision': revision,
    'source_sha256': build['source_sha256'],
    'package': str(package),
    'skill_discovery_path': str(link.absolute()),
    'resolved_skills_path': str(skills),
    'skill_count': len(actual),
    'discovery_method': 'staged .agents/skills symlink; verify in the actual cloud task',
    'plugin_registration': 'not attempted',
    'codex_cli_authentication': 'not used for direct Codex cloud',
}
(root / 'setup.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
PY

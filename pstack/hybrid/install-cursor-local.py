#!/usr/bin/env python3
"""Publish a generated Cursor marketplace to a stable local Git repository."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

MARKER = '.hstack-cursor-marketplace'
MARKER_TEXT = 'Managed by hstack install-cursor-local.py v1\n'


def git(directory, *args):
    return subprocess.check_output(['git', '-C', str(directory), '-c', 'core.hooksPath=/dev/null',
        *args], stderr=subprocess.PIPE, text=True).strip()


def install(source, destination):
    source = Path(source).expanduser().resolve()
    destination = Path(destination).expanduser().resolve()
    if source == destination or source.is_relative_to(destination) or destination.is_relative_to(source):
        raise ValueError('Source and destination must be separate directories')
    manifest = json.loads((source / '.cursor-plugin/marketplace.json').read_text())
    entries = manifest.get('plugins', [])
    if manifest.get('name') != 'hstack' or len(entries) != 1 or entries[0].get('name') != 'hstack':
        raise ValueError('Expected the generated hstack Cursor marketplace')
    if entries[0].get('source') != './plugins/hstack' or not (source / 'plugins/hstack/.cursor-plugin/plugin.json').is_file():
        raise ValueError('Marketplace must reference ./plugins/hstack with a plugin manifest')
    if destination.exists():
        marker = destination / MARKER
        if not marker.is_file() or marker.read_text() != MARKER_TEXT or not (destination / '.git').is_dir():
            raise ValueError('Refusing to replace an unrecognized destination')
        if Path(git(destination, 'rev-parse', '--show-toplevel')).resolve() != destination:
            raise ValueError('Destination must be its own Git repository')
        if git(destination, 'status', '--porcelain', '--untracked-files=all', '--ignored'):
            raise ValueError('Destination has local changes; preserve or resolve them before updating')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.hstack-cursor-stage-', dir=destination.parent) as directory:
        staging = Path(directory)
        # Complete both copies before touching the installed repository. A bad
        # source can then be fixed and retried without leaving a dirty install.
        for name in ('.cursor-plugin', 'plugins'):
            shutil.copytree(source / name, staging / name)
        if not destination.exists():
            destination.mkdir()
            git(destination, 'init', '--quiet', '--initial-branch=main')
            (destination / MARKER).write_text(MARKER_TEXT)
        for name in ('.cursor-plugin', 'plugins'):
            target = destination / name
            if target.exists():
                shutil.rmtree(target)
            (staging / name).replace(target)
    git(destination, 'add', '--force', '--all', '--', MARKER, '.cursor-plugin', 'plugins')
    changed = bool(git(destination, 'diff', '--cached', '--name-only'))
    if changed:
        git(destination, '-c', 'user.name=hstack', '-c', 'user.email=hstack@local.invalid',
            'commit', '--quiet', '--no-gpg-sign', '-m', 'Update hstack Cursor marketplace')
    return {'path': str(destination), 'commit': git(destination, 'rev-parse', 'HEAD'),
            'status': 'updated' if changed else 'unchanged'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Generated marketplace root: dist/hstack/cursor')
    parser.add_argument('--destination', type=Path, default=Path('~/.local/share/hstack-cursor-marketplace'))
    args = parser.parse_args()
    try:
        print(json.dumps(install(args.source, args.destination), indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python3
"""Activate portable hstack skills in the current Cursor project or personal scope."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

spec = importlib.util.spec_from_file_location(
    'hstack_cursor_skills', Path(__file__).with_name('install-cursor-skills.py'))
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

BEGIN = '# BEGIN hstack Cursor skills (managed)'
END = '# END hstack Cursor skills (managed)'


def git(directory, *args):
    return subprocess.run(['git', '-C', str(directory), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()


def exclusion_text(original, names):
    lines = original.splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines) if line.rstrip('\r\n') == BEGIN]
    ends = [index for index, line in enumerate(lines) if line.rstrip('\r\n') == END]
    block = '\n'.join([BEGIN] + ['/.cursor/skills/' + name + '/' for name in sorted(names)] + [END]) + '\n'
    if not starts and not ends:
        return original + ('\n' if original and not original.endswith('\n') else '') + block
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        raise ValueError('Malformed managed hstack block in Git info/exclude; preserve and repair it first')
    return ''.join(lines[:starts[0]]) + block + ''.join(lines[ends[0] + 1:])


def activate(package, directory=None, personal_directory=None):
    # Validate the requested package even outside Git. Invalid hstack must never
    # cause a successful-looking fallback to an unrelated workflow.
    source = installer.plugin_root(package)
    names = {path.parent.name for path in (source / 'skills').glob('*/SKILL.md')}
    if installer.ENTRYPOINT not in names or any(
            not re.fullmatch(r'hstack-[a-z0-9]+(?:-[a-z0-9]+)*', name) for name in names):
        raise ValueError('Expected a Cursor package with unique hstack-prefixed skills')
    directory = Path(directory if directory is not None else Path.cwd()).expanduser().resolve()
    if not directory.is_dir():
        raise ValueError(f'Cursor working directory does not exist: {directory}')
    try:
        project = Path(git(directory, 'rev-parse', '--show-toplevel')).resolve()
    except subprocess.CalledProcessError:
        project = None
    exclude = None
    if project is not None:
        destination = project / '.cursor/skills'
        if (project / '.cursor').is_symlink() or destination.is_symlink():
            raise ValueError('Refusing a symlinked project Cursor skills destination')
        existing = {path.name for path in destination.glob('hstack-*') if installer.recognized_marker(path)}
        tracked = git(project, 'ls-files', '--',
                      *['.cursor/skills/' + name for name in sorted(names | existing)])
        if tracked:
            raise ValueError('Refusing to replace tracked project hstack skills')
        exclude = Path(git(project, 'rev-parse', '--git-path', 'info/exclude'))
        if not exclude.is_absolute():
            exclude = project / exclude
        original = exclude.read_text() if exclude.exists() else ''
        updated = exclusion_text(original, names)
    else:
        destination = Path(personal_directory if personal_directory is not None else '~/.cursor/skills')
    result = installer.install(source, destination)
    if exclude is not None:
        exclude.parent.mkdir(parents=True, exist_ok=True)
        if updated != original:
            exclude.write_text(updated)
    result['scope'] = 'project' if project is not None else 'personal'
    if project is not None:
        result['project'] = str(project)
        result['git_exclude'] = str(exclude.resolve())
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True,
                        help='Generated Cursor marketplace or plugins/hstack directory')
    parser.add_argument('--directory', type=Path, default=Path.cwd(),
                        help='Cursor working directory; defaults to the current directory')
    args = parser.parse_args()
    try:
        print(json.dumps(activate(args.package, args.directory), indent=2))
    except (OSError, ValueError, subprocess.SubprocessError, installer.yaml.YAMLError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        sys.exit(1)

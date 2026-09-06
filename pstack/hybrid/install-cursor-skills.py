#!/usr/bin/env python3
"""Export hstack as portable personal or project Cursor skills."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

import yaml

ENTRYPOINT = 'hstack-poteto-mode'
PAYLOAD = Path(ENTRYPOINT) / 'references/hstack-package'
MARKER = '.hstack-skill-export.json'
OWNER = 'hstack/install-cursor-skills/v1'
FRONTMATTER = re.compile(r'^---\n(.*?)\n---\n', re.S)


def inventory(directory):
    """Fingerprint every managed path, including otherwise empty directories."""
    result = {}
    for path in sorted(directory.rglob('*')):
        relative = path.relative_to(directory).as_posix()
        if relative == MARKER:
            continue
        if path.is_symlink():
            raise ValueError(f'Symlinks are not supported in skill exports: {path}')
        if path.is_dir():
            result[relative] = 'directory'
        elif path.is_file():
            result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            raise ValueError(f'Unsupported file in skill export: {path}')
    return result


def plugin_root(source):
    source = Path(source).expanduser().resolve()
    if (source / '.cursor-plugin/marketplace.json').is_file():
        source = source / 'plugins/hstack'
    manifest = json.loads((source / '.cursor-plugin/plugin.json').read_text())
    build = json.loads((source / 'BUILD.json').read_text())
    if manifest.get('name') != 'hstack' or build.get('runtime') != 'cursor':
        raise ValueError('Expected a generated hstack Cursor package')
    inventory(source)  # Do not dereference links into files outside the package.
    return source


def workflow_references(text, path, payload, renamed):
    """Rewrite only paths to bundled workflows, preserving authoring destinations."""
    def replacement(match):
        candidate = match[0]
        targets = ((path.parent / candidate).resolve(), (payload / candidate).resolve())
        if any(target in renamed for target in targets):
            return candidate[:-len('SKILL.md')] + 'WORKFLOW.md'
        return candidate

    parts = re.split(r'(https?://[^\s<>`]+)', text)
    for index in range(0, len(parts), 2):
        parts[index] = re.sub(r'(?:[\w.@~$\{\}*<>-]+/)+SKILL\.md\b',
                              replacement, parts[index])
    return ''.join(parts)


def stage_export(source, staging):
    skills = sorted((source / 'skills').glob('*/SKILL.md'))
    names = {skill.parent.name for skill in skills}
    if ENTRYPOINT not in names or not names or any(
            not re.fullmatch(r'hstack-[a-z0-9]+(?:-[a-z0-9]+)*', name) for name in names):
        raise ValueError('Build a Cursor package with unique hstack-prefixed skill names first')
    payload = staging / PAYLOAD
    shutil.copytree(source, payload)
    # Cursor recursively discovers SKILL.md, even below references/. Auxiliary
    # automation workflows must therefore be renamed along with public skills.
    renamed = {workflow.resolve() for workflow in payload.rglob('SKILL.md')}
    for workflow in sorted(renamed):
        target = workflow.with_name('WORKFLOW.md')
        if target.exists():
            raise ValueError(f'Workflow export would replace an existing file: {target}')
        workflow.rename(target)
    references = list(payload.rglob('*.md'))
    if (payload / 'SKILL-MAP.json').is_file():
        references.append(payload / 'SKILL-MAP.json')
    for path in references:
        original = path.read_text()
        rewritten = workflow_references(original, path, payload, renamed)
        if rewritten != original:
            path.write_text(rewritten)
    for skill in skills:
        match = FRONTMATTER.match(skill.read_text())
        if not match:
            raise ValueError(f'Missing skill frontmatter: {skill}')
        metadata = yaml.safe_load(match[1])
        name = skill.parent.name
        if not isinstance(metadata, dict) or metadata.get('name') != name or not metadata.get('description'):
            raise ValueError(f'Skill metadata must match its unique folder name: {skill}')
        wrapper = staging / name
        wrapper.mkdir(exist_ok=True)
        prefix = 'references/hstack-package' if name == ENTRYPOINT else '../' + PAYLOAD.as_posix()
        target = f'{prefix}/skills/{name}/WORKFLOW.md'
        # Preserve all upstream Cursor metadata, including explicit invocation.
        body = (f'# {name}\n\n'
                f'Read [the bundled hstack workflow]({target}) in full and follow it. '
                'Its runtime adapter governs Cursor implementation and Codex review.\n\n'
                'Resolve relative references from the bundled file containing them. '
                'The package uses WORKFLOW.md for its bundled workflows so Cursor '
                'discovers each public skill only once. References in that package '
                'to reading a sibling skill mean its WORKFLOW.md in this same package. '
                'Keep skill-authoring output named SKILL.md.\n\n'
                'Use this hstack package throughout the task. If a dependency is missing, '
                'report the missing file; do not substitute a pstack workflow.\n')
        (wrapper / 'SKILL.md').write_text('---\n' + match[1] + '\n---\n\n' + body)
    for name in sorted(names):
        marker = {'owner': OWNER, 'skill': name, 'files': inventory(staging / name)}
        (staging / name / MARKER).write_text(json.dumps(marker, sort_keys=True, indent=2) + '\n')
    return names


def recognized_marker(directory):
    marker = directory / MARKER
    if directory.is_symlink() or not marker.is_file() or marker.is_symlink():
        return None
    try:
        data = json.loads(marker.read_text())
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get('owner') != OWNER or data.get('skill') != directory.name:
        return None
    return data


def install(source, destination=Path('~/.cursor/skills')):
    source = plugin_root(source)
    destination = Path(destination).expanduser().resolve()
    if source == destination or source.is_relative_to(destination) or destination.is_relative_to(source):
        raise ValueError('Source and destination must be separate directories')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.hstack-skills-stage-', dir=destination.parent) as directory:
        temporary = Path(directory)
        staging = temporary / 'skills'
        names = stage_export(source, staging)
        existing = {path.name: path for path in destination.glob('hstack-*')
                    if recognized_marker(path)}
        for name in names:
            path = destination / name
            if (path.exists() or path.is_symlink()) and name not in existing:
                raise ValueError(f'Refusing to replace an unrecognized skill: {path}')
        for name, path in existing.items():
            if inventory(path) != recognized_marker(path).get('files'):
                raise ValueError(f'Skill has local changes; preserve them before updating: {path}')
        if set(existing) == names and all(
                (existing[name] / MARKER).read_bytes() == (staging / name / MARKER).read_bytes()
                for name in names):
            return {'path': str(destination), 'skills': len(names), 'status': 'unchanged',
                    'entrypoint': '/' + ENTRYPOINT}
        destination.mkdir(parents=True, exist_ok=True)
        backup = temporary / 'backup'
        backup.mkdir()
        moved = []
        published = []
        try:
            for name in sorted(existing):
                existing[name].rename(backup / name)
                moved.append(name)
            for name in sorted(names):
                (staging / name).rename(destination / name)
                published.append(name)
        except OSError:
            for name in published:
                shutil.rmtree(destination / name)
            for name in moved:
                (backup / name).rename(destination / name)
            raise
    return {'path': str(destination), 'skills': len(names), 'status': 'updated',
            'entrypoint': '/' + ENTRYPOINT}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Generated Cursor marketplace or plugins/hstack directory')
    parser.add_argument('--destination', type=Path, default=Path('~/.cursor/skills'),
                        help='Personal skill directory, or <project>/.cursor/skills')
    args = parser.parse_args()
    try:
        print(json.dumps(install(args.source, args.destination), indent=2))
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        sys.exit(1)

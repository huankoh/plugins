import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

import yaml

HYBRID = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hstack_build', HYBRID / 'build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class BuildTests(unittest.TestCase):
    def test_packages_preserve_skills_and_runtime_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'packages'
            result = builder.build(output)
            again = builder.build(output)
            self.assertEqual(result, again)
            original = {p.parent.name for p in (builder.SOURCE / 'skills').glob('*/SKILL.md')}
            namespaced = {'hstack-' + name for name in original}
            self.assertEqual(len(original), 45)
            for runtime in ('cursor', 'codex'):
                target = output / runtime / 'plugins/hstack'
                self.assertEqual({p.parent.name for p in (target / 'skills').glob('*/SKILL.md')}, namespaced)
                self.assertFalse(namespaced & original)
                for skill in (target / 'skills').glob('*/SKILL.md'):
                    self.assertEqual(yaml.safe_load(skill.read_text().split('---')[1])['name'], skill.parent.name)
                mapping = json.loads((target / 'SKILL-MAP.json').read_text())
                self.assertEqual(set(mapping['skills']), original)
                for path in list(mapping['skills'].values()) + list(mapping['agents'].values()):
                    self.assertTrue((target / path).is_file(), path)
                self.assertEqual({p.stem for p in (target / 'agents').glob('*.md')},
                                 {'hstack-poteto-agent', 'hstack-comment-sicko'})
                self.assertTrue((target / 'hybrid/runner.py').exists())
                self.assertTrue((target / 'LICENSE').exists())
            marketplace_path = output / 'cursor/.cursor-plugin/marketplace.json'
            marketplace = json.loads(marketplace_path.read_text())
            self.assertEqual(marketplace['name'], 'hstack')
            self.assertEqual(marketplace['owner']['name'], 'huankoh')
            self.assertEqual(len(marketplace['plugins']), 1)
            entry = marketplace['plugins'][0]
            self.assertEqual(entry['source'], './plugins/hstack')
            plugin_root = (marketplace_path.parent.parent / entry['source']).resolve()
            self.assertEqual(plugin_root, (output / 'cursor/plugins/hstack').resolve())
            manifest = json.loads((plugin_root / '.cursor-plugin/plugin.json').read_text())
            self.assertEqual(entry['name'], manifest['name'])
            self.assertEqual(entry['name'], 'hstack')
            cursor = output / 'cursor/plugins/hstack/skills/hstack-poteto-mode/SKILL.md'
            codex = output / 'codex/plugins/hstack/skills/hstack-poteto-mode/SKILL.md'
            self.assertTrue(yaml.safe_load(cursor.read_text().split('---')[1])['disable-model-invocation'])
            self.assertNotIn('disable-model-invocation', codex.read_text().split('---')[1])
            policy = yaml.safe_load((codex.parent / 'agents/openai.yaml').read_text())
            self.assertTrue(policy['policy']['allow_implicit_invocation'])
            implicit = set()
            for skill in (codex.parent.parent).glob('*/SKILL.md'):
                settings = skill.parent / 'agents/openai.yaml'
                metadata = yaml.safe_load(settings.read_text()) if settings.exists() else {}
                if metadata.get('policy', {}).get('allow_implicit_invocation', True):
                    implicit.add(skill.parent.name)
            self.assertEqual(implicit, {'hstack-poteto-mode', 'hstack-setup-pstack'})
            codex_manifest = json.loads((output / 'codex/plugins/hstack/.codex-plugin/plugin.json').read_text())
            self.assertEqual(codex_manifest['interface']['defaultPrompt'],
                             ['Use $hstack-poteto-mode for this engineering task.'])
            defaults = json.loads((output / 'codex/plugins/hstack/config/default-models.json').read_text())
            self.assertEqual(len(defaults['roles']), 18)
            self.assertEqual(defaults['default'], 'inherit-parent')
            # Cursor's setup remains native; Codex receives its own template.
            self.assertIn('~/.cursor/rules/pstack-models.mdc', (output / 'cursor/plugins/hstack/skills/hstack-setup-pstack/SKILL.md').read_text())
            self.assertIn('~/.codex/pstack-models.json', (output / 'codex/plugins/hstack/skills/hstack-setup-pstack/SKILL.md').read_text())
            for runtime in ('cursor', 'codex'):
                package = output / runtime / 'plugins/hstack'
                pages = list((package / 'skills').glob('*/SKILL.md'))
                pages += [package / 'hybrid/runtime' / (runtime + '.md')]
                for page in pages:
                    for address in re.findall(r'\]\(([^\s)]+)\)', page.read_text()):
                        if 'hybrid/runtime/' in address or address.endswith('SKILL-MAP.json'):
                            self.assertTrue((page.parent / address).resolve().is_file(), (page, address))

    def test_namespacing_resolves_nested_links_and_preserves_source_urls(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory)
            paths = {
                'skills/poteto-mode/SKILL.md': '[How](../how/SKILL.md) /how $poteto-mode `how`',
                'skills/poteto-mode/references/guide.md': '[How](../../how/SKILL.md#evidence)\n'
                    '[Source](https://github.com/cursor/plugins/blob/main/pstack/skills/how/SKILL.md)\n'
                    'Run `poteto-agent`; inspect pstack/skills/how/SKILL.md for source evidence.',
                'skills/how/SKILL.md': '[Return](../poteto-mode/SKILL.md)',
                'agents/poteto-agent.md': '---\nname: poteto-agent\ndescription: Uses /poteto-mode\n---\n'
                    'Read [mode](../skills/poteto-mode/SKILL.md).',
            }
            for name, contents in paths.items():
                path = package / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(contents)
            builder.namespace_package(package)
            entry = package / 'skills/hstack-poteto-mode/SKILL.md'
            guide = package / 'skills/hstack-poteto-mode/references/guide.md'
            self.assertIn('/hstack-how $hstack-poteto-mode `hstack-how`', entry.read_text())
            self.assertIn('https://github.com/cursor/plugins/blob/main/pstack/skills/how/SKILL.md', guide.read_text())
            self.assertIn('pstack/skills/how/SKILL.md for source evidence', guide.read_text())
            self.assertIn('`hstack-poteto-agent`', guide.read_text())
            for path in package.rglob('*.md'):
                for address in re.findall(r'\]\(([^\s)]+)\)', path.read_text()):
                    if not address.startswith('https://'):
                        self.assertTrue((path.parent / address.split('#')[0]).resolve().is_file(), (path, address))
            self.assertFalse((package / 'skills/poteto-mode').exists())
            self.assertFalse((package / 'agents/poteto-agent.md').exists())

    def test_build_refuses_source_and_unmarked_directories(self):
        with self.assertRaises(ValueError):
            builder.build(HYBRID / 'accidental-output')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / 'user-file').write_text('keep')
            with self.assertRaises(ValueError):
                builder.build(path)
            self.assertEqual((path / 'user-file').read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()

import importlib.util
import json
from pathlib import Path
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
            self.assertEqual(len(original), 45)
            for runtime in ('cursor', 'codex'):
                target = output / runtime / 'plugins/hstack'
                self.assertEqual({p.parent.name for p in (target / 'skills').glob('*/SKILL.md')}, original)
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
            cursor = output / 'cursor/plugins/hstack/skills/poteto-mode/SKILL.md'
            codex = output / 'codex/plugins/hstack/skills/poteto-mode/SKILL.md'
            self.assertIn('disable-model-invocation', cursor.read_text().split('---')[1])
            self.assertNotIn('disable-model-invocation', codex.read_text().split('---')[1])
            policy = yaml.safe_load((codex.parent / 'agents/openai.yaml').read_text())
            self.assertFalse(policy['policy']['allow_implicit_invocation'])
            defaults = json.loads((output / 'codex/plugins/hstack/config/default-models.json').read_text())
            self.assertEqual(len(defaults['roles']), 18)
            self.assertEqual(defaults['default'], 'inherit-parent')
            # Cursor's setup remains native; Codex receives its own template.
            self.assertIn('~/.cursor/rules/pstack-models.mdc', (output / 'cursor/plugins/hstack/skills/setup-pstack/SKILL.md').read_text())
            self.assertIn('~/.codex/pstack-models.json', (output / 'codex/plugins/hstack/skills/setup-pstack/SKILL.md').read_text())

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

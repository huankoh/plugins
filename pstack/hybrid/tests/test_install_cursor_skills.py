import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest import mock

import yaml

HYBRID = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HYBRID / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load('hstack_cursor_skills', 'install-cursor-skills.py')
builder = load('hstack_build_for_export', 'build.py')


class CursorSkillExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        builder.build(self.root / 'packages')
        self.source = self.root / 'packages/cursor/plugins/hstack'
        self.destination = self.root / 'personal-skills'
        self.payload = self.destination / 'hstack-poteto-mode/references/hstack-package'

    def test_portable_export_resolves_every_wrapper_and_runtime_dependency(self):
        result = installer.install(self.source, self.destination)
        original = sorted((self.source / 'skills').glob('*/SKILL.md'))
        discovered = sorted(self.destination.rglob('SKILL.md'))
        self.assertEqual(result['skills'], 45)
        self.assertEqual(len(discovered), len(original))
        self.assertEqual({path.parent.name for path in discovered}, {path.parent.name for path in original})
        for source_skill in original:
            wrapper = self.destination / source_skill.parent.name / 'SKILL.md'
            metadata = yaml.safe_load(wrapper.read_text().split('---')[1])
            self.assertEqual(metadata, yaml.safe_load(source_skill.read_text().split('---')[1]))
            self.assertEqual(metadata['name'], wrapper.parent.name)
            links = re.findall(r'\]\(([^)]+)\)', wrapper.read_text())
            self.assertEqual(len(links), 1)
            workflow = (wrapper.parent / links[0]).resolve()
            self.assertTrue(workflow.is_relative_to(self.payload))
            self.assertEqual(workflow.name, 'WORKFLOW.md')
            self.assertTrue(workflow.is_file())
            adapter = re.search(r'\[the cursor runtime adapter\]\(([^)]+)\)', workflow.read_text())
            self.assertIsNotNone(adapter)
            self.assertTrue((workflow.parent / adapter[1]).resolve().is_file())
        mapping = json.loads((self.payload / 'SKILL-MAP.json').read_text())
        for category in ('skills', 'agents'):
            for relative in mapping[category].values():
                self.assertTrue((self.payload / relative).is_file(), relative)
        # The runtime, scripts, assets, references, and README travel with sync.
        for path in self.source.rglob('*'):
            if path.is_file():
                relative = path.relative_to(self.source)
                if path.name == 'SKILL.md':
                    relative = relative.with_name('WORKFLOW.md')
                self.assertTrue((self.payload / relative).is_file(), str(relative))
                if path.suffix not in ('.md', '.json'):
                    self.assertEqual((self.payload / relative).read_bytes(), path.read_bytes())

    def test_local_workflow_links_are_rewritten_but_web_sources_are_preserved(self):
        source = self.source / 'skills/hstack-poteto-mode/SKILL.md'
        with source.open('a') as stream:
            stream.write('\n[local](../hstack-how/SKILL.md#example)\n'
                         '[upstream](https://github.com/cursor/plugins/blob/main/pstack/skills/how/SKILL.md)\n'
                         'When authoring a skill, create SKILL.md.\n'
                         'Write the output to .cursor/skills/example/SKILL.md.\n')
        installer.install(self.source, self.destination)
        workflow = self.payload / 'skills/hstack-poteto-mode/WORKFLOW.md'
        text = workflow.read_text()
        link = re.search(r'\[local\]\(([^#]+)#', text)[1]
        self.assertTrue((workflow.parent / link).resolve().is_file())
        self.assertIn('https://github.com/cursor/plugins/blob/main/pstack/skills/how/SKILL.md', text)
        self.assertIn('When authoring a skill, create SKILL.md.', text)
        self.assertIn('.cursor/skills/example/SKILL.md', text)
        verification = self.payload / 'skills/hstack-create-verification-skill/WORKFLOW.md'
        self.assertIn('.cursor/skills/verify-<app>/SKILL.md', verification.read_text())

    def test_repeat_update_and_retirement_preserve_unrelated_skills(self):
        pstack = self.destination / 'poteto-mode/SKILL.md'
        personal = self.destination / 'hstack-my-own-skill/SKILL.md'
        for path in (pstack, personal):
            path.parent.mkdir(parents=True)
            path.write_text('personal work to keep\n')
        installer.install(self.source.parent.parent, self.destination)
        original = installer.inventory(self.destination)
        self.assertEqual(installer.install(self.source, self.destination)['status'], 'unchanged')
        self.assertEqual(original, installer.inventory(self.destination))
        (self.source / 'README.md').write_text('updated package documentation\n')
        self.assertEqual(installer.install(self.source, self.destination)['status'], 'updated')
        self.assertEqual((self.payload / 'README.md').read_text(), 'updated package documentation\n')
        # A retired generated workflow must not remain in the slash catalog.
        (self.source / 'skills/hstack-how/SKILL.md').unlink()
        installer.install(self.source, self.destination)
        self.assertFalse((self.destination / 'hstack-how').exists())
        for path in (pstack, personal):
            self.assertEqual(path.read_text(), 'personal work to keep\n')

    def test_refuses_unrecognized_or_modified_export_before_changing_any_skill(self):
        occupied = self.destination / 'hstack-how/SKILL.md'
        occupied.parent.mkdir(parents=True)
        occupied.write_text('existing unowned workflow\n')
        before = installer.inventory(self.destination)
        with self.assertRaisesRegex(ValueError, 'unrecognized'):
            installer.install(self.source, self.destination)
        self.assertEqual(before, installer.inventory(self.destination))
        occupied.unlink()
        occupied.parent.rmdir()
        installer.install(self.source, self.destination)
        (self.payload / 'README.md').write_text('keep my local edit\n')
        before = installer.inventory(self.destination)
        with self.assertRaisesRegex(ValueError, 'local changes'):
            installer.install(self.source, self.destination)
        self.assertEqual(before, installer.inventory(self.destination))

    def test_invalid_source_and_external_symlinks_preserve_existing_install(self):
        installer.install(self.source, self.destination)
        before = installer.inventory(self.destination)
        skill = self.source / 'skills/hstack-how/SKILL.md'
        valid = skill.read_text()
        skill.write_text('invalid source without metadata\n')
        with self.assertRaisesRegex(ValueError, 'frontmatter'):
            installer.install(self.source, self.destination)
        self.assertEqual(before, installer.inventory(self.destination))
        skill.write_text(valid)
        private = self.root / 'outside.txt'
        private.write_text('do not copy\n')
        (self.source / 'outside').symlink_to(private)
        with self.assertRaisesRegex(ValueError, 'Symlinks'):
            installer.install(self.source, self.destination)
        self.assertEqual(before, installer.inventory(self.destination))
        self.assertFalse((self.payload / 'outside').exists())

    def test_failed_publication_restores_previous_complete_export(self):
        installer.install(self.source, self.destination)
        before = installer.inventory(self.destination)
        (self.source / 'README.md').write_text('new package\n')
        rename = Path.rename

        def fail_second_skill(path, target):
            if path.parent.name == 'skills' and path.name == 'hstack-blast-radius':
                raise OSError('simulated publication failure')
            return rename(path, target)

        with mock.patch.object(Path, 'rename', fail_second_skill):
            with self.assertRaisesRegex(OSError, 'publication failure'):
                installer.install(self.source, self.destination)
        self.assertEqual(before, installer.inventory(self.destination))
        self.assertEqual(installer.install(self.source, self.destination)['status'], 'updated')


if __name__ == '__main__':
    unittest.main()

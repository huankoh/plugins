import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HYBRID = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hstack_cursor_activate', HYBRID / 'activate-cursor-skills.py')
activation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(activation)


class CursorActivationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.package = self.root / 'package'
        (self.package / '.cursor-plugin').mkdir(parents=True)
        (self.package / '.cursor-plugin/plugin.json').write_text('{"name":"hstack"}')
        (self.package / 'BUILD.json').write_text('{"runtime":"cursor"}')
        for name in ('hstack-poteto-mode', 'hstack-how'):
            skill = self.package / 'skills' / name / 'SKILL.md'
            skill.parent.mkdir(parents=True)
            skill.write_text(f'---\nname: {name}\ndescription: Test workflow\n---\n\nRead the task.\n')
        self.project = self.root / 'project'
        self.project.mkdir()
        activation.git(self.project, 'init', '--quiet')
        self.personal = self.root / 'personal-skills'

    def activate(self, directory=None):
        return activation.activate(self.package, directory or self.project, self.personal)

    def test_project_discovery_is_idempotent_clean_and_preserves_unrelated_files(self):
        nested = self.project / 'src'
        nested.mkdir()
        exclude = self.project / '.git/info/exclude'
        exclude.write_text('# personal exclusions\nlocal-cache/\n')
        original = self.project / '.cursor/skills/poteto-mode/SKILL.md'
        original.parent.mkdir(parents=True)
        original.write_text('original pstack skill\n')
        activation.git(self.project, 'add', '.cursor')
        activation.git(self.project, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                       'commit', '--quiet', '-m', 'Existing personal skills')
        first = self.activate(nested)
        self.assertEqual(first['scope'], 'project')
        self.assertEqual(first['path'], str(self.project / '.cursor/skills'))
        expected_exclude = exclude.read_text()
        self.assertTrue(expected_exclude.startswith('# personal exclusions\nlocal-cache/\n'))
        self.assertIn('/.cursor/skills/hstack-poteto-mode/\n', expected_exclude)
        self.assertNotIn('/.cursor/skills/\n', expected_exclude)
        self.assertEqual(activation.git(self.project, 'status', '--porcelain'), '')
        second = self.activate()
        self.assertEqual(second['status'], 'unchanged')
        self.assertEqual(exclude.read_text(), expected_exclude)
        self.assertEqual(original.read_text(), 'original pstack skill\n')
        unrelated = self.project / '.cursor/skills/my-new-skill/SKILL.md'
        unrelated.parent.mkdir()
        unrelated.write_text('my workflow\n')
        self.assertIn('my-new-skill', activation.git(self.project, 'status', '--porcelain', '--untracked-files=all'))

    def test_non_repository_uses_personal_scope_and_invalid_package_fails(self):
        result = self.activate(self.root)
        self.assertEqual(result['scope'], 'personal')
        self.assertEqual(result['path'], str(self.personal))
        (self.package / '.cursor-plugin/plugin.json').write_text('{"name":"pstack"}')
        with self.assertRaisesRegex(ValueError, 'hstack Cursor package'):
            self.activate(self.root)

    def test_preserves_exclude_and_files_when_managed_skill_has_local_changes(self):
        self.activate()
        exclude = self.project / '.git/info/exclude'
        before = exclude.read_text()
        skill = self.project / '.cursor/skills/hstack-how/SKILL.md'
        skill.write_text('keep my changes\n')
        with self.assertRaisesRegex(ValueError, 'local changes'):
            self.activate()
        self.assertEqual(skill.read_text(), 'keep my changes\n')
        self.assertEqual(exclude.read_text(), before)

    def test_malformed_exclude_tracked_skills_and_symlink_fail_before_install(self):
        exclude = self.project / '.git/info/exclude'
        exclude.write_text(activation.BEGIN + '\nkeep this\n')
        with self.assertRaisesRegex(ValueError, 'Malformed'):
            self.activate()
        self.assertFalse((self.project / '.cursor/skills').exists())
        exclude.write_text('keep this\n')
        owned = self.project / '.cursor/skills/hstack-how/SKILL.md'
        owned.parent.mkdir(parents=True)
        owned.write_text('tracked workflow\n')
        activation.git(self.project, 'add', '.cursor')
        with self.assertRaisesRegex(ValueError, 'tracked'):
            self.activate()
        self.assertEqual(owned.read_text(), 'tracked workflow\n')
        other = self.root / 'other-project'
        other.mkdir()
        activation.git(other, 'init', '--quiet')
        (other / '.cursor').symlink_to(self.project / '.cursor', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlinked'):
            self.activate(other)

    def test_skills_only_boot_activates_without_codex_or_authentication(self):
        auth_home = self.root / 'private-auth'
        environment = dict(os.environ, HSTACK_CODEX_AUTH_JSON='invalid seed must not be read',
                           HSTACK_CODEX_AUTH_HOME=str(auth_home))
        command = ['bash', str(HYBRID / 'start-cursor.sh'), '--skills', str(self.package),
                   '--skills-only', '--python', sys.executable]
        result = subprocess.run(command, cwd=self.project, env=environment, check=True,
                                capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout)['scope'], 'project')
        self.assertFalse(auth_home.exists())
        self.assertEqual(activation.git(self.project, 'status', '--porcelain'), '')

    def test_tracked_retired_skill_cannot_be_deleted_by_an_update(self):
        self.activate()
        retired = self.project / '.cursor/skills/hstack-how'
        activation.git(self.project, 'add', '--force', str(retired))
        shutil.rmtree(self.package / 'skills/hstack-how')
        with self.assertRaisesRegex(ValueError, 'tracked'):
            self.activate()
        self.assertTrue((retired / 'SKILL.md').is_file())

    def test_exclude_replacement_preserves_both_neighbors(self):
        original = 'before\n' + activation.BEGIN + '\nold/\n' + activation.END + '\nafter\n'
        updated = activation.exclusion_text(original, {'hstack-how'})
        self.assertTrue(updated.startswith('before\n'))
        self.assertTrue(updated.endswith('after\n'))
        self.assertNotIn('old/', updated)
        self.assertEqual(updated.count(activation.BEGIN), 1)


class CodexCloudDiscoveryTests(unittest.TestCase):
    def test_updates_only_a_previous_owned_build_link(self):
        code = (HYBRID / 'setup-codex-cloud.sh').read_text().split("<<'PY'\n", 1)[1].rsplit('\nPY', 1)[0]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / 'source'
            (source / 'pstack/skills/poteto-mode').mkdir(parents=True)
            (source / 'pstack/skills/poteto-mode/SKILL.md').write_text('upstream')
            revision = 'b' * 40
            output = root / 'builds' / revision
            package = output / 'codex/plugins/hstack'
            for relative in ('skills/hstack-poteto-mode/SKILL.md', 'hybrid/runtime/codex.md',
                             'config/default-models.json', 'SKILL-MAP.json', '.codex-plugin/plugin.json'):
                path = package / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('{}')
            (package / 'BUILD.json').write_text(json.dumps({
                'runtime': 'codex', 'source_revision': revision, 'source_sha256': 'fixture'}))
            discovery = root / 'skills'
            discovery.mkdir()
            previous = root / 'builds' / ('a' * 40) / 'codex/plugins/hstack'
            (previous / 'skills').mkdir(parents=True)
            (previous / 'BUILD.json').write_text(json.dumps({
                'runtime': 'codex', 'source_revision': 'a' * 40}))
            link = discovery / 'hstack'
            link.symlink_to(previous / 'skills', target_is_directory=True)
            command = [sys.executable, '-', str(root), str(source), str(output), str(discovery), revision]
            result = subprocess.run(command, input=code, check=True, capture_output=True, text=True)
            self.assertEqual(link.resolve(), package / 'skills')
            self.assertEqual(json.loads(result.stdout)['skill_count'], 1)
            subprocess.run(command, input=code, check=True, capture_output=True, text=True)
            link.unlink()
            unrelated = root / 'unrelated'
            unrelated.mkdir()
            link.symlink_to(unrelated, target_is_directory=True)
            result = subprocess.run(command, input=code, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('unmanaged', result.stderr)
            self.assertEqual(link.resolve(), unrelated)


if __name__ == '__main__':
    unittest.main()

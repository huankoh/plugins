import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

HYBRID = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hstack_cursor_install', HYBRID / 'install-cursor-local.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class CursorInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'generated'
        (self.source / '.cursor-plugin').mkdir(parents=True)
        (self.source / '.cursor-plugin/marketplace.json').write_text(json.dumps({
            'name': 'hstack', 'plugins': [{'name': 'hstack', 'source': './plugins/hstack'}]}))
        self.plugin = self.source / 'plugins/hstack'
        (self.plugin / '.cursor-plugin').mkdir(parents=True)
        (self.plugin / '.cursor-plugin/plugin.json').write_text('{"name":"hstack"}')
        (self.plugin / 'README.md').write_text('first build\n')
        self.destination = self.root / 'installed'

    def test_git_import_repeat_and_updates_preserve_cached_revisions(self):
        first = installer.install(self.source, self.destination)
        clone = self.root / 'cursor-cache'
        subprocess.run(['git', 'clone', '--quiet', '--no-local', str(self.destination), str(clone)], check=True)
        self.assertEqual((clone / 'plugins/hstack/README.md').read_text(), 'first build\n')
        again = installer.install(self.source, self.destination)
        self.assertEqual(again['status'], 'unchanged')
        self.assertEqual(again['commit'], first['commit'])
        (self.plugin / 'README.md').write_text('second build\n')
        updated = installer.install(self.source, self.destination)
        self.assertNotEqual(updated['commit'], first['commit'])
        subprocess.run(['git', '-C', str(clone), 'fetch', '--quiet', 'origin', first['commit']], check=True)
        subprocess.run(['git', '-C', str(clone), 'fetch', '--quiet', 'origin', updated['commit']], check=True)
        subprocess.run(['git', '-C', str(clone), 'merge-base', '--is-ancestor', first['commit'], updated['commit']], check=True)
        self.assertEqual(installer.git(self.destination, 'status', '--porcelain'), '')

    def test_refuses_unknown_or_modified_destination_without_losing_files(self):
        self.destination.mkdir()
        note = self.destination / 'note.txt'
        note.write_text('keep unknown files\n')
        with self.assertRaisesRegex(ValueError, 'unrecognized'):
            installer.install(self.source, self.destination)
        self.assertEqual(note.read_text(), 'keep unknown files\n')
        managed = self.root / 'managed'
        installer.install(self.source, managed)
        readme = managed / 'plugins/hstack/README.md'
        readme.write_text('keep my edits\n')
        with self.assertRaisesRegex(ValueError, 'local changes'):
            installer.install(self.source, managed)
        self.assertEqual(readme.read_text(), 'keep my edits\n')

    def test_copy_failure_preserves_install_and_allows_fixed_source_retry(self):
        first = installer.install(self.source, self.destination)
        (self.plugin / 'README.md').write_text('second build\n')
        broken = self.plugin / 'broken-link'
        broken.symlink_to('missing-file')
        with self.assertRaises(OSError):
            installer.install(self.source, self.destination)
        self.assertEqual((self.destination / 'plugins/hstack/README.md').read_text(), 'first build\n')
        self.assertEqual(installer.git(self.destination, 'rev-parse', 'HEAD'), first['commit'])
        self.assertEqual(installer.git(self.destination, 'status', '--porcelain'), '')
        fresh = self.root / 'fresh-install'
        with self.assertRaises(OSError):
            installer.install(self.source, fresh)
        self.assertFalse(fresh.exists())
        broken.unlink()
        result = installer.install(self.source, self.destination)
        self.assertEqual(result['status'], 'updated')
        self.assertEqual((self.destination / 'plugins/hstack/README.md').read_text(), 'second build\n')
        self.assertEqual(installer.git(self.destination, 'status', '--porcelain'), '')


if __name__ == '__main__':
    unittest.main()

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HYBRID = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hstack_worker', HYBRID / 'worker.py')
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class WorkerTests(unittest.TestCase):
    def test_binary_resolution_preserves_overrides_and_finds_installer_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            installed = root / 'private/node_modules/.bin/codex'
            installed.parent.mkdir(parents=True)
            installed.write_text('#!/bin/sh\nexit 0\n')
            installed.chmod(0o755)
            path_directory = root / 'bin'
            path_directory.mkdir()
            env = dict(os.environ, HSTACK_CODEX_PREFIX=str(root / 'private'), PATH=str(path_directory))
            env.pop('HSTACK_CODEX_BINARY', None)
            with patch.dict(os.environ, env, clear=True):
                self.assertEqual(worker.resolve_binary(), str(installed))
                installed.chmod(0o644)
                self.assertNotEqual(worker.resolve_binary(), str(installed))
                installed.chmod(0o755)
                path_binary = path_directory / 'codex'
                path_binary.write_text('#!/bin/sh\nexit 0\n')
                path_binary.chmod(0o755)
                self.assertEqual(worker.resolve_binary(), str(path_binary))
                with patch.dict(os.environ, {'HSTACK_CODEX_BINARY': str(root / 'explicit-codex')}):
                    self.assertEqual(worker.resolve_binary(), str(root / 'explicit-codex'))


if __name__ == '__main__':
    unittest.main()

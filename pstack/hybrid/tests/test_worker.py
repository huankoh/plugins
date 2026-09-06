import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

HYBRID = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hstack_worker', HYBRID / 'worker.py')
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class WorkerTests(unittest.TestCase):
    def test_auth_seed_uses_private_home_and_is_removed_from_child_environment(self):
        with patch.dict(os.environ, {
            'HOME': '/home/fixture', 'CODEX_HOME': '/home/fixture/desktop-codex',
            'HSTACK_CODEX_AUTH_JSON': 'private-seed-fixture',
            'OPENAI_API_KEY': 'api-key-fixture', 'CODEX_API_KEY': 'other-api-key-fixture',
            'OPENAI_BASE_URL': 'https://provider.invalid', 'OPENAI_API_BASE': 'https://provider.invalid',
            'CODEX_BASE_URL': 'https://provider.invalid',
        }, clear=True):
            env = worker.environment()
        self.assertEqual(env, {'HOME': '/home/fixture', 'CODEX_HOME': '/home/fixture/.local/share/hstack-codex-auth'})
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(worker.environment(), env)

    def test_auth_home_override_survives_sanitization_with_or_without_seed(self):
        for seed in (None, 'private-seed-fixture'):
            with self.subTest(seed_present=seed is not None):
                env = {'HOME': '/home/fixture', 'CODEX_HOME': '/desktop-codex',
                       'HSTACK_CODEX_AUTH_HOME': '~/dedicated-codex'}
                if seed:
                    env['HSTACK_CODEX_AUTH_JSON'] = seed
                with patch.dict(os.environ, env, clear=True):
                    child_env = worker.environment()
                self.assertEqual(child_env, {'HOME': '/home/fixture', 'CODEX_HOME': '/home/fixture/dedicated-codex'})
                with patch.dict(os.environ, child_env, clear=True):
                    self.assertEqual(worker.environment(), child_env)

    def test_desktop_auth_home_is_preserved_without_bootstrap_configuration(self):
        for home in (None, '/desktop-codex'):
            with self.subTest(codex_home=home):
                env = {'HOME': '/home/fixture', 'HSTACK_CODEX_AUTH_JSON': '', 'HSTACK_CODEX_AUTH_HOME': ''}
                if home:
                    env['CODEX_HOME'] = home
                with patch.dict(os.environ, env, clear=True):
                    child_env = worker.environment()
                self.assertEqual(child_env.get('CODEX_HOME'), home)
                self.assertNotIn('HSTACK_CODEX_AUTH_JSON', child_env)
                self.assertNotIn('HSTACK_CODEX_AUTH_HOME', child_env)

    def test_models_use_selected_auth_home(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private_home = root / '.local/share/hstack-codex-auth'
            private_home.mkdir(parents=True)
            cache = private_home / 'models_cache.json'
            cache.write_text(json.dumps({'models': [{'slug': 'fixture-model', 'visibility': 'list'}]}))
            with patch.dict(os.environ, {'HOME': directory, 'CODEX_HOME': str(root / 'desktop'),
                                         'HSTACK_CODEX_AUTH_JSON': 'private-seed-fixture'}, clear=True):
                catalog = worker.models()
            self.assertEqual(catalog['source'], str(cache))
            self.assertEqual(catalog['models'][0]['model'], 'fixture-model')

    def test_real_supervisor_preserves_selected_home_without_passing_seed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake = root / 'fake-codex'
            fake.write_text('''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys

args = sys.argv[1:]
stage = 'version' if '--version' in args else 'login' if 'login' in args else 'exec'
safe = (os.environ.get('CODEX_HOME') == os.environ['FIXTURE_AUTH_HOME']
        and 'HSTACK_CODEX_AUTH_JSON' not in os.environ
        and 'HSTACK_CODEX_AUTH_HOME' not in os.environ)
with open(os.environ['FIXTURE_CALLS'], 'a') as stream:
    stream.write(json.dumps({'stage': stage, 'isolated': safe}) + '\\n')
if not safe:
    sys.exit(7)
if stage == 'version':
    print('codex-cli test-double')
elif stage == 'login':
    print('Logged in using ChatGPT')
else:
    sys.stdin.read()
    Path(args[args.index('--output-last-message') + 1]).write_text('fixture passed')
''')
            fake.chmod(0o755)
            calls = root / 'calls.jsonl'
            task = root / 'task.json'
            task.write_text(json.dumps({'prompt': 'Check environment isolation'}))
            env = dict(os.environ, HOME=directory, CODEX_HOME=str(root / 'desktop'),
                       HSTACK_CODEX_AUTH_JSON='private-seed-fixture',
                       HSTACK_CODEX_DATA=str(root / 'state'), HSTACK_CODEX_BINARY=str(fake),
                       FIXTURE_CALLS=str(calls), FIXTURE_AUTH_HOME=str(root / '.local/share/hstack-codex-auth'))
            env.pop('HSTACK_CODEX_AUTH_HOME', None)

            def call(*args):
                result = subprocess.run([sys.executable, str(HYBRID / 'worker.py'), *args],
                                        env=env, capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return json.loads(result.stdout)

            self.assertTrue(call('doctor')['ready'])
            job = call('submit', '--cwd', directory, '--task', str(task), '--timeout-seconds', '5')
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                status = call('status', job['id'])
                if status['status'] not in worker.ACTIVE:
                    break
                time.sleep(0.05)
            else:
                self.fail('Fixture supervisor did not finish')
            self.assertEqual(status['status'], 'succeeded')
            observed = [json.loads(line) for line in calls.read_text().splitlines()]
            self.assertEqual([record['stage'] for record in observed], ['version', 'login', 'login', 'exec'])
            self.assertTrue(all(record['isolated'] for record in observed))

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

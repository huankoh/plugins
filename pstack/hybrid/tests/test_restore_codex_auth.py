import concurrent.futures
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'restore-codex-auth.py'
SENTINEL = 'secret-marker-never-print'


def seed(marker=SENTINEL):
    return {
        'auth_mode': 'chatgpt',
        'OPENAI_API_KEY': None,
        'tokens': {
            'id_token': marker + '-id',
            'access_token': marker + '-access',
            'refresh_token': marker + '-refresh',
            'account_id': 'test-account',
        },
        'last_refresh': '2026-09-06T00:00:00Z',
    }


class RestoreCodexAuthTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.auth_home = self.root / 'auth-cache'

    def run_bootstrap(self, raw=None, auth_home=None, **env_overrides):
        env = dict(os.environ)
        env.pop('HSTACK_CODEX_AUTH_JSON', None)
        if raw is not None:
            env['HSTACK_CODEX_AUTH_JSON'] = raw
        env.update(env_overrides)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), '--auth-home', str(auth_home or self.auth_home)],
            env=env, text=True, capture_output=True, timeout=15,
        )
        self.assertNotIn(SENTINEL, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stdout + result.stderr)
        return result

    def test_restores_full_auth_with_private_permissions(self):
        result = self.run_bootstrap(json.dumps(seed()))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads((self.auth_home / 'auth.json').read_text()), seed())
        self.assertEqual(stat.S_IMODE(self.auth_home.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((self.auth_home / 'auth.json').stat().st_mode), 0o600)
        self.assertEqual([p.name for p in self.auth_home.iterdir()], ['auth.json'])

    def test_existing_refreshed_cache_wins_over_new_missing_or_invalid_seed(self):
        self.assertEqual(self.run_bootstrap(json.dumps(seed())).returncode, 0)
        cache = self.auth_home / 'auth.json'
        refreshed = json.dumps(seed('refreshed-token')).encode()
        cache.write_bytes(refreshed)
        inode = cache.stat().st_ino
        for raw in (json.dumps(seed('different-seed')), None, SENTINEL + '-invalid'):
            with self.subTest(raw_is_missing=raw is None):
                result = self.run_bootstrap(raw)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('preserved', result.stdout)
                self.assertEqual(cache.read_bytes(), refreshed)
                self.assertEqual(cache.stat().st_ino, inode)

    def test_existing_cache_permissions_are_private_without_reseeding(self):
        self.auth_home.mkdir(mode=0o755)
        cache = self.auth_home / 'auth.json'
        cache.write_text('refreshed-cache')
        cache.chmod(0o644)
        result = self.run_bootstrap()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(cache.read_text(), 'refreshed-cache')
        self.assertEqual(stat.S_IMODE(cache.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.auth_home.stat().st_mode), 0o700)

    def test_default_cache_is_dedicated_to_hstack(self):
        env = dict(os.environ, HOME=str(self.root), HSTACK_CODEX_AUTH_JSON=json.dumps(seed()))
        result = subprocess.run(
            [sys.executable, str(SCRIPT)], env=env, text=True, capture_output=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(SENTINEL, result.stdout + result.stderr)
        self.assertEqual(json.loads((self.root / '.local/share/hstack-codex-auth/auth.json').read_text()), seed())
        self.assertFalse((self.root / '.codex').exists())

    def test_invalid_secrets_fail_without_values_or_auth_files(self):
        cases = [None, SENTINEL + '-bad-json', json.dumps([SENTINEL]), '{"auth_mode":"chatgpt","auth_mode":"' + SENTINEL + '"}', '{"auth_mode":"chatgpt","tokens":NaN}']
        for key in ('id_token', 'access_token', 'refresh_token'):
            for value in ('', ' ', None, 42):
                auth = seed()
                auth['tokens'][key] = value
                cases.append(json.dumps(auth))
        for raw in cases:
            with self.subTest(raw_is_missing=raw is None):
                result = self.run_bootstrap(raw)
                self.assertEqual(result.returncode, 1)
                self.assertFalse((self.auth_home / 'auth.json').exists())

    def test_rejects_api_credentials_and_other_auth_modes(self):
        for key in ('OPENAI_API_KEY', 'api_key', 'apiKey'):
            auth = seed()
            auth[key] = SENTINEL
            self.assertEqual(self.run_bootstrap(json.dumps(auth)).returncode, 1)
        for mode in ('apikey', 'chatgptAuthTokens', SENTINEL):
            auth = seed()
            auth['auth_mode'] = mode
            self.assertEqual(self.run_bootstrap(json.dumps(auth)).returncode, 1)
        result = self.run_bootstrap(OPENAI_API_KEY=SENTINEL, CODEX_API_KEY=SENTINEL)
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.auth_home / 'auth.json').exists())

    def test_rejects_auth_file_symlink_without_touching_target(self):
        self.auth_home.mkdir()
        target = self.root / 'target'
        target.write_text(SENTINEL)
        target.chmod(0o644)
        (self.auth_home / 'auth.json').symlink_to(target)
        self.assertEqual(self.run_bootstrap(json.dumps(seed())).returncode, 1)
        self.assertEqual(target.read_text(), SENTINEL)
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o644)

    def test_rejects_symlinked_cache_and_ancestor(self):
        target = self.root / 'target'
        target.mkdir()
        self.auth_home.symlink_to(target, target_is_directory=True)
        self.assertEqual(self.run_bootstrap(json.dumps(seed())).returncode, 1)
        self.assertEqual(self.run_bootstrap(json.dumps(seed()), self.auth_home / 'nested').returncode, 1)
        self.assertEqual(list(target.iterdir()), [])

    def test_rejects_nonregular_cache_without_blocking(self):
        self.auth_home.mkdir()
        os.mkfifo(self.auth_home / 'auth.json')
        self.assertEqual(self.run_bootstrap(json.dumps(seed())).returncode, 1)

    def test_rejects_parent_traversal_and_git_checkouts(self):
        result = self.run_bootstrap(json.dumps(seed()), str(self.root / 'child') + '/../escaped')
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.root / 'escaped').exists())
        for git_is_file in (False, True):
            checkout = self.root / ('worktree' if git_is_file else 'checkout')
            checkout.mkdir()
            if git_is_file:
                (checkout / '.git').write_text('gitdir: /test-only')
            else:
                (checkout / '.git').mkdir()
            result = self.run_bootstrap(json.dumps(seed()), checkout / 'cache')
            self.assertEqual(result.returncode, 1)
            self.assertFalse((checkout / 'cache').exists())

    def test_simultaneous_bootstraps_publish_one_complete_seed(self):
        seeds = [seed('concurrent-' + str(i)) for i in range(12)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(lambda value: self.run_bootstrap(json.dumps(value)), seeds))
        self.assertTrue(all(result.returncode == 0 for result in results), [result.stderr for result in results])
        self.assertEqual(sum('restored' in result.stdout for result in results), 1)
        self.assertIn(json.loads((self.auth_home / 'auth.json').read_text()), seeds)
        self.assertEqual([p.name for p in self.auth_home.iterdir()], ['auth.json'])


if __name__ == '__main__':
    unittest.main()

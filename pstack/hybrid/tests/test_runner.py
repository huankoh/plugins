import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

HYBRID = Path(__file__).resolve().parents[1]


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.env = dict(os.environ, HSTACK_CODEX_DATA=str(self.root / 'state'), HSTACK_CODEX_BINARY=str(HYBRID / 'tests/fake_codex.py'))
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        (self.repo / 'value.txt').write_text('original\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture base')
        self.base = self.git('rev-parse', 'HEAD')

    def tearDown(self):
        # All tests await their jobs before deleting state.
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.PIPE, text=True).strip()

    def call(self, *args, success=True):
        result = subprocess.run([sys.executable, str(HYBRID / 'runner.py'), *args], env=self.env, capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return json.loads(result.stdout)

    def submit(self, key='review', prompt='Review fixture', role='review', timeout=10, checks=None):
        task = self.root / (key + '.json')
        task.write_text(json.dumps({'prompt': prompt, 'checks': checks or []}))
        args = ['submit', '--repo', str(self.repo), '--base', self.base, '--head', self.base,
                '--key', key, '--task', str(task), '--role', role, '--timeout-seconds', str(timeout)]
        if role == 'rescue':
            args += ['--writer-stopped']
        return self.call(*args)

    def collect(self, key='review'):
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            result = self.call('result', key)
            if result['status'] in {'succeeded', 'failed', 'cancelled', 'interrupted'}:
                return result
            time.sleep(0.05)
        self.fail('Job did not finish')

    def test_review_idempotence_and_stale_head(self):
        first = self.submit()
        again = self.submit()
        self.assertEqual(first['worker_id'], again['worker_id'])
        result = self.collect()
        self.assertEqual(result['verification'], 'passed')
        self.assertTrue(self.call('validate', 'review', '--head', self.base)['valid'])
        (self.repo / 'value.txt').write_text('changed\n')
        self.assertIn('uncommitted', self.call('validate', 'review', '--head', self.base, success=False)['error'])
        self.git('commit', '-qam', 'later change')
        self.assertIn('stale', self.call('validate', 'review', '--head', 'HEAD', success=False)['error'])

    def test_rescue_collects_patch_and_preserves_source(self):
        self.submit(role='rescue', prompt='FAKE_EDIT', checks=[[sys.executable, '-c', "from pathlib import Path; assert Path('value.txt').read_text() == 'fixed\\n'"]])
        result = self.collect()
        self.assertEqual(result['verification'], 'passed')
        self.assertEqual(set(result['changed_paths']), {'value.txt', 'new.txt'})
        self.assertIn('new file', Path(result['patch']).read_text())
        self.assertEqual((self.repo / 'value.txt').read_text(), 'original\n')
        self.assertFalse((self.repo / 'new.txt').exists())
        self.git('apply', '--check', result['patch'])

    def test_read_only_contract_rejects_mutation(self):
        self.submit(prompt='FAKE_EDIT')
        self.assertEqual(self.collect()['verification'], 'failed')

    def test_review_acceptance_can_use_temporary_files_and_still_gates_success(self):
        check = """import csv
import tempfile
with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv') as fixture:
    fixture.write('amount\\n7.50\\n')
    fixture.seek(0)
    assert list(csv.DictReader(fixture)) == [{'amount': '7.50'}]
"""
        job = self.submit(checks=[[sys.executable, '-c', check]])
        result = self.collect()
        state = json.loads((self.root / 'state/jobs' / job['worker_id'] / 'state.json').read_text())
        self.assertEqual(state['sandbox'], 'read-only')
        self.assertEqual(result['verification'], 'passed')
        self.assertEqual(result['checks'][0]['exit_code'], 0)
        self.assertEqual(result['changed_paths'], [])
        self.assertEqual(self.git('status', '--porcelain'), '')
        self.submit(key='failing-check', checks=[[sys.executable, '-c', check + 'raise SystemExit(3)\n']])
        failed = self.collect('failing-check')
        self.assertEqual(failed['report']['verdict'], 'pass')
        self.assertEqual(failed['checks'][0]['exit_code'], 3)
        self.assertEqual(failed['verification'], 'failed')

    def test_runner_children_cannot_inherit_auth_seed(self):
        real_git = shutil.which('git')
        binary_directory = self.root / 'bin'
        binary_directory.mkdir()
        git_calls = self.root / 'git-calls.jsonl'
        git_wrapper = binary_directory / 'git'
        git_wrapper.write_text('''#!/usr/bin/env python3
import json
import os
import sys

for key in ('HSTACK_CODEX_AUTH_JSON', 'HSTACK_CODEX_AUTH_HOME', 'OPENAI_API_KEY', 'CODEX_API_KEY',
            'OPENAI_BASE_URL', 'OPENAI_API_BASE', 'CODEX_BASE_URL'):
    if key in os.environ:
        sys.exit(81)
if os.environ.get('CODEX_HOME') != os.environ['FIXTURE_CODEX_HOME']:
    sys.exit(82)
with open(os.environ['FIXTURE_GIT_CALLS'], 'a') as stream:
    stream.write(json.dumps({'command': sys.argv[3], 'has_index': 'GIT_INDEX_FILE' in os.environ}) + '\\n')
os.execv(os.environ['FIXTURE_REAL_GIT'], [os.environ['FIXTURE_REAL_GIT'], *sys.argv[1:]])
''')
        git_wrapper.chmod(0o755)
        seed = 'private-runner-seed-fixture-94c21'
        self.env.update(
            HOME=str(self.root), CODEX_HOME=str(self.root / 'desktop-codex'),
            HSTACK_CODEX_AUTH_JSON=seed, OPENAI_API_KEY='fixture-api-key',
            CODEX_API_KEY='fixture-api-key', OPENAI_BASE_URL='https://fixture.invalid',
            OPENAI_API_BASE='https://fixture.invalid', CODEX_BASE_URL='https://fixture.invalid',
            FIXTURE_CODEX_HOME=str(self.root / '.local/share/hstack-codex-auth'),
            FIXTURE_REAL_GIT=real_git, FIXTURE_GIT_CALLS=str(git_calls),
            PATH=str(binary_directory) + os.pathsep + os.environ.get('PATH', ''),
        )
        self.env.pop('HSTACK_CODEX_AUTH_HOME', None)
        check = """import os
for name in ('HSTACK_CODEX_AUTH_JSON', 'HSTACK_CODEX_AUTH_HOME', 'OPENAI_API_KEY', 'CODEX_API_KEY',
             'OPENAI_BASE_URL', 'OPENAI_API_BASE', 'CODEX_BASE_URL'):
    assert name not in os.environ, name + ' unexpectedly inherited'
assert os.environ['CODEX_HOME'] == os.environ['FIXTURE_CODEX_HOME']
print('AUTH_ENV_ISOLATED')
"""
        self.assertTrue(self.call('doctor')['ready'])
        self.submit(checks=[[sys.executable, '-c', check]])
        result = self.collect()
        self.assertEqual(result['verification'], 'passed')
        self.assertEqual(result['checks'][0]['exit_code'], 0)
        self.assertEqual(Path(result['checks'][0]['log']).read_text(), 'AUTH_ENV_ISOLATED\n')
        calls = [json.loads(line) for line in git_calls.read_text().splitlines()]
        self.assertIn('merge-base', {call['command'] for call in calls})
        for command in ('read-tree', 'add', 'diff'):
            self.assertTrue(any(call['command'] == command and call['has_index'] for call in calls))
        for artifact in (self.root / 'state').rglob('*'):
            if artifact.is_file():
                self.assertNotIn(seed.encode(), artifact.read_bytes(), str(artifact))

    def test_findings_and_failed_checks_are_not_accepted(self):
        self.submit(prompt='FAKE_FINDING')
        self.assertEqual(self.collect()['verification'], 'failed')
        self.submit(key='blocked-review', prompt='FAKE_BLOCKED', checks=[[sys.executable, '-c', 'pass']])
        blocked = self.collect('blocked-review')
        self.assertEqual(blocked['report']['verdict'], 'blocked')
        self.assertEqual(blocked['checks'][0]['exit_code'], 0)
        self.assertEqual(blocked['verification'], 'failed')
        self.submit(key='check', checks=[[sys.executable, '-c', 'raise SystemExit(3)']])
        self.assertEqual(self.collect('check')['verification'], 'failed')

    def test_failure_invalid_report_and_timeout(self):
        for key, prompt, timeout in [('fail', 'FAKE_FAIL', 10), ('bad', 'FAKE_BAD_REPORT', 10), ('timeout', 'FAKE_SLEEP', 1)]:
            self.submit(key=key, prompt=prompt, timeout=timeout)
            result = self.collect(key)
            self.assertNotEqual(result['verification'], 'passed')
            if key == 'timeout':
                self.assertEqual(result['status'], 'failed')

    def test_concurrent_submit_and_cancel(self):
        first = self.submit(prompt='FAKE_SLEEP')
        task = self.root / 'another.json'
        task.write_text('{"prompt":"another"}')
        failure = self.call('submit', '--repo', str(self.repo), '--base', self.base, '--head', self.base,
                           '--key', 'another', '--task', str(task), success=False)
        self.assertIn('unfinished', failure['error'])
        self.call('cancel', first['key'])
        self.assertEqual(self.collect()['status'], 'cancelled')

    def test_lost_worker_lock_marks_interrupted_without_resubmitting(self):
        job = self.submit()
        self.collect()
        state_path = self.root / 'state/jobs' / job['worker_id'] / 'state.json'
        state = json.loads(state_path.read_text())
        state['status'] = 'running'
        state_path.write_text(json.dumps(state))
        handoff_path = self.root / 'state/handoffs/review/handoff.json'
        handoff = json.loads(handoff_path.read_text())
        handoff['status'] = 'running'
        handoff_path.write_text(json.dumps(handoff))
        result = self.collect()
        self.assertEqual(result['status'], 'interrupted')
        self.assertNotEqual(result['verification'], 'passed')
        self.assertEqual(self.submit()['worker_id'], job['worker_id'])

    def test_key_conflict_and_preparation_failure(self):
        self.submit()
        self.collect()
        task = self.root / 'different.json'
        task.write_text('{"prompt":"different"}')
        self.assertIn('different request', self.call('submit', '--repo', str(self.repo), '--base', self.base,
            '--head', self.base, '--key', 'review', '--task', str(task), success=False)['error'])
        self.env['HSTACK_CODEX_BINARY'] = str(self.root / 'missing')
        self.assertIn('FileNotFoundError', self.call('submit', '--repo', str(self.repo), '--base', self.base,
            '--head', self.base, '--key', 'missing', '--task', str(task), success=False)['error'])
        self.assertEqual(self.call('status', 'missing')['status'], 'interrupted')


if __name__ == '__main__':
    unittest.main()

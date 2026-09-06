import json
import os
from pathlib import Path
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
        self.env = dict(os.environ, PSTACK_CODEX_DATA=str(self.root / 'state'), PSTACK_CODEX_BINARY=str(HYBRID / 'tests/fake_codex.py'))
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

    def test_findings_and_failed_checks_are_not_accepted(self):
        self.submit(prompt='FAKE_FINDING')
        self.assertEqual(self.collect()['verification'], 'failed')
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
        self.env['PSTACK_CODEX_BINARY'] = str(self.root / 'missing')
        self.assertIn('FileNotFoundError', self.call('submit', '--repo', str(self.repo), '--base', self.base,
            '--head', self.base, '--key', 'missing', '--task', str(task), success=False)['error'])
        self.assertEqual(self.call('status', 'missing')['status'], 'interrupted')


if __name__ == '__main__':
    unittest.main()

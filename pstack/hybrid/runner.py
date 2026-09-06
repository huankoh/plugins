#!/usr/bin/env python3
"""Isolated Codex review/rescue jobs. Run --help for the lifecycle interface."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import worker

ROOT = worker.ROOT / 'handoffs'
TERMINAL = {'succeeded', 'failed', 'cancelled', 'interrupted'}


def git(repo, *args, env=None):
    return subprocess.check_output(['git', '-C', str(repo), *args], env=env,
                                   stderr=subprocess.PIPE).decode().strip()


def locked():
    ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(ROOT / '.lock', os.O_RDWR | os.O_CREAT, 0o600)
    fcntl.flock(fd, fcntl.LOCK_EX)
    return fd


def path_for(key):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,100}', key):
        raise ValueError('Key must be 1-101 letters, numbers, dots, underscores or hyphens')
    return ROOT / key


def load(key):
    return worker.read(path_for(key) / 'handoff.json')


def save(job):
    worker.save(path_for(job['key']) / 'handoff.json', job)


def canonical_repo(path):
    return str(Path(git(path, 'rev-parse', '--show-toplevel')).resolve())


def commit(repo, ref):
    return git(repo, 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}')


def check_task(task):
    if not isinstance(task, dict) or set(task) - {'prompt', 'checks'}:
        raise ValueError('Task accepts prompt and optional checks only')
    if not isinstance(task.get('prompt'), str) or not task['prompt'].strip():
        raise ValueError('Task needs a nonempty prompt')
    checks = task.get('checks', [])
    if not isinstance(checks, list) or any(not isinstance(c, list) or not c or any(not isinstance(a, str) or not a for a in c) for c in checks):
        raise ValueError('Checks must be nonempty argv arrays, not shell command strings')


def runtime_identity():
    package = Path(__file__).resolve().parent.parent
    if (package / 'BUILD.json').exists():
        identity = worker.read(package / 'BUILD.json')
    else:
        identity = {'source_revision': git(package, 'rev-parse', 'HEAD')}
    identity['runner_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    identity['worker_sha256'] = hashlib.sha256(Path(worker.__file__).read_bytes()).hexdigest()
    return identity


def submit(args):
    task = json.load(sys.stdin) if args.task == '-' else worker.read(Path(args.task))
    check_task(task)
    repo = canonical_repo(args.repo)
    base, head = commit(repo, args.base), commit(repo, args.head)
    subprocess.run(['git', '-C', repo, 'merge-base', '--is-ancestor', base, head], check=True, capture_output=True)
    if args.role == 'rescue' and not args.writer_stopped:
        raise ValueError('Rescue requires --writer-stopped after the coordinator confirms the prior writer ended')
    request = dict(repo=repo, base=base, head=head, role=args.role, task=task,
                   model=args.model, effort=args.effort, timeout_seconds=args.timeout_seconds)
    fingerprint = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
    directory = path_for(args.key)
    fd = locked()
    try:
        if (directory / 'handoff.json').exists():
            existing = load(args.key)
            if existing['fingerprint'] != fingerprint:
                raise ValueError('Key already belongs to a different request')
            return existing
        common = str((Path(repo) / git(repo, 'rev-parse', '--git-common-dir')).resolve())
        for existing_path in ROOT.glob('*/handoff.json'):
            existing = worker.read(existing_path)
            if existing['common_dir'] == common and existing['status'] not in TERMINAL:
                raise ValueError('Repository has an unfinished job; collect its result before another submission')
        directory.mkdir(mode=0o700)
        checkout = directory / 'checkout'
        job = dict(request, key=args.key, fingerprint=fingerprint, common_dir=common,
                   checkout=str(checkout), worker_id=hashlib.sha256((args.key + fingerprint).encode()).hexdigest()[:32], status='preparing', verification='pending', created_at=time.time())
        job['hstack'] = runtime_identity()
        save(job)
        # The public record exists before the subprocess is started. An uncertain
        # handoff remains visible and cannot silently launch a duplicate.
        git(repo, 'worktree', 'add', '--detach', str(checkout), head)
        prompt = ('You are a bounded hstack worker. Do not delegate to another execution backend. '
                  'Do not push, merge, or change the source checkout. Return the required JSON report. '
                  'Findings must contain only unresolved blocking issues; use an empty findings array when passing. Put completed work and evidence in summary.\n'
                  + ('Review only. Do not modify tracked or untracked project files. ' if args.role == 'review' else
                     'Implement only the assigned rescue/implementation. Leave changes in this checkout; do not commit. ')
                  + f'\nOriginal base: {base}\nInput head: {head}\n'
                  + f'Read the hstack Codex adapter at {Path(__file__).parent / "runtime/codex.md"}. '
                  + f'Apply the verification principle at {Path(__file__).parent.parent / "skills/principle-prove-it-works/SKILL.md"}. '
                  + 'Your bounded worker role overrides orchestrator instructions: do not spawn another backend or run the full orchestration loop.\n'
                  + 'Read AGENTS.md and applicable repository instructions. Inspect the diff from original base to input head.\n'
                  + task['prompt'] + '\nAcceptance commands: ' + json.dumps(task.get('checks', [])))
        task_path = directory / 'worker-task.json'
        worker.save(task_path, {'prompt': prompt})
        submitted = worker.submit(argparse.Namespace(cwd=str(checkout), model=args.model, effort=args.effort,
            sandbox='read-only' if args.role == 'review' else 'workspace-write',
            timeout_seconds=args.timeout_seconds, task=str(task_path), job_id=job['worker_id']))
        job.update(worker_id=submitted['id'], status='running')
        save(job)
        return job
    except Exception:
        if (directory / 'handoff.json').exists():
            job = load(args.key)
            if job.get('fingerprint') == fingerprint and job['status'] == 'preparing':
                job.update(status='running' if (worker.job_path(job['worker_id']) / 'state.json').exists() else 'interrupted', verification='blocked', error='Preparation or submission failed; inspect before retrying')
                save(job)
        raise
    finally:
        os.close(fd)


def capture(job):
    directory = path_for(job['key'])
    env = os.environ.copy()
    env['GIT_INDEX_FILE'] = str(directory / 'artifact.index')
    git(job['checkout'], 'read-tree', job['head'], env=env)
    git(job['checkout'], 'add', '-A', '--', '.', env=env)
    patch = subprocess.check_output(['git', '-C', job['checkout'], 'diff', '--cached', '--binary', job['head']], env=env)
    (directory / 'changes.patch').write_bytes(patch)
    paths = git(job['checkout'], 'diff', '--cached', '--name-only', job['head'], env=env).splitlines()
    return {'patch': str(directory / 'changes.patch'), 'changed_paths': paths,
            'result_head': git(job['checkout'], 'rev-parse', 'HEAD')}


def inspect(key, collect=False):
    fd = locked()
    try:
        job = load(key)
        if job['status'] in TERMINAL or 'worker_id' not in job:
            return job
        if not (worker.job_path(job['worker_id']) / 'state.json').exists():
            job.update(status='interrupted', verification='blocked', error='Preparation ended without a worker record')
            save(job)
            return job
        info = worker.snapshot(job['worker_id'])
        if info['status'] not in TERMINAL:
            return dict(job, worker_status=info['status'])
        if not collect:
            return dict(job, worker_status=info['status'], result_pending=True)
        job.update(status=info['status'], verification='blocked', finished_at=time.time())
        try:
            job.update(capture(job))
            report_path = worker.job_path(job['worker_id']) / 'result.txt'
            report = json.loads(report_path.read_text())
            if set(report) != {'summary', 'verdict', 'findings'} or report['verdict'] not in {'pass', 'fail', 'blocked'} or not isinstance(report['summary'], str) or not isinstance(report['findings'], list) or any(not isinstance(f, str) for f in report['findings']):
                raise ValueError('Invalid worker report')
            job['report'] = report
            outcomes = []
            if info['status'] == 'succeeded':
                for index, argv in enumerate(job['task'].get('checks', [])):
                    log = path_for(key) / f'check-{index}.log'
                    with log.open('wb') as stream:
                        try:
                            result = subprocess.run(argv, cwd=job['checkout'], stdout=stream, stderr=subprocess.STDOUT,
                                                    timeout=job['timeout_seconds'])
                            code = result.returncode
                        except subprocess.TimeoutExpired:
                            code = 124
                        except OSError:
                            code = 127
                    outcomes.append({'argv': argv, 'exit_code': code, 'log': str(log)})
            job['checks'] = outcomes
            # Checks can alter tracked files too. Capture the final, verified artifact.
            job.update(capture(job))
            review_clean = job['role'] != 'review' or (not job['changed_paths'] and job['result_head'] == job['head'])
            passed = info['status'] == 'succeeded' and report['verdict'] == 'pass' and not report['findings'] and all(c['exit_code'] == 0 for c in outcomes) and review_clean
            job['verification'] = 'passed' if passed else 'failed'
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            job['error'] = 'Result collection failed: ' + type(exc).__name__
        save(job)
        return job
    finally:
        os.close(fd)


def validate(key, head):
    job = inspect(key, collect=True)
    if job['role'] != 'review' or job['verification'] != 'passed':
        raise ValueError('Job is not a passed independent review')
    if commit(job['repo'], head) != job['head']:
        raise ValueError('Review is stale: current head differs from reviewed head')
    if git(job['repo'], 'status', '--porcelain'):
        raise ValueError('Source checkout has uncommitted changes; this review covers the committed head only')
    return {'key': key, 'valid': True, 'reviewed_head': job['head']}


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    commands.add_parser('doctor')
    create = commands.add_parser('submit')
    for name in ('repo', 'base', 'head', 'key', 'task'):
        create.add_argument('--' + name, required=True)
    create.add_argument('--role', choices=['review', 'rescue', 'implement'], default='review')
    create.add_argument('--writer-stopped', action='store_true')
    create.add_argument('--model')
    create.add_argument('--effort')
    create.add_argument('--timeout-seconds', type=int, default=1800)
    for name in ('status', 'result', 'cancel'):
        commands.add_parser(name).add_argument('key')
    verify = commands.add_parser('validate')
    verify.add_argument('key')
    verify.add_argument('--head', required=True)
    args = parser.parse_args()
    if args.action == 'doctor':
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('worker.py')), 'doctor'])
        return result.returncode
    if args.action == 'submit':
        result = submit(args)
    elif args.action == 'validate':
        result = validate(args.key, args.head)
    elif args.action == 'cancel':
        job = load(args.key)
        if 'worker_id' in job:
            info = worker.snapshot(job['worker_id'])
            if info['status'] == 'orphaned':
                raise ValueError('Orphaned worker: inspect checkout; no PID will be signalled')
            if info['status'] in worker.ACTIVE:
                (worker.job_path(job['worker_id']) / 'cancel.request').touch(mode=0o600)
        result = inspect(args.key)
    else:
        result = inspect(args.key, collect=args.action == 'result')
    worker.emit(result)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        worker.emit({'error': str(exc) if isinstance(exc, ValueError) else type(exc).__name__})
        sys.exit(1)

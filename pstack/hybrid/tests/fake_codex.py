#!/usr/bin/env python3
"""Deterministic CLI double for process and artifact tests, never a real model."""
import json
from pathlib import Path
import sys
import time

args = sys.argv[1:]
if '--version' in args:
    print('codex-cli test-double')
elif 'login' in args:
    print('Logged in using ChatGPT')
else:
    prompt = sys.stdin.read()
    if 'FAKE_SLEEP' in prompt:
        time.sleep(30)
    if 'FAKE_FAIL' in prompt:
        sys.exit(7)
    if 'FAKE_EDIT' in prompt:
        Path('value.txt').write_text('fixed\n')
        Path('new.txt').write_text('new file\n')
    report = {'summary': 'fixture result', 'verdict': 'pass', 'findings': []}
    if 'FAKE_FINDING' in prompt:
        report['findings'] = ['Blocking fixture finding']
    if 'FAKE_BAD_REPORT' in prompt:
        report = {'invalid': True}
    Path(args[args.index('--output-last-message') + 1]).write_text(json.dumps(report))
    print(json.dumps({'type': 'turn.completed'}))

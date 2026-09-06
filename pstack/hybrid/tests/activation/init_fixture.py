#!/usr/bin/env python3
"""Create a disposable Git repository with a reproducible accounting defect."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


FIXTURE_VERSION = 1
FILES = {
    ".gitignore": "__pycache__/\n*.pyc\n",
    "README.md": """# Receipt summary activation fixture

This disposable Python application summarizes a CSV of receipt events. It uses
only the standard library. Run `python3 receipt_summary.py example.csv` or
`python3 -m unittest discover -s tests -v`.

Each row has `status` (paid, refunded, or void) and a nonnegative `amount` with at
most two decimal places. Paid events increase net receipts, refunds decrease
them, and void events do not affect totals or settled_count. Output is one JSON
object with paid, refunded, and net totals formatted to two decimal places, plus
settled_count (paid and refunded events).

Reported bug: a refund incorrectly increases net receipts. The included sample
must produce paid=21.35, refunded=3.40, net=17.95, settled_count=3. Fix the behavior
without weakening the acceptance tests. Keep the change bounded to this fixture.

Do not push or merge. hstack activation requires recording the loaded skill,
runtime, base/head commits, checks, and independent review evidence separately.
""",
    "example.csv": "status,amount\npaid,12.10\npaid,9.25\nrefunded,3.40\nvoid,99.00\n",
    "receipt_summary.py": '''"""Summarize settled receipts from a CSV file."""

import csv
from decimal import Decimal
import json
from pathlib import Path
import sys


def summarize(path):
    paid = Decimal("0.00")
    refunded = Decimal("0.00")
    settled_count = 0
    with Path(path).open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            amount = Decimal(row["amount"])
            if row["status"] == "paid":
                paid += amount
                settled_count += 1
            elif row["status"] == "refunded":
                refunded += amount
                settled_count += 1
            elif row["status"] != "void":
                raise ValueError("Unknown receipt status")
    return {
        "paid": format(paid, ".2f"),
        "refunded": format(refunded, ".2f"),
        "net": format(paid + refunded, ".2f"),
        "settled_count": settled_count,
    }


if __name__ == "__main__":
    print(json.dumps(summarize(sys.argv[1]), sort_keys=True))
''',
    "tests/test_receipts.py": '''"""Acceptance checks drive the real command-line application."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


APP = Path(__file__).resolve().parents[1] / "receipt_summary.py"


class ReceiptAcceptance(unittest.TestCase):
    def run_summary(self, rows):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "receipts.csv"
            source.write_text("status,amount\\n" + rows, encoding="utf-8")
            process = subprocess.run(
                [sys.executable, str(APP), str(source)],
                capture_output=True, text=True, check=True,
            )
            self.assertEqual(process.stderr, "")
            return json.loads(process.stdout)

    def test_customer_receipts_after_partial_refund(self):
        self.assertEqual(
            self.run_summary("paid,12.10\\npaid,9.25\\nrefunded,3.40\\nvoid,99.00\\n"),
            {"paid": "21.35", "refunded": "3.40", "net": "17.95", "settled_count": 3},
        )

    def test_full_refund_leaves_no_net_receipts(self):
        result = self.run_summary("paid,55.10\\nrefunded,55.10\\n")
        self.assertEqual(result["net"], "0.00")
        self.assertEqual(result["settled_count"], 2)

    def test_many_small_receipts_preserve_cents(self):
        result = self.run_summary("paid,0.01\\n" * 100 + "refunded,0.01\\n" * 3)
        self.assertEqual(result["net"], "0.97")
        self.assertEqual(result["settled_count"], 103)

    def test_empty_or_void_only_ledger_has_no_settled_receipts(self):
        expected = {"paid": "0.00", "refunded": "0.00", "net": "0.00", "settled_count": 0}
        for rows in ("", "void,999.99\\n"):
            with self.subTest(rows=rows):
                self.assertEqual(self.run_summary(rows), expected)


if __name__ == "__main__":
    unittest.main()
''',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--evidence", type=Path, help="Write baseline results outside the fixture")
    args = parser.parse_args()
    destination = args.destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        parser.error("destination must be absent or empty; existing work is never replaced")
    if args.evidence and args.evidence.resolve().is_relative_to(destination):
        parser.error("evidence must be outside the fixture to preserve a clean checkpoint")
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in FILES.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    environment = dict(os.environ, GIT_AUTHOR_NAME="hstack activation fixture",
                       GIT_AUTHOR_EMAIL="hstack-fixture@example.invalid",
                       GIT_COMMITTER_NAME="hstack activation fixture",
                       GIT_COMMITTER_EMAIL="hstack-fixture@example.invalid",
                       GIT_AUTHOR_DATE="2026-09-06T00:00:00+0000",
                       GIT_COMMITTER_DATE="2026-09-06T00:00:00+0000")
    def git(*arguments):
        return subprocess.run(["git", *arguments], cwd=destination, env=environment,
                              text=True, capture_output=True, check=True).stdout.strip()
    git("-c", "init.templateDir=", "init")
    git("symbolic-ref", "HEAD", "refs/heads/main")
    git("add", ".")
    git("-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", "commit", "-m", "Add receipt summary with reproducible refund defect")
    baseline = git("rev-parse", "HEAD")
    checks = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    result = subprocess.run(checks, cwd=destination, text=True, capture_output=True)
    evidence = {"fixture_version": FIXTURE_VERSION,
                "repo": str(destination), "base": baseline, "check_argv": checks,
                "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
                "clean_checkpoint": git("status", "--porcelain") == ""}
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    if result.returncode != 1 or "FAILED (failures=3)" not in result.stderr:
        raise SystemExit("Unexpected baseline: expected four tests with three refund failures")


if __name__ == "__main__":
    main()

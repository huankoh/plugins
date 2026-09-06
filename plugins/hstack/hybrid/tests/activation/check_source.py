#!/usr/bin/env python3
"""Snapshot a source checkout or verify it is unchanged after delegated work."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess


def snapshot(repo):
    def git(*arguments):
        return subprocess.check_output(["git", "-C", str(repo), *arguments])
    files = {}
    for raw in sorted(set(git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split(b"\0")) - {b""}):
        name = os.fsdecode(raw)
        path = repo / name
        if not path.exists() and not path.is_symlink():
            files[name] = {"missing": True}
            continue
        mode = path.lstat().st_mode
        payload = os.fsencode(os.readlink(path)) if stat.S_ISLNK(mode) else path.read_bytes()
        files[name] = {"sha256": hashlib.sha256(payload).hexdigest(), "mode": stat.S_IMODE(mode),
                       "symlink": stat.S_ISLNK(mode)}
    return {"head": git("rev-parse", "HEAD").decode().strip(),
            "status": git("status", "--porcelain=v1", "--untracked-files=all").decode(),
            "index_sha256": hashlib.sha256(git("ls-files", "--stage", "-z")).hexdigest(), "files": files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--save", type=Path)
    group.add_argument("--compare", type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.save and args.save.resolve().is_relative_to(repo):
        parser.error("save the snapshot outside the source checkout")
    actual = snapshot(repo)
    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        args.save.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"saved": str(args.save), "head": actual["head"], "files": len(actual["files"])}))
    else:
        expected = json.loads(args.compare.read_text(encoding="utf-8"))
        changed = [key for key in actual if actual[key] != expected.get(key)]
        print(json.dumps({"source_unchanged": not changed, "changed_sections": changed, "head": actual["head"]}))
        raise SystemExit(bool(changed))


if __name__ == "__main__":
    main()

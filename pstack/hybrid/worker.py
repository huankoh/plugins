#!/usr/bin/env python3
"""Process supervision for subscription-authenticated hstack Codex jobs."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(os.environ.get("HSTACK_CODEX_DATA", "~/.local/share/hstack")).expanduser().resolve()


def resolve_binary():
    preferred = os.environ.get("HSTACK_CODEX_BINARY") or shutil.which("codex")
    if preferred:
        return preferred
    prefix = Path(os.environ.get("HSTACK_CODEX_PREFIX", "~/.local/share/hstack-codex")).expanduser()
    installed = prefix / "node_modules/.bin/codex"
    if installed.is_file() and os.access(installed, os.X_OK):
        return str(installed)
    app = Path("/Applications/ChatGPT.app/Contents/Resources/codex")
    return str(app) if app.exists() else "codex"


BINARY = resolve_binary()
ACTIVE = {"starting", "running", "orphaned"}
PUBLIC = ("id", "cwd", "model", "effort", "sandbox", "timeout_seconds", "status", "created_at", "finished_at", "exit_code", "error")


def emit(value):
    print(json.dumps(value, ensure_ascii=False))


def save(path, value):
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temp.open("x") as stream:
        json.dump(value, stream, ensure_ascii=False)
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)


def read(path):
    return json.loads(path.read_text())


def environment():
    env = os.environ.copy()
    for name in ("OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL", "OPENAI_API_BASE", "CODEX_BASE_URL"):
        env.pop(name, None)
    return env


def auth_status():
    result = subprocess.run([BINARY, "-c", 'model_provider="openai"', "login", "status"],
                            capture_output=True, text=True, timeout=15, env=environment())
    text = (result.stdout + result.stderr).lower()
    return "chatgpt" if result.returncode == 0 and "chatgpt" in text else "unavailable"


def models():
    path = Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser() / "models_cache.json"
    data = read(path) if path.exists() else {}
    return {"source": str(path), "verified_live": False, "fetched_at": data.get("fetched_at"),
            "effort_note": "ultra omitted; this worker does not implement orchestration-mode semantics",
            "models": [{"model": m["slug"], "name": m.get("display_name", m["slug"]),
                        "efforts": [r["effort"] for r in m.get("supported_reasoning_levels", []) if r["effort"] != "ultra"]}
                       for m in data.get("models", []) if m.get("visibility") == "list"]}


def job_path(job_id):
    if not re.fullmatch(r"[0-9a-f]{32}", job_id):
        raise ValueError("Invalid job ID")
    return ROOT / "jobs" / job_id


def lock_path(cwd):
    return ROOT / "locks" / (hashlib.sha256(cwd.encode()).hexdigest() + ".lock")


def acquire(cwd):
    path = lock_path(cwd)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        return None
    return fd


def birth(pid):
    result = subprocess.run(["/bin/ps", "-p", str(pid), "-o", "lstart="],
                            capture_output=True, text=True, timeout=5)
    return result.stdout.strip() if result.returncode == 0 else None


def snapshot(job_id):
    directory = job_path(job_id)
    state = read(directory / "state.json")
    if state["status"] in ACTIVE:
        fd = acquire(state["cwd"])
        if fd is not None:
            try:
                state = read(directory / "state.json")
                if state["status"] in ACTIVE:
                    state.update(status="interrupted", finished_at=time.time(),
                                 error="Worker ownership ended without a completion record; inspect the workspace before retrying")
                    save(directory / "state.json", state)
            finally:
                os.close(fd)
        elif lock_path(state["cwd"]).read_text() != job_id:
            state.update(status="interrupted", error="Working directory is now owned by another job")
        elif state["status"] != "starting" and birth(state["supervisor_pid"]) != state["supervisor_birth"]:
            state.update(status="orphaned", error="Supervisor ended; the worker lock is still held. No PID will be signalled")
    result = {key: state[key] for key in PUBLIC if key in state}
    result["cancel_requested"] = (directory / "cancel.request").exists()
    result["result_available"] = (directory / "result.txt").exists()
    return result


def submit(args):
    cwd = Path(args.cwd)
    if not cwd.is_absolute() or not cwd.is_dir():
        raise ValueError("--cwd must be an existing absolute directory")
    cwd = str(cwd.resolve())
    if args.model and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", args.model):
        raise ValueError("--model must be an explicit native Codex model slug")
    if args.effort and not args.model:
        raise ValueError("--effort requires an explicit --model")
    if args.effort:
        catalog = {m["model"]: m for m in models()["models"]}
        if args.model not in catalog or args.effort not in catalog[args.model]["efforts"]:
            raise ValueError("Requested reasoning effort is not supported by this model in the account cache")
    if not 1 <= args.timeout_seconds <= 21600:
        raise ValueError("--timeout-seconds must be between 1 and 21600")
    task = json.load(sys.stdin) if args.task == "-" else read(Path(args.task))
    if not isinstance(task, dict) or set(task) != {"prompt"} or not isinstance(task["prompt"], str) or not task["prompt"].strip():
        raise ValueError('Task JSON must contain exactly one nonempty string field: "prompt"')
    if auth_status() != "chatgpt":
        raise ValueError("ChatGPT login required. Run codex login; no API-key fallback is allowed")
    fd = acquire(cwd)
    if fd is None:
        raise ValueError("Working directory already has an active worker; use a separate worktree")
    job_id = getattr(args, "job_id", None) or uuid.uuid4().hex
    directory = job_path(job_id)
    directory.mkdir(parents=True, mode=0o700)
    state = dict(id=job_id, cwd=cwd, model=args.model, effort=args.effort,
                 sandbox=args.sandbox, timeout_seconds=args.timeout_seconds, status="starting", created_at=time.time())
    try:
        os.ftruncate(fd, 0)
        os.write(fd, job_id.encode())
        os.fsync(fd)
        save(directory / "task.json", task)
        save(directory / "state.json", state)
        with (directory / "supervisor.log").open("ab") as log:
            subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "_run", job_id, str(fd)],
                             cwd=directory, env=environment(), stdin=subprocess.DEVNULL,
                             stdout=log, stderr=log, start_new_session=True, pass_fds=(fd,))
    except Exception:
        state.update(status="failed", error="Could not launch supervisor", finished_at=time.time())
        save(directory / "state.json", state)
        raise
    finally:
        os.close(fd)
    return {"id": job_id, "status": "starting", "cwd": cwd, "model": args.model, "sandbox": args.sandbox}


def command(state, directory):
    args = [BINARY, "exec", "--json", "-C", state["cwd"],
            "-s", state["sandbox"], "--output-last-message", str(directory / "result.txt"),
            "--output-schema", str(Path(__file__).with_name("report.schema.json")), "-c", 'model_provider="openai"',
            "-c", 'forced_login_method="chatgpt"', "-c", 'approval_policy="never"']
    if state["model"]:
        args += ["-m", state["model"]]
    if state["effort"]:
        args += ["-c", 'model_reasoning_effort=' + json.dumps(state["effort"])]
    return args + ["-"]


def stop_owned_child(child):
    if child.poll() is not None:
        return
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        child.wait(timeout=2)
        return
    # Keep the child unreaped so its process-group ID cannot be recycled here.
    time.sleep(1)
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except PermissionError:
        # Darwin returns EPERM for a process group containing only zombies.
        child.wait(timeout=2)
        return
    child.wait()


def supervise(job_id, fd):
    directory = job_path(job_id)
    state = read(directory / "state.json")
    if state["status"] != "starting" or os.fstat(fd).st_ino != lock_path(state["cwd"]).stat().st_ino:
        raise ValueError("Invalid supervisor handoff")
    cancelled = False
    timed_out = False
    child = None

    def interrupt(_signum, _frame):
        nonlocal cancelled
        cancelled = True

    signal.signal(signal.SIGTERM, interrupt)
    signal.signal(signal.SIGINT, interrupt)
    try:
        state.update(status="running", supervisor_pid=os.getpid(), supervisor_birth=birth(os.getpid()))
        save(directory / "state.json", state)
        prompt = read(directory / "task.json")["prompt"]
        (directory / "prompt.txt").write_text(prompt)
        with (directory / "prompt.txt").open("rb") as source, (directory / "events.jsonl").open("ab") as out, (directory / "stderr.log").open("ab") as err:
            if not (directory / "cancel.request").exists():
                child = subprocess.Popen(command(state, directory), cwd=state["cwd"], env=environment(),
                                         stdin=source, stdout=out, stderr=err,
                                         start_new_session=True, pass_fds=(fd,))
                deadline = time.monotonic() + state["timeout_seconds"]
                while child.poll() is None:
                    if cancelled or (directory / "cancel.request").exists():
                        cancelled = True
                        stop_owned_child(child)
                        break
                    if time.monotonic() >= deadline:
                        timed_out = True
                        stop_owned_child(child)
                        break
                    time.sleep(0.2)
            else:
                cancelled = True
        code = child.returncode if child else None
        state.update(status="cancelled" if cancelled else "succeeded" if code == 0 and not timed_out else "failed", exit_code=code)
        if (code or timed_out) and not cancelled:
            state["error"] = "Job time limit reached" if timed_out else "Codex exited unsuccessfully; inspect the private job stderr log"
    except Exception as exc:
        if child:
            stop_owned_child(child)
        state.update(status="failed", error="Supervisor error: " + type(exc).__name__)
    finally:
        state["finished_at"] = time.time()
        save(directory / "state.json", state)
        os.close(fd)


def main():
    os.umask(0o077)
    if len(sys.argv) == 4 and sys.argv[1] == "_run":
        supervise(sys.argv[2], int(sys.argv[3]))
        return
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("doctor")
    commands.add_parser("models")
    create = commands.add_parser("submit")
    create.add_argument("--cwd", required=True)
    create.add_argument("--model")
    create.add_argument("--task", required=True, help='JSON file or - for stdin; {"prompt":"..."}')
    create.add_argument("--sandbox", choices=["read-only", "workspace-write"], default="read-only")
    create.add_argument("--effort", choices=["minimal", "low", "medium", "high", "xhigh", "max"])
    create.add_argument("--timeout-seconds", type=int, default=1800)
    for name in ("status", "result", "cancel"):
        commands.add_parser(name).add_argument("id")
    args = parser.parse_args()
    if args.action == "models":
        emit(models())
    elif args.action == "doctor":
        version = subprocess.run([BINARY, "--version"], capture_output=True, text=True, timeout=10).stdout.strip()
        auth = auth_status()
        emit({"binary": BINARY, "version": version, "auth": auth, "ready": auth == "chatgpt",
              "data_root": str(ROOT), "model_source": "account cache; not live-verified"})
        if auth != "chatgpt":
            sys.exit(1)
    elif args.action == "submit":
        emit(submit(args))
    else:
        info = snapshot(args.id)
        directory = job_path(args.id)
        if args.action == "cancel" and info["status"] in ACTIVE:
            if info["status"] == "orphaned":
                raise ValueError(info["error"])
            (directory / "cancel.request").touch(mode=0o600)
            info["cancel_requested"] = True
        if args.action == "result":
            if info["status"] in ACTIVE:
                raise ValueError("Job has not finished; use status")
            info["result"] = (directory / "result.txt").read_text() if info["result_available"] else None
            info["job_directory"] = str(directory)
        emit(info)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        emit({"error": str(error) if isinstance(error, ValueError) else type(error).__name__})
        sys.exit(1)

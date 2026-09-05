import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest

from veil import ipc
from veil.daemon import Session, _handle


def _quiet(monkeypatch) -> None:
    monkeypatch.setattr("veil.daemon.log.record", lambda *a, **k: None)
    monkeypatch.setattr("veil.daemon.save_vault", lambda *a, **k: None)


def _session(monkeypatch, secrets=None, idle=60) -> Session:
    _quiet(monkeypatch)
    payload = {"demo": "s3cret"} if secrets is None else secrets
    return Session("pw", {"secrets": payload}, idle_seconds=idle)


def test_ping_and_unknown_op(monkeypatch):
    session = _session(monkeypatch)
    ping = _handle(session, {"op": "ping"})
    assert ping["ok"] is True
    assert ping["pid"] == os.getpid()
    bad = _handle(session, {"op": "get"})
    assert bad["ok"] is False
    session.wipe()


def test_lock_sets_stopping(monkeypatch):
    session = _session(monkeypatch)
    assert _handle(session, {"op": "lock"})["ok"] is True
    assert session.stopping is True
    session.wipe()


def test_set_rejects_empty(monkeypatch):
    session = _session(monkeypatch)
    reply = _handle(session, {"op": "set", "name": "", "value": "x"})
    assert reply["ok"] is False
    session.wipe()


def test_set_then_list_has_no_values(monkeypatch):
    session = _session(monkeypatch, secrets={})
    assert _handle(session, {"op": "set", "name": "k", "value": "hidden"})["ok"] is True
    listed = _handle(session, {"op": "list"})
    assert listed["names"] == ["k"]
    assert "hidden" not in str(listed)
    session.wipe()


def test_wipe_zeros_buffers(monkeypatch):
    session = _session(monkeypatch)
    assert session.secrets()["demo"] == "s3cret"
    session.wipe()
    assert set(session._secrets.snapshot()) == {0}
    assert set(session._passphrase.snapshot()) == {0}


def test_resolve_does_not_echo_unknown_values(monkeypatch):
    session = _session(monkeypatch)
    denied = _handle(session, {"op": "resolve", "names": ["nope"], "command": ["x"]})
    assert denied["ok"] is False
    assert "s3cret" not in str(denied)
    session.wipe()


def _daemon_env(tmp_path: Path) -> tuple[dict[str, str], str]:
    pipe = rf"\\.\pipe\veil-test-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    if os.name != "nt":
        pipe = str(tmp_path / "veil.sock")
    env = os.environ.copy()
    env["VEIL_HOME"] = str(tmp_path)
    env["VEIL_PIPE"] = pipe
    return env, pipe


def _spawn_daemon(tmp_path: Path, *, idle: int = 30) -> tuple[subprocess.Popen, dict[str, str]]:
    env, _pipe = _daemon_env(tmp_path)
    proc = subprocess.Popen(
        [sys.executable, "-m", "veil.daemon"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    assert proc.stdin is not None and proc.stdout is not None
    bootstrap = {"passphrase": "pw", "secrets": {"demo": "s3cret"}, "idle_seconds": idle}
    proc.stdin.write((json.dumps(bootstrap) + "\n").encode("utf-8"))
    proc.stdin.close()
    ready = proc.stdout.readline()
    if b"ready" not in ready:
        err = proc.stderr.read() if proc.stderr else b""
        proc.kill()
        raise AssertionError(f"daemon failed: {ready!r} {err!r}")
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline and not (tmp_path / "session.key").exists():
        time.sleep(0.05)
    if not (tmp_path / "session.key").exists():
        proc.kill()
        raise AssertionError("daemon wrote no session key")
    return proc, env


def _ask(env: dict[str, str], message: dict) -> dict:
    monkey_home = env["VEIL_HOME"]
    monkey_pipe = env["VEIL_PIPE"]
    old_home = os.environ.get("VEIL_HOME")
    old_pipe = os.environ.get("VEIL_PIPE")
    os.environ["VEIL_HOME"] = monkey_home
    os.environ["VEIL_PIPE"] = monkey_pipe
    try:
        conn = ipc.connect()
        ipc.send(conn, message)
        reply = ipc.recv(conn)
        conn.close()
        return reply
    finally:
        if old_home is None:
            os.environ.pop("VEIL_HOME", None)
        else:
            os.environ["VEIL_HOME"] = old_home
        if old_pipe is None:
            os.environ.pop("VEIL_PIPE", None)
        else:
            os.environ["VEIL_PIPE"] = old_pipe


def test_daemon_process_ping_resolve_lock(tmp_path):
    proc, env = _spawn_daemon(tmp_path)
    try:
        ping = _ask(env, {"op": "ping"})
        assert ping["ok"] is True
        granted = _ask(env, {"op": "resolve", "names": ["demo"], "command": ["echo"]})
        assert granted["ok"] is True
        assert granted["secrets"]["DEMO"] == "s3cret"
        listed = _ask(env, {"op": "list"})
        assert listed["names"] == ["demo"]
        assert "s3cret" not in str(listed)
        assert _ask(env, {"op": "lock"})["ok"] is True
        proc.wait(timeout=5)
        assert proc.returncode == 0
        assert not (tmp_path / "session.key").exists()
        assert not (tmp_path / "daemon.pid").exists()
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=3)


def test_daemon_process_idle_timeout(tmp_path):
    proc, env = _spawn_daemon(tmp_path, idle=1)
    try:
        proc.wait(timeout=8)
        assert proc.returncode == 0
        assert not (tmp_path / "session.key").exists()
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=3)


def test_daemon_process_rejects_wrong_key(tmp_path):
    from multiprocessing.connection import Client

    proc, env = _spawn_daemon(tmp_path)
    try:
        family = "AF_PIPE" if os.name == "nt" else "AF_UNIX"
        from multiprocessing.context import AuthenticationError

        with pytest.raises((OSError, EOFError, ConnectionError, AuthenticationError)):
            Client(env["VEIL_PIPE"], family=family, authkey=b"x" * 32)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=3)

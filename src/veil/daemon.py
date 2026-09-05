# Copyright (C) 2026 Veil contributors
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import json
import os
import signal
import sys
import threading
import time
from typing import Any

from veil import ipc, log
from veil.memory import LockedBuffer
from veil.paths import pid_path, vault_path
from veil.vault import env_name, save_vault

DEFAULT_IDLE_SECONDS = 30 * 60


class Session:
    def __init__(self, passphrase: str, payload: dict, idle_seconds: int = DEFAULT_IDLE_SECONDS):
        self._passphrase = LockedBuffer(passphrase.encode("utf-8"))
        self._secrets = LockedBuffer(json.dumps(payload.get("secrets", {})).encode("utf-8"))
        self.idle_seconds = idle_seconds
        self.last_activity = time.monotonic()
        self.stopping = False

    def touch(self) -> None:
        self.last_activity = time.monotonic()

    def secrets(self) -> dict[str, str]:
        raw = self._secrets.snapshot()
        data = json.loads(raw.decode("utf-8"))
        return {str(k): str(v) for k, v in data.items()}

    def set_secret(self, name: str, value: str) -> None:
        current = self.secrets()
        current[name] = value
        self._secrets.replace(json.dumps(current).encode("utf-8"))
        passphrase = self._passphrase.snapshot().decode("utf-8")
        save_vault(vault_path(), {"secrets": current}, passphrase)

    def unset_secret(self, name: str) -> bool:
        current = self.secrets()
        if name not in current:
            return False
        del current[name]
        self._secrets.replace(json.dumps(current).encode("utf-8"))
        passphrase = self._passphrase.snapshot().decode("utf-8")
        save_vault(vault_path(), {"secrets": current}, passphrase)
        return True

    def wipe(self) -> None:
        self._passphrase.wipe()
        self._secrets.wipe()


def _write_pid() -> None:
    pid_path().write_text(str(os.getpid()), encoding="utf-8")


def _clear_runtime() -> None:
    if pid_path().exists():
        pid_path().unlink()
    ipc.clear_session_key()


def _handle(session: Session, message: dict[str, Any]) -> dict[str, Any]:
    session.touch()
    op = message.get("op")
    if op == "ping":
        return {"ok": True, "pid": os.getpid()}
    if op == "list":
        return {"ok": True, "names": sorted(session.secrets())}
    if op == "set":
        name = str(message.get("name") or "")
        value = str(message.get("value") or "")
        if not name or not value:
            return {"ok": False, "error": "name and value are required"}
        session.set_secret(name, value)
        log.record("set", names=[name], result="stored")
        return {"ok": True}
    if op == "unset":
        name = str(message.get("name") or "")
        if not name:
            return {"ok": False, "error": "name is required"}
        if not session.unset_secret(name):
            log.record("unset", names=[name], result="missing")
            return {"ok": False, "error": f"unknown secret: {name}"}
        log.record("unset", names=[name], result="removed")
        return {"ok": True}
    if op == "resolve":
        requested = [str(n) for n in message.get("names") or []]
        secrets = session.secrets()
        missing = [n for n in requested if n not in secrets]
        if missing:
            log.record("run", names=requested, command=message.get("command") or [], result="denied")
            return {"ok": False, "error": f"unknown secrets: {', '.join(missing)}"}
        resolved = {env_name(n): secrets[n] for n in requested}
        log.record("run", names=requested, command=message.get("command") or [], result="granted")
        return {"ok": True, "secrets": resolved}
    if op == "lock":
        session.stopping = True
        return {"ok": True}
    return {"ok": False, "error": f"unknown op: {op}"}


def serve(session: Session) -> int:
    authkey = ipc.write_session_key()
    listener = ipc.listen(authkey)
    _write_pid()

    def shutdown(*_args: object) -> None:
        session.stopping = True

    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

    def accept_loop() -> None:
        while not session.stopping:
            try:
                conn = listener.accept()
            except (OSError, EOFError):
                break
            try:
                message = ipc.recv(conn)
                reply = _handle(session, message)
                ipc.send(conn, reply)
            except Exception as exc:
                try:
                    ipc.send(conn, {"ok": False, "error": str(exc)})
                except Exception:
                    pass
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

    worker = threading.Thread(target=accept_loop, daemon=True)
    worker.start()
    try:
        while not session.stopping:
            time.sleep(0.25)
            if time.monotonic() - session.last_activity > session.idle_seconds:
                log.record("lock", result="idle-timeout")
                session.stopping = True
    finally:
        try:
            listener.close()
        except Exception:
            pass
        session.wipe()
        _clear_runtime()
    return 0


def main() -> int:
    raw = sys.stdin.readline()
    if not raw:
        return 2
    bootstrap = json.loads(raw)
    session = Session(
        passphrase=bootstrap["passphrase"],
        payload={"secrets": bootstrap.get("secrets") or {}},
        idle_seconds=int(bootstrap.get("idle_seconds") or DEFAULT_IDLE_SECONDS),
    )
    sys.stdin.close()
    print("ready", flush=True)
    return serve(session)


if __name__ == "__main__":
    raise SystemExit(main())

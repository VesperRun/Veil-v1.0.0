# Copyright (C) 2026 Veil contributors
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import json
import os
import time
from multiprocessing.connection import Client, Listener
from typing import Any

from veil.paths import data_dir, ensure_data_dir, ipc_address, ipc_family


def session_key_path():
    return data_dir() / "session.key"


def write_session_key() -> bytes:
    ensure_data_dir()
    key = os.urandom(32)
    path = session_key_path()
    path.write_bytes(key)
    if os.name != "nt":
        os.chmod(path, 0o600)
    return key


def read_session_key() -> bytes:
    path = session_key_path()
    if not path.exists():
        raise FileNotFoundError("veil is locked")
    return path.read_bytes()


def clear_session_key() -> None:
    path = session_key_path()
    if path.exists():
        path.unlink()


def connect(retries: int = 40, delay: float = 0.05):
    last: Exception | None = None
    key = read_session_key()
    for _ in range(retries):
        try:
            return Client(ipc_address(), family=ipc_family(), authkey=key)
        except (EOFError, OSError, ConnectionRefusedError) as exc:
            last = exc
            time.sleep(delay)
    raise ConnectionError("veil daemon is not reachable") from last


def listen(authkey: bytes) -> Listener:
    address = ipc_address()
    if ipc_family() == "AF_UNIX":
        from pathlib import Path

        sock = Path(address)
        if sock.exists():
            sock.unlink()
    return Listener(address, family=ipc_family(), authkey=authkey)


def send(conn, message: dict[str, Any]) -> None:
    conn.send_bytes(json.dumps(message).encode("utf-8"))


def recv(conn) -> dict[str, Any]:
    raw = conn.recv_bytes()
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("invalid ipc payload")
    return payload

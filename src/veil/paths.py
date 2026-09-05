# Copyright (C) 2026 Veil contributors
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import os
from pathlib import Path


def data_dir() -> Path:
    override = os.environ.get("VEIL_HOME")
    if override:
        return Path(override)
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "veil"
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "veil"
    return Path.home() / ".local" / "share" / "veil"


def ensure_data_dir() -> Path:
    path = data_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def vault_path() -> Path:
    return data_dir() / "vault"


def log_path() -> Path:
    return data_dir() / "access.log"


def pid_path() -> Path:
    return data_dir() / "daemon.pid"


def ipc_address() -> str:
    override = os.environ.get("VEIL_PIPE")
    if override:
        return override
    if os.name == "nt":
        user = os.environ.get("USERNAME") or "user"
        return rf"\\.\pipe\veil-{user}"
    return str(data_dir() / "veil.sock")


def ipc_family() -> str:
    return "AF_PIPE" if os.name == "nt" else "AF_UNIX"


def session_key_path() -> Path:
    return data_dir() / "session.key"


def artifacts() -> list[Path]:
    items = [vault_path(), log_path(), pid_path(), session_key_path()]
    if ipc_family() == "AF_UNIX":
        items.append(Path(ipc_address()))
    return items

# Copyright (C) 2026 Veil contributors
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import argparse
import ctypes
import getpass
import json
import os
import subprocess
import sys
from typing import Sequence

from veil import ipc, log
from veil.daemon import DEFAULT_IDLE_SECONDS
from veil.paths import pid_path, vault_path
from veil.vault import WrongPassphrase, create_vault, env_name, load_vault, save_vault

CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NO_WINDOW = 0x08000000


def _prompt_passphrase(confirm: bool = False) -> str:
    first = getpass.getpass("Passphrase: ")
    if not first:
        raise SystemExit("passphrase cannot be empty")
    if confirm:
        second = getpass.getpass("Confirm passphrase: ")
        if first != second:
            raise SystemExit("passphrases do not match")
    return first


def _pid_exists(pid: int) -> bool:
    if os.name == "nt":
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _daemon_alive() -> bool:
    if not pid_path().exists():
        return False
    try:
        pid = int(pid_path().read_text(encoding="utf-8").strip())
    except ValueError:
        return False
    return _pid_exists(pid)


def _request(message: dict) -> dict:
    if not _daemon_alive():
        raise SystemExit("veil is locked — run `veil unlock` first")
    try:
        conn = ipc.connect()
    except (ConnectionError, FileNotFoundError) as exc:
        raise SystemExit(f"veil is locked — {exc}") from exc
    try:
        ipc.send(conn, message)
        reply = ipc.recv(conn)
    finally:
        conn.close()
    return reply


def cmd_init(_args: argparse.Namespace) -> int:
    path = vault_path()
    if path.exists():
        raise SystemExit(f"vault already exists at {path}")
    passphrase = _prompt_passphrase(confirm=True)
    create_vault(path, passphrase)
    print(f"Created vault at {path}")
    return 0


def cmd_unlock(args: argparse.Namespace) -> int:
    if _daemon_alive():
        print("Veil is already unlocked")
        return 0
    path = vault_path()
    if not path.exists():
        raise SystemExit("no vault — run `veil init` first")
    passphrase = _prompt_passphrase()
    try:
        payload = load_vault(path, passphrase)
    except WrongPassphrase:
        raise SystemExit("wrong passphrase")
    creationflags = 0
    if os.name == "nt":
        creationflags = CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
    proc = subprocess.Popen(
        [sys.executable, "-m", "veil.daemon"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )
    assert proc.stdin is not None and proc.stdout is not None
    bootstrap = {
        "passphrase": passphrase,
        "secrets": payload.get("secrets") or {},
        "idle_seconds": args.idle,
    }
    proc.stdin.write((json.dumps(bootstrap) + "\n").encode("utf-8"))
    proc.stdin.close()
    ready = proc.stdout.readline()
    proc.stdout.close()
    if b"ready" not in ready:
        raise SystemExit("failed to start veil session")
    print("Unlocked")
    return 0


def cmd_lock(_args: argparse.Namespace) -> int:
    if not _daemon_alive():
        print("Veil is already locked")
        return 0
    try:
        _request({"op": "lock"})
    except SystemExit:
        pass
    print("Locked")
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    name = args.name
    value = getpass.getpass(f"Value for {name}: ")
    if not value:
        raise SystemExit("value cannot be empty")
    if _daemon_alive():
        reply = _request({"op": "set", "name": name, "value": value})
        if not reply.get("ok"):
            raise SystemExit(reply.get("error") or "set failed")
        print(f"Stored {name}")
        return 0
    path = vault_path()
    if not path.exists():
        raise SystemExit("no vault — run `veil init` first")
    passphrase = _prompt_passphrase()
    try:
        payload = load_vault(path, passphrase)
    except WrongPassphrase:
        raise SystemExit("wrong passphrase")
    payload["secrets"][name] = value
    save_vault(path, payload, passphrase)
    log.record("set", names=[name], result="stored")
    print(f"Stored {name}")
    return 0


def cmd_list(_args: argparse.Namespace) -> int:
    if _daemon_alive():
        reply = _request({"op": "list"})
        names = reply.get("names") or []
    else:
        path = vault_path()
        if not path.exists():
            raise SystemExit("no vault — run `veil init` first")
        passphrase = _prompt_passphrase()
        try:
            payload = load_vault(path, passphrase)
        except WrongPassphrase:
            raise SystemExit("wrong passphrase")
        names = sorted(payload["secrets"])
    if not names:
        print("(empty)")
        return 0
    for name in names:
        print(f"{name}  ->  {env_name(name)}")
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    path = vault_path()
    print(f"vault:  {path}{'  (missing)' if not path.exists() else ''}")
    print(f"session: {'unlocked' if _daemon_alive() else 'locked'}")
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    entries = log.read_entries(limit=args.limit)
    if not entries:
        print("(no entries)")
        return 0
    for entry in entries:
        names = ",".join(entry.get("names") or []) or "-"
        command = " ".join(entry.get("command") or [])
        extra = f"  {command}" if command else ""
        print(f"{entry.get('ts')}  {entry.get('action')}  {entry.get('result')}  {names}{extra}")
    return 0


def _wipe_env(env: dict[str, str], keys: Sequence[str]) -> None:
    for key in keys:
        if key in env:
            env[key] = "\x00" * len(env[key])
            del env[key]


def cmd_run(args: argparse.Namespace) -> int:
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SystemExit("usage: veil run --with NAME -- <command>")
    names = args.with_names
    reply = _request({"op": "resolve", "names": names, "command": command})
    if not reply.get("ok"):
        raise SystemExit(reply.get("error") or "denied")
    secrets = reply.get("secrets") or {}
    env = os.environ.copy()
    injected = []
    for key, value in secrets.items():
        env[key] = value
        injected.append(key)
    try:
        completed = subprocess.run(command, env=env, check=False)
        return int(completed.returncode)
    finally:
        _wipe_env(env, injected)
        for value in secrets.values():
            del value
        secrets.clear()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="veil",
        description="Local agent credential broker. The agent can use the key; it cannot see the key.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="create a local encrypted vault")
    p_init.set_defaults(func=cmd_init)

    p_unlock = sub.add_parser("unlock", help="open a session (holds secrets in memory)")
    p_unlock.add_argument("--idle", type=int, default=DEFAULT_IDLE_SECONDS, help="idle lock seconds")
    p_unlock.set_defaults(func=cmd_unlock)

    p_lock = sub.add_parser("lock", help="wipe memory and close the session")
    p_lock.set_defaults(func=cmd_lock)

    p_set = sub.add_parser("set", help="store a secret (value is prompted, never argv)")
    p_set.add_argument("name")
    p_set.set_defaults(func=cmd_set)

    p_list = sub.add_parser("list", help="list secret names only")
    p_list.set_defaults(func=cmd_list)

    p_status = sub.add_parser("status", help="show vault path and session state")
    p_status.set_defaults(func=cmd_status)

    p_log = sub.add_parser("log", help="show local access log (no secret values)")
    p_log.add_argument("--limit", type=int, default=50)
    p_log.set_defaults(func=cmd_log)

    p_run = sub.add_parser("run", help="run a command with named secrets in its environment")
    p_run.add_argument("--with", dest="with_names", action="append", required=True, metavar="NAME")
    p_run.add_argument("command", nargs=argparse.REMAINDER)
    p_run.set_defaults(func=cmd_run)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)

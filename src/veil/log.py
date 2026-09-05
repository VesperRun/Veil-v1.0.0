# Copyright (C) 2026 Veil contributors
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from veil.paths import ensure_data_dir, log_path


def record(action: str, *, names: list[str] | None = None, command: list[str] | None = None, result: str) -> None:
    ensure_data_dir()
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "action": action,
        "names": names or [],
        "command": command or [],
        "result": result,
    }
    with log_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, separators=(",", ":")) + "\n")


def read_entries(path: Path | None = None, limit: int = 50) -> list[dict]:
    target = path or log_path()
    if not target.exists():
        return []
    lines = target.read_text(encoding="utf-8").splitlines()
    entries = []
    for line in lines[-limit:]:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries

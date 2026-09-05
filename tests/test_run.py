import subprocess
import sys
from pathlib import Path

from veil.cli import cmd_run


class _Args:
    def __init__(self, names, command):
        self.with_names = names
        self.command = command


def test_run_injects_into_child_only(monkeypatch, tmp_path):
    secret = "shh-not-from-veil-itself"
    out = tmp_path / "child.txt"

    def fake_request(message):
        assert message["op"] == "resolve"
        assert message["names"] == ["demo"]
        return {"ok": True, "secrets": {"DEMO": secret}}

    monkeypatch.setattr("veil.cli._request", fake_request)
    child = Path(__file__).parent / "child_echo.py"
    code = cmd_run(_Args(["demo"], [sys.executable, str(child), "DEMO", str(out)]))
    assert code == 0
    assert out.read_text(encoding="utf-8") == secret


def test_run_does_not_put_secret_in_parent_env(monkeypatch):
    def fake_request(_message):
        return {"ok": True, "secrets": {"DEMO": "child-only"}}

    monkeypatch.setattr("veil.cli._request", fake_request)
    child = Path(__file__).parent / "child_echo.py"
    cmd_run(_Args(["demo"], [sys.executable, str(child), "DEMO"]))
    assert os_get("DEMO") is None


def os_get(name: str):
    import os

    return os.environ.get(name)

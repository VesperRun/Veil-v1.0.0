from pathlib import Path

from veil import log


def test_record_has_no_secret_values(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(log, "log_path", lambda: tmp_path / "access.log")
    monkeypatch.setattr(log, "ensure_data_dir", lambda: tmp_path)
    log.record("run", names=["openai"], command=["python", "app.py"], result="granted")
    text = (tmp_path / "access.log").read_text(encoding="utf-8")
    assert "openai" in text
    assert "sk-" not in text
    entries = log.read_entries(tmp_path / "access.log")
    assert entries[0]["result"] == "granted"
    assert "secrets" not in entries[0]

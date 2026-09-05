from veil.daemon import Session, _handle


def test_resolve_maps_to_env_and_hides_missing(monkeypatch):
    monkeypatch.setattr("veil.daemon.log.record", lambda *a, **k: None)
    session = Session("pw", {"secrets": {"openai": "sk-test"}}, idle_seconds=60)
    granted = _handle(session, {"op": "resolve", "names": ["openai"], "command": ["python"]})
    assert granted["ok"] is True
    assert granted["secrets"] == {"OPENAI": "sk-test"}
    denied = _handle(session, {"op": "resolve", "names": ["missing"]})
    assert denied["ok"] is False
    session.wipe()


def test_list_names_only(monkeypatch):
    monkeypatch.setattr("veil.daemon.log.record", lambda *a, **k: None)
    session = Session("pw", {"secrets": {"openai": "sk-test"}}, idle_seconds=60)
    reply = _handle(session, {"op": "list"})
    assert reply["names"] == ["openai"]
    session.wipe()

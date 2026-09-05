from veil.cli import cmd_erase, cmd_explain, main


class _Args:
    def __init__(self, yes=False):
        self.yes = yes


def test_bare_veil_states_the_job(capsys):
    assert main([]) == 0
    text = capsys.readouterr().out
    assert "one child command" in text
    assert "veil explain" in text


def test_explain_declares_no_network_and_no_ai(capsys):
    assert cmd_explain(_Args()) == 0
    text = capsys.readouterr().out
    assert "not an AI system" in text
    assert "does not call a model" in text
    assert "does not wrap this product" in text
    assert "There is no AI interaction alert" in text
    assert "No surveillance" in text
    assert "You approve every change" in text


def test_erase_requires_yes():
    try:
        cmd_erase(_Args(yes=False))
    except SystemExit as exc:
        assert "--yes" in str(exc)
    else:
        raise AssertionError("erase without --yes must fail")


def test_erase_removes_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr("veil.cli.artifacts", lambda: [tmp_path / "vault", tmp_path / "access.log"])
    monkeypatch.setattr("veil.cli._daemon_alive", lambda: False)
    vault = tmp_path / "vault"
    log = tmp_path / "access.log"
    vault.write_text("x", encoding="utf-8")
    log.write_text("y", encoding="utf-8")
    assert cmd_erase(_Args(yes=True)) == 0
    assert not vault.exists()
    assert not log.exists()

from pathlib import Path

import pytest

from veil.vault import (
    KdfParams,
    WrongPassphrase,
    create_vault,
    decrypt_payload,
    encrypt_payload,
    env_name,
    load_vault,
    save_vault,
)

FAST = KdfParams(iterations=1, memory_kib=8 * 1024, lanes=1)


def test_round_trip():
    payload = {"secrets": {"openai": "sk-test"}}
    blob = encrypt_payload(payload, "secret", FAST)
    assert decrypt_payload(blob, "secret")["secrets"]["openai"] == "sk-test"


def test_wrong_passphrase():
    blob = encrypt_payload({"secrets": {"a": "b"}}, "right", FAST)
    with pytest.raises(WrongPassphrase):
        decrypt_payload(blob, "wrong")


def test_file_round_trip(tmp_path: Path):
    path = tmp_path / "vault"
    create_vault(path, "pw", FAST)
    payload = load_vault(path, "pw")
    payload["secrets"]["github"] = "ghp-test"
    save_vault(path, payload, "pw", FAST)
    assert load_vault(path, "pw")["secrets"]["github"] == "ghp-test"


def test_env_name():
    assert env_name("openai") == "OPENAI"
    assert env_name("openai-api-key") == "OPENAI_API_KEY"
    assert env_name("OPENAI_API_KEY") == "OPENAI_API_KEY"

# Copyright (C) 2026 Veil contributors
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import json
import os
import struct
from dataclasses import dataclass
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

MAGIC = b"VL01"
SALT_LEN = 16
NONCE_LEN = 12
KEY_LEN = 32
DEFAULT_ITERATIONS = 3
DEFAULT_MEMORY_KIB = 64 * 1024
DEFAULT_LANES = 4


class VaultError(Exception):
    pass


class WrongPassphrase(VaultError):
    pass


@dataclass
class KdfParams:
    iterations: int = DEFAULT_ITERATIONS
    memory_kib: int = DEFAULT_MEMORY_KIB
    lanes: int = DEFAULT_LANES


def _derive(passphrase: str, salt: bytes, params: KdfParams) -> bytes:
    kdf = Argon2id(
        salt=salt,
        length=KEY_LEN,
        iterations=params.iterations,
        lanes=params.lanes,
        memory_cost=params.memory_kib,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def empty_payload() -> dict:
    return {"secrets": {}}


def encrypt_payload(payload: dict, passphrase: str, params: KdfParams | None = None) -> bytes:
    params = params or KdfParams()
    salt = os.urandom(SALT_LEN)
    nonce = os.urandom(NONCE_LEN)
    key = _derive(passphrase, salt, params)
    plaintext = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, MAGIC)
    header = MAGIC + struct.pack(
        ">IIB",
        params.iterations,
        params.memory_kib,
        params.lanes,
    )
    return header + salt + nonce + ciphertext


def decrypt_payload(blob: bytes, passphrase: str) -> dict:
    if len(blob) < 4 + 9 + SALT_LEN + NONCE_LEN + 16:
        raise VaultError("vault file is truncated or corrupt")
    if blob[:4] != MAGIC:
        raise VaultError("not a Veil vault")
    iterations, memory_kib, lanes = struct.unpack(">IIB", blob[4:13])
    salt = blob[13 : 13 + SALT_LEN]
    nonce = blob[13 + SALT_LEN : 13 + SALT_LEN + NONCE_LEN]
    ciphertext = blob[13 + SALT_LEN + NONCE_LEN :]
    params = KdfParams(iterations=iterations, memory_kib=memory_kib, lanes=lanes)
    key = _derive(passphrase, salt, params)
    try:
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, MAGIC)
    except InvalidTag as exc:
        raise WrongPassphrase("wrong passphrase or corrupted vault") from exc
    payload = json.loads(plaintext.decode("utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("secrets"), dict):
        raise VaultError("vault payload is invalid")
    return payload


def create_vault(path: Path, passphrase: str, params: KdfParams | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encrypt_payload(empty_payload(), passphrase, params))


def load_vault(path: Path, passphrase: str) -> dict:
    return decrypt_payload(path.read_bytes(), passphrase)


def save_vault(path: Path, payload: dict, passphrase: str, params: KdfParams | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(encrypt_payload(payload, passphrase, params))
    tmp.replace(path)


def env_name(name: str) -> str:
    return name.upper().replace("-", "_")

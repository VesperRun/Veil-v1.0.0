# Copyright (C) 2026 Veil contributors
# SPDX-License-Identifier: GPL-3.0-only

"""Operator-facing transparency. Filter tier — does not enter the vault or run loop."""

from veil import __version__
from veil.paths import data_dir, log_path, vault_path

NOTICE = """Veil {version} — what this tool does

Veil is a local run-broker. It is not an AI system. It does not call a model.
How the code was written does not wrap this product. There is no AI interaction alert,
because you are not talking to AI.

Local-first rules (always):
  I    Locality         — secrets stay on this machine
  II   Minimization     — only names you explicitly save
  III  Consent          — nothing moves unless you command it
  IV   Transparency     — this text; also `veil status`
  V    Erasure          — `veil unset` and `veil erase --yes`
  VI   Human authority  — you unlock, run, lock, erase; Veil does not act alone
  VII  No surveillance  — no telemetry, analytics, or crash reporters

What it does:
  - Stores secrets you explicitly save, encrypted, in {vault}
  - Holds them in a session on this machine after you unlock
  - Injects named secrets into one child command when you run `veil run`
  - Writes an access log of names, commands, and grant/deny — never values
    Log: {log}

What it never does:
  - No network. No accounts. No cloud. No get. Nothing in Veil prints a secret.
  - No autonomous action.
  - No "you are talking to AI" banner. That alert is for products that ship a model.

Where files live:
  {data}
  VEIL_HOME overrides that directory. VEIL_PIPE overrides the local session pipe.

You approve every change. You deploy.
"""


def render() -> str:
    return NOTICE.format(
        version=__version__,
        vault=vault_path(),
        log=log_path(),
        data=data_dir(),
    )

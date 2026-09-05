# Veil

Local run-broker. The child gets the key. The transcript does not.

GPL-3. No account. No cloud. No telemetry. Not an AI system.

There is no `veil get`. Nothing in this tool prints a secret.

## Install

Python 3.11 or newer.

```bash
git clone https://github.com/VesperRun/Veil-v1.0.0.git
cd Veil-v1.0.0
pip install -e ".[dev]"
python -m veil
```

On Windows, use `python -m veil` if `veil` is not on PATH.

## Use

```bash
python -m veil init
python -m veil set OPENAI_API_KEY
python -m veil unlock
python -m veil run --with OPENAI_API_KEY -- python your_script.py
python -m veil log
python -m veil lock
python -m veil explain
python -m veil erase --yes
```

`--with NAME` injects that secret into the **child process only**, as an environment variable. `openai` becomes `OPENAI`. Store `OPENAI_API_KEY` if that is the name you want.

Unlock once. The session holds secrets in memory and locks after 30 minutes idle, or when you run `lock`. `explain` states the rules and paths. `erase --yes` deletes the vault, log, and session files. `unset NAME` removes one secret.

## What it is

A vault on your machine. A session you unlock. One command that may see named secrets. An access log of names and grant/deny — never values.

Simple, local, sharp. For the people.

## What it is not

Not a password manager for websites. Not HASP. Not a credential proxy. Not protection against someone who already owns the box. The child can read `os.environ`. Veil does not call a model, so there is no “you are talking to AI” alert.

## Tests

```bash
python -m pytest -q
```

## Privacy and security

- [PRIVACY.md](PRIVACY.md) — Veil collects nothing remotely.
- [SECURITY.md](SECURITY.md) — how to report a hole, and what we do not claim.
- On the machine: `python -m veil explain`

## License

[GNU GPL-3.0 only](LICENSE). If you distribute Veil or a modified version, you must do so under GPL-3 and provide the source.

For the people. Local only. Always.

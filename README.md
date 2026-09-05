# Veil

Local run-broker. GPL-3. No account. No cloud. No telemetry.

The agent can use the key. It cannot see the key.

Veil is not an AI system. It does not call a model. There is no “you are talking to AI” alert, because you are not. A later layer that invokes a model would have to stop and disclose. This one does not.

There is no `veil get`. Nothing in this tool prints a secret.

## Install

```bash
pip install -e ".[dev]"
```

## Use

```bash
veil init
veil set OPENAI_API_KEY
veil unlock
veil run --with OPENAI_API_KEY -- python your_script.py
veil unset OPENAI_API_KEY
veil log
veil lock
veil explain
veil erase --yes
```

`--with NAME` injects that secret into the child process only, as an environment variable. The name is uppercased (`openai` → `OPENAI`). Store `OPENAI_API_KEY` if that is the variable you want.

Unlock once. The session holds secrets in memory and locks after 30 minutes idle, or when you run `veil lock`.

`veil explain` states the local-first rules, what is stored, where, and what Veil never does. `veil erase --yes` deletes the vault, log, and session files.

## Rules

Always, whether or not a model is present:

- Data stays on this machine
- Store only what you save
- Nothing moves without your command
- The tool declares itself (`veil explain`)
- You can erase it
- You decide; Veil does not act alone
- No telemetry

AI disclosure applies only if the shipped product uses AI. Veil does not.

## Scope

Standing order: simple, local, sharp. For the people.

Veil stays tiny. It is a local run-broker, not a platform.

- Unlock a vault, inject named secrets into one child command, lock, log names.
- No MCP, no agent profiles, no repo grants, no HTTP proxy, no telemetry, no account.
- No network in the core. Local IPC only.

HASP is a fuller agent broker. Agent Vault is a credential proxy. Veil injects into one child command and stops there.

## What this is not

Not a password manager for websites. Not protection against someone who already owns the machine. Not an AI wrapper. The child process still sees the secret in its environment. Secrets stay out of chat transcripts, `veil` output, and your shell environment.

## Privacy

Veil collects nothing remotely. Secrets stay on your machine. See [PRIVACY.md](PRIVACY.md) and `veil explain`.

## Security

How to report a hole, and what Veil does not claim: [SECURITY.md](SECURITY.md).

## License

GNU General Public License v3.0 only. You can use, study, share, and change Veil. If you distribute it or a modified version, you must do so under GPL-3 as well, and provide the source. See [LICENSE](LICENSE).

For the people. Local only. Always.

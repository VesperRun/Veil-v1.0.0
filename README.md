# Veil

Local agent credential broker. Free software under GPL-3. No account. No cloud. No telemetry.

**The agent can use the key. It cannot see the key.**

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
veil log
veil lock
```

`--with NAME` injects that secret into the **child process only**, as an environment variable. The name is uppercased (`openai` → `OPENAI`). Store `OPENAI_API_KEY` if that is the variable you want.

Unlock once. The session holds secrets in memory and locks itself after 30 minutes idle, or when you run `veil lock`.

## What this is not

Not a password manager for websites. Not protection against someone who already owns the machine. The guarantee is: secrets stay out of chat transcripts, `veil` output, and your shell environment.

## License

GNU General Public License v3.0 only. You can use, study, share, and change Veil. If you distribute it or a modified version, you must do so under GPL-3 as well, and provide the source. See [LICENSE](LICENSE).

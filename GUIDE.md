# Veil setup guide

This is the first hour. The README is the product. This page is only how to stand it up.

Veil never prints a secret. There is no `get`. Do not put a real key in a command line or a chat.

## 1. Need

- Python 3.11 or newer
- This repository
- A passphrase you will remember. Veil cannot recover it.

## 2. Install

```bash
git clone https://github.com/VesperRun/Veil-v1.0.0.git
cd Veil-v1.0.0
pip install -e ".[dev]"
python -m veil
```

You should see one sentence and `veil explain`. On Windows, keep using `python -m veil`. The `veil` command may be missing from PATH. That is normal.

## 3. First vault

```bash
python -m veil init
```

Enter a passphrase twice. That creates an encrypted file on this machine (Windows: `%LOCALAPPDATA%\veil\vault`).

## 4. Store one name

Use a throwaway the first time.

```bash
python -m veil set DEMO
```

It will prompt for the value. Type it. It will not echo.

## 5. Unlock, run, lock

```bash
python -m veil unlock
python -m veil run --with DEMO -- python -c "import os; print('ok' if os.environ.get('DEMO') else 'missing')"
python -m veil lock
```

`--with DEMO` sets `DEMO` in the **child** only. The parent shell stays empty. `unlock` keeps a session for 30 minutes of idle, or until `lock`.

If the child is your real script, use the name it already expects (`OPENAI_API_KEY`, not `openai`).

## 6. Look, do not dump

```bash
python -m veil list
python -m veil status
python -m veil log
python -m veil explain
```

`list` is names only. `log` is names, commands, granted or denied. `explain` is the privacy notice on your disk.

## 7. Remove

```bash
python -m veil unset DEMO
python -m veil erase --yes
```

`unset` drops one name. `erase --yes` deletes vault, log, and session files. It cannot take back a key you already pasted somewhere else.

## Helpful hints

### What a shortcut is

A shortcut is an icon on your desktop. You click it instead of typing the long `veil run` line every time.

It is the same command, saved. Veil still sits in the middle. The app gets the named key for **that one launch** only. It does not get the vault. It cannot come back later and read secrets on its own.

Everyday loop stays the same: `unlock` → click the shortcut → use the app → `lock` (or wait for the 30-minute idle lock).

Do not put the secret in the shortcut. Only the name (`OPENAI_API_KEY`). If someone opens the shortcut’s properties, they should see a name, never a key.

If Veil is locked, the click fails. That is correct. Unlock, then click again.

### Make one on Windows

1. Right-click the desktop → New → Shortcut.
2. In the location box, paste one line. Change the exe path to your app:

```text
python -m veil run --with OPENAI_API_KEY -- "C:\Path\TheApp.exe"
```

3. Name it something you will recognize (`Star Turn via Veil`).
4. Finish. Use the name you stored (`python -m veil list` if you forget). Quote the exe path if it has spaces.

If a click says `python` was not found, replace `python` with the full path to `python.exe` (where Python is installed).

A `.cmd` file in a folder you own is the same idea — a small file that holds that one line, which you can also pin or shortcut.

## If it fails

| You see | Try |
|---|---|
| `veil` is not recognized | `python -m veil` |
| no vault | `init` first |
| locked | `unlock` |
| wrong passphrase | the passphrase from `init`; there is no reset except `erase` and start over |
| unknown secret | `list`; `--with` must match the stored name |
| still locked after a crash | `unlock` again; a dead session is treated as locked |

## Leave these alone

Do not ask Veil to print a secret. Do not put the value in argv. Do not commit the vault. Do not expect the child to be blind — it can read its own environment.

For the people. Local only. Always.

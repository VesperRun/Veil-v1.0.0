# Security

Veil is a local run-broker. Report holes in the tool. Do not expect it to defend a hostile machine.

## How to report

Use GitHub’s private advisory on this repository:

https://github.com/VesperRun/Veil-v1.0.0/security/advisories/new

If that form is not available, open an issue **without** secret values, exploit code, or a full write-up, and say you want a private channel.

Do not file a public issue that includes a working exploit.

## What Veil is meant to do

- Keep secret values off disk except as an encrypted vault
- Keep values out of `veil` output, the access log, and the parent environment
- Inject named values into one child process you asked for
- Wipe the session on lock, idle timeout, or a trapped shutdown

## What Veil is not

- Not protection against someone who already has code execution on the box
- Not DRM, anti-debug, or anti-tamper
- Not a network proxy; the child process sees the secret in its environment
- Not a guarantee against `kill -9`, core dumps, swap, or a debugger on the daemon
- Not an AI system and not a cloud vault

If you need the agent to never hold the key even inside a child, this is the wrong tool.

## Scope

In scope: vault format, passphrase handling, session IPC, `run` injection, wipe, log contents, accidental print or leak in Veil itself.

Out of scope: the child you launch, your OS, your backups, GitHub’s site, and “I pasted the key into a chat.”

## Supported versions

The `master` branch of this repository. There is no paid support line.

You approve every change. You deploy.

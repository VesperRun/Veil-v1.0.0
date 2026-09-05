# Privacy

Veil is a program you run on your own computer. It is not a service. It has no account, no website backend, and no company cloud.

This page is a plain notice. It is not legal advice. It is not a certification of any statute.

## What Veil collects

Nothing remotely. Veil does not open the network. It does not send telemetry, analytics, crash reports, or usage data. There is no update check.

## What stays on your machine

Only what you save, and only after you command it:

- An encrypted vault of named secrets you enter with `veil set`
- A session while the vault is unlocked (memory on this machine)
- An access log of names, commands, and grant/deny — never secret values

Default location on Windows: `%LOCALAPPDATA%\veil`  
Override: `VEIL_HOME`

The child process you start with `veil run` receives the named secrets in its environment. That process is yours. Veil does not transmit those values.

## What you can delete

- One name: `veil unset NAME`
- Vault, log, and session files: `veil erase --yes`

After erase, Veil has nothing left on disk that it created. It cannot erase data from a child process or from backups you made yourself.

## What this product is not

Veil is not an AI system. It does not call a model. There is no “you are talking to AI” notice, because you are not.

GitHub may log visits to this repository under GitHub’s own policy. That is GitHub, not Veil.

## On demand

`veil explain` prints the same facts with the paths on your machine.

You approve every change. You deploy.

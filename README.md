# grkit — a guardrails kit

Guardrails for software that uses LLMs, in two halves that fail in opposite directions on purpose:

- **On the answer path, fail OPEN.** A guard outage degrades to "not guarded", never "no answer". Guards ship in
  SHADOW (record only) and block only after their false-positive rate is measured on real traffic. Every fail-open
  is counted, so a guard that quietly stopped guarding still raises an alert.
- **On the change path, fail CLOSED.** A check that could not run is never a pass: `0` clean · `1` findings ·
  `2` could not check.

Both rules say one thing: **never let an absence pose as a result.** The reasoning: [docs/method.md](docs/method.md).

## What's here

| Part | For | Docs |
|---|---|---|
| `python/` — the `grkit` package (stdlib only) | guard services and their callers: `verdict` (the decision vocabulary and wire format), `client` (a fail-open guard client that counts its failures), `modes` (shadow/flag/block per validator, bad config stops startup), `pipeline` (runs a hook's validators), `checks` (the 0/1/2 result for build-time checks) | [docs/runtime-guardrails.md](docs/runtime-guardrails.md) |
| `template/` — a Copier template | any repo: an `AGENTS.md` core for coding agents, a nine-pillar definition of done, and a worked fail-closed guard with its tests | [docs/change-gate.md](docs/change-gate.md) |

## Adopt it

Runtime half:

```
pip install "grkit @ git+https://github.com/edtbl76/grkit@v0.1.1#subdirectory=python"
```

Build-time half:

```
pipx run copier copy gh:edtbl76/grkit path/to/repo
pipx run copier update          # later, to pull newer rules
```

Details and examples: [docs/adopting.md](docs/adopting.md).

## Develop

```
bash scripts/test.sh
```

It runs the package tests, renders the template into a scratch directory, runs the rendered guard's own tests
(including the cases where it must fail), and runs the rendered guard against the rendered repo. Everything runs in
Docker as your user; nothing is installed on the host.

## Origin

Extracted from a self-hosted AI platform where these rules were learned the hard way: a validator that flagged
every tech noun as a person, a shadow guard that hid an outage, a quality gate that passed with critical issues
open, a backup that had never been restored. The lessons are written up in the docs; the platform itself is not
part of this repo.

# Adopting grkit

## The runtime half: the Python package

Stdlib only, Python 3.10+. Install from git (the package lives in `python/`):

```
pip install "grkit @ git+https://github.com/edtbl76/grkit@v0.1.1#subdirectory=python"
```

A guard SERVICE uses `grkit.verdict`, `grkit.modes.ModeTable` and `grkit.pipeline.GuardrailPipeline` around its own
validators (the models stay in the service). A CALLER uses `grkit.client.GuardClient`:

```python
from grkit.client import GuardClient
from grkit.verdict import Hook

guard = GuardClient(os.environ["GUARD_BASE_URL"], timeout=10,
                    on_failure=lambda hook, cause: GUARD_FAILOPEN.labels(hook.value, cause).inc())
blocked = guard.guard(Hook.OUTPUT, request_id, {"answer": answer, "sources": sources}, actor=trusted_actor)
if blocked:
    return refusal(blocked.reason)
```

Export `on_failure` as a metric and alert on it: fail-open is only safe when someone sees it happen.

## The build-time half: the Copier template

```
pipx run copier copy gh:edtbl76/grkit .            # answer the questions; writes the files below
pipx run copier update                             # later: pull the kit's newer rules, review the diff
```

It writes:

| File | What |
|---|---|
| `AGENTS.md` | the core rules for every coding agent (fail closed, observe before stubbing, …); add project rules below the marked line |
| `docs/definition-of-done.md` | the nine pillars |
| `scripts/check-required-docs.sh` + `scripts/tests/check-required-docs.bats` | a worked fail-closed guard and the tests that watch it fail |
| `.grkit/required-docs` | the documents the guard requires |
| `.copier-answers.yml` | what `copier update` needs; commit it |

Wire the guard into CI as its own step. It must run on every change, and a `2` must fail the build like a `1`.

## Keeping up to date

A repo that never runs `copier update` keeps the rules it was born with. Run it when the kit's changelog shows a
new rule, and review the diff like any other change: the update merges, it does not overwrite your additions below
the marked line.

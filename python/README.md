# grkit (Python package)

The runtime half of [grkit](https://github.com/edtbl76/grkit), stdlib only, Python 3.10+.

| Module | For |
|---|---|
| `grkit.verdict` | `Decision`, `Hook`, `Mode`, `Verdict`: the decision vocabulary and its wire format |
| `grkit.client` | `GuardClient`: calls a guard service; fails open on content hooks and closed on the act hook; counts every failure by cause |
| `grkit.modes` | `ModeTable`: shadow/flag/block per validator from defaults, env and live overrides; a bad value stops startup |
| `grkit.pipeline` | `GuardrailPipeline`: runs a hook's validators (shadow off the request path, flag/block inline) |
| `grkit.checks` | `run()`: the 0 clean / 1 findings / 2 could-not-check result for build-time checks |

```
pip install "grkit @ git+https://github.com/edtbl76/grkit@v0.2.0#subdirectory=python"
```

The method and the contracts: [docs](https://github.com/edtbl76/grkit/tree/main/docs).

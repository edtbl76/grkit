# Contributing to grkit

Thanks for helping. grkit is small on purpose, and its rules apply to its own code first. Here's how to work on it.

## Ways to help

- **Tell us a war story.** Found a guard that lied, a check that passed on nothing, a monitor that cried wolf? Open
  an issue. Real failures are where the rules come from.
- **Report a bug** in the package or the template.
- **Improve the docs**, especially where they assume knowledge they don't explain.
- **Send a pull request.** For anything bigger than a fix, open an issue first so we can agree on the shape.

## Set up

You need Docker and bash. Nothing else gets installed on your machine.

```
git clone https://github.com/edtbl76/grkit
cd grkit
bash scripts/test.sh
```

`scripts/test.sh` runs everything: the package tests, a real install of the package, a render of the template, the
rendered guard's own tests, and the rendered guard against the rendered repo. It must print
`grkit: all 4 stages passed`.

To iterate on just the package:

```
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD":/w -w /w/python python:3.12-slim \
  sh -c 'pip install -q pytest && python -m pytest -q'
```

## How we write code here

1. **Write the failing test first.** Run it and watch it fail for the right reason. Then write the code that
   makes it pass.
2. **Assert the reason, not just the outcome.** A test that only checks "exit code isn't 0" also passes when the
   command doesn't exist. Check the message.
3. **Fail closed in checks, fail open in guards.** A build-time check that couldn't run exits `2`. A runtime guard
   client that couldn't reach its service returns "allow", and counts it. If you're not sure which one you're
   writing, read [docs/method.md](docs/method.md).
4. **Observe before you stub.** If a test fakes an external system, call the real thing once and copy its actual
   response shape into the fake. Say in a comment when and where you observed it.
5. **No dependencies in the package.** `grkit` is standard library only. Model-backed or heavy code belongs in the
   services that use grkit, not in grkit.
6. **Nothing environment-specific.** No hostnames, IP addresses, internal service names or credentials, anywhere.
   `test_repo_hygiene.py` enforces this, and it will fail your build.
7. **Shell that makes decisions gets bats tests**, and passes `shellcheck --severity=warning`.

## Pull requests

- Keep each PR to one change, with a description of *why*.
- Add a line to [CHANGELOG.md](CHANGELOG.md) under **Unreleased**.
- `bash scripts/test.sh` passes, and CI is green.
- If you change the template, check that `copier update` on an already-rendered repo still produces a sensible
  diff.

## Releases

Versions are git tags (`v0.1.1`, …), and the package version in `python/pyproject.toml` matches the tag. A
published tag is never moved: a fix ships as a new version.

## Conduct

Everyone taking part follows the [Code of Conduct](CODE_OF_CONDUCT.md).

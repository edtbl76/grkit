## What and why

<!-- What does this change, and what problem does it solve? Link the issue if there is one. -->

## Checklist

- [ ] I wrote the failing test first and watched it fail for the right reason.
- [ ] Tests assert *why* something failed, not only that it did.
- [ ] Checks fail closed (`2` when they can't run); guard clients fail open and count it.
- [ ] No dependencies added to the package; nothing environment-specific (hosts, IPs, credentials).
- [ ] `bash scripts/test.sh` prints `grkit: all 4 stages passed`.
- [ ] `CHANGELOG.md` has a line under **Unreleased**.

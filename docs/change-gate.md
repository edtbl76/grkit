# The change gate: build-time guardrails

Everything a change must pass before it is done. Each item fails closed: `0` clean · `1` findings · `2` could not
check, which is never a pass.

## 1. Before the work starts

- **The issue is implementation-ready.** Beyond why and scope, it names the affected systems and files, testable
  acceptance criteria, edge cases and failure modes, and what is out of scope. Check it by rule, not by an LLM
  score: required sections with real content, at least one real acceptance criterion, a priority.
- **Check decisions already made.** A rejected option re-proposed costs the owner's time.

## 2. While building

- **Test first.** For each layer: a failing test, the minimum code to pass it, then refactor. Shell that makes
  decisions gets tests too (bats).
- **Observe before stubbing.** Call the real API once and write the stub to what it returned.
- **Assert the failure reason**, never only a non-zero status.
- **Prove the change in its own toolchain image** before pushing. CI confirms; it should not discover.

## 3. Before handoff

- **The whole local guard suite**, not one guard: the first failure masks the later ones.
- **Static analysis with the CI gate's rules on the changed files.** If CI blocks on a quality gate, run the same
  rules locally first. A scratch analysis project's own gate passes with issues open, so judge by the findings.
- **Read what each tool printed**, not just its exit code.

## 4. The definition of done (nine pillars)

A change is done when it is:

1. **Documented** — the architecture entry (with the alternatives rejected), the runbook with the real commands,
   and the API and host lists.
2. **Placed** — in the architecture model, with a sequence diagram for any non-obvious flow.
3. **Demonstrated** — a demo that was actually run, including a negative case, with eyes-on steps for any UI.
4. **Reversible** — anything a demo creates has a teardown.
5. **Tracked** — the backlog and the issue tracker agree.
6. **Operationally durable** — it runs on a schedule or a trigger, is monitored, and its secrets are restorable.
7. **Scanned** — security and quality scans run, findings triaged (fixed, or accepted with a written reason).
8. **Cascaded** — everything that had to move because this moved, did.
9. **Recoverable** — every piece of state has a backup and a restore that was actually tested.

The template ships this as `docs/definition-of-done.md`.

## 5. Guards that keep the estate honest

Patterns worth a guard in most repos:

| Guard | Catches |
|---|---|
| Required documents present and non-empty | the runbook or architecture page nobody wrote |
| Two copies of shared code identical | drift between a library and its vendored copy |
| Every scheduled job has a freshness budget | a job that stopped and nobody noticed |
| Every heartbeat monitor's interval exceeds its job's cadence | a monitor that goes red a minute after every good run (a common default) |
| Every backup has a restore drill on record | a backup that has never been restored |
| Every deployed component appears in the inventory | a workload nobody knows is running |

A guard is a script with three exit codes and a test that watches each one happen. The template's
`scripts/check-required-docs.sh` is a worked example.

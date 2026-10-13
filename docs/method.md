# The method: fail open on the answer path, fail closed on the change path

Guardrails sit in two places, and they fail in opposite directions on purpose.

| | Runtime guardrails | Build-time guardrails |
|---|---|---|
| **Guard** | a model's input, output and actions while it serves | a change to the code, config or docs before it lands |
| **Examples** | prompt-injection and PII scanners, a safety classifier, topical rails, output-schema checks, an action allowlist | repo guards, the definition of done, static analysis, restore drills, monitor checks |
| **When the guard itself breaks** | **fail OPEN**: "not guarded", never "no answer" | **fail CLOSED**: "could not check" is never a pass |
| **Why** | a guard outage must not take the product down | a check that ran on nothing must not look like a clean estate |
| **Promotion** | ship in SHADOW (record only); measure the false-positive rate on real traffic; then FLAG, then BLOCK | a new check blocks from day one, but only after it has been seen failing |
| **Exit / decision** | `allow` or `block` (+ a recorded verdict) | `0` clean · `1` findings · `2` could not check |

The two rules look contradictory and are the same idea: **never let an absence pose as a result.** On the answer
path, the absence is a guard that did not answer; the safe reading is "unguarded", which keeps serving, and it is
counted so someone sees it. On the change path, the absence is a check that did not run; the safe reading is "not
verified", which stops the change.

## Rules that follow

1. **An absent, empty or errored result is never success.** `cmd 2>/dev/null` inside a boolean, a pipeline whose
   status is the last command's, an empty list where a list of findings was expected: each turns an error into a
   positive answer. Read what a tool printed, not only its exit code; some tools print `FAILED` and exit 0.
2. **Fail-open is never silent.** A runtime guard that fell open is counted by cause and exported, so "the guard
   quietly stopped guarding" alerts like any other outage (`grkit.client.GuardClient.failures`).
3. **Shadow before block.** A validator's default mode is SHADOW. Promote it only with a measured false-positive
   rate on the traffic it will actually see: a PII detector that is precise on emails can flag every tech noun as
   a person.
4. **A check nobody has watched fail is not a check.** Every build-time check has a test that makes it fail, and
   the test asserts the failure REASON, not only a non-zero exit: exit 127 (command not found) is non-zero too.
5. **Observe the real system before stubbing it.** A stub encodes the author's assumption about an API; observe the
   real response once, then write the stub to that shape. Many defects survive green tests and die in the first
   live run.
6. **A verdict is not a scratch gate.** When a check borrows another tool's pass/fail (a quality gate, a
   dashboard), confirm that verdict means what you need. A brand-new analysis project's gate can pass with
   critical issues open.
7. **Modes come from configuration, and a bad value stops startup.** A typo in a mode must not fall back to the
   permissive default (`grkit.modes.ModeTable`).

## Where each half lives

- Runtime contracts: [runtime-guardrails.md](runtime-guardrails.md), and the `grkit` Python package.
- Build-time process: [change-gate.md](change-gate.md), and the Copier template.
- Adopting either half: [adopting.md](adopting.md).

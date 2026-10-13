"""Build-time checks FAIL CLOSED.

A check function returns a LIST of findings (strings). The exit code is the contract a CI step or a human reads:

  0  clean — the check ran and found nothing
  1  findings — the estate has a defect; each finding is printed
  2  could not check — an exception, an absent result, the wrong type. NEVER a pass: "verified nothing" and
     "verified, all good" must not look the same.

    import sys
    from grkit.checks import run
    sys.exit(run("docs-present", find_missing_docs))
"""
import sys
from enum import IntEnum
from typing import Callable


class Exit(IntEnum):
    CLEAN = 0
    FINDINGS = 1
    CANNOT_CHECK = 2


def run(name: str, check: Callable[[], list]) -> Exit:
    try:
        findings = check()
    except Exception as exc:
        print(f"{name}: could not check — {type(exc).__name__}: {exc}", file=sys.stderr)
        return Exit.CANNOT_CHECK
    if findings is None:
        print(f"{name}: could not check — the check returned no result", file=sys.stderr)
        return Exit.CANNOT_CHECK
    if not isinstance(findings, list):
        print(f"{name}: could not check — expected a list of findings, got {type(findings).__name__}",
              file=sys.stderr)
        return Exit.CANNOT_CHECK
    if not findings:
        print(f"{name}: OK")
        return Exit.CLEAN
    for f in findings:
        print(f"  ❌ {f}")
    print(f"{name}: {len(findings)} finding(s)")
    return Exit.FINDINGS

"""grkit — a guardrails kit.

Runtime (the answer path) FAILS OPEN: a guard outage degrades to "not guarded", never "no answer", guards ship in
SHADOW, and nothing blocks until its false-positive rate is measured. Build time (the change path) FAILS CLOSED: a
check that could not run is never a pass. See docs/method.md.
"""
__version__ = "0.1.1"

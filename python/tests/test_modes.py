"""grkit.modes — which mode each validator runs in: a default, overridden by env, overridden live (never persisted)."""
import pytest

from grkit.modes import ModeTable
from grkit.verdict import Hook, Mode

DEFAULTS = {Hook.INPUT: [("injection", Mode.SHADOW), ("safety", Mode.SHADOW)],
            Hook.ACT: [("policy.gate", Mode.SHADOW)]}


def test_defaults_apply_when_nothing_overrides():
    t = ModeTable(DEFAULTS, env={})
    assert t.chain(Hook.INPUT) == [("injection", Mode.SHADOW), ("safety", Mode.SHADOW)]
    assert t.chain(Hook.OUTPUT) == []
    assert t.validators() == ["injection", "policy.gate", "safety"]


def test_env_overrides_a_default_with_dots_as_double_underscores():
    t = ModeTable(DEFAULTS, env={"GUARDRAIL_MODE__policy__gate": "block"})
    assert t.chain(Hook.ACT) == [("policy.gate", Mode.BLOCK)]


def test_a_live_override_wins_and_reset_returns_to_env():
    t = ModeTable(DEFAULTS, env={"GUARDRAIL_MODE__injection": "flag"})
    t.set_override("injection", Mode.OFF)
    assert t.chain(Hook.INPUT)[0] == ("injection", Mode.OFF) and t.overrides() == {"injection": "off"}
    t.clear_overrides()
    assert t.chain(Hook.INPUT)[0] == ("injection", Mode.FLAG)


def test_an_invalid_env_mode_fails_closed_at_construction():
    # a typo must not quietly fall back to SHADOW and disable a block someone meant to enforce
    with pytest.raises(ValueError, match="GUARDRAIL_MODE__policy__gate.*'blok'"):
        ModeTable(DEFAULTS, env={"GUARDRAIL_MODE__policy__gate": "blok"})


def test_an_override_for_an_unknown_validator_is_refused():
    t = ModeTable(DEFAULTS, env={})
    with pytest.raises(KeyError, match="nope"):
        t.set_override("nope", Mode.BLOCK)

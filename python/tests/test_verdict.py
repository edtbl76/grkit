"""grkit.verdict — the shared vocabulary of a guard decision, wire-compatible with the service it was extracted from."""
import json

from grkit.verdict import Decision, Hook, Mode, Verdict


def test_values_are_the_wire_strings():
    assert [d.value for d in Decision] == ["pass", "flag", "block"]
    assert [h.value for h in Hook] == ["input", "output", "act"]
    assert [m.value for m in Mode] == ["off", "shadow", "flag", "block"]


def test_enums_compare_equal_to_their_wire_string():
    # str-valued enums: callers that compare against the raw JSON string keep working
    assert Decision.BLOCK == "block" and Hook.ACT == "act" and Mode.SHADOW == "shadow"


def test_a_service_response_round_trips():
    # The response shape of the guard service grkit was extracted from:
    # {request_id, decision: "allow" | "block", verdict: {validator, decision, score, reason, latency_ms} | null}
    wire = {"request_id": "r1", "decision": "block",
            "verdict": {"validator": "policy.gate", "decision": "block", "score": None,
                        "reason": "no actor", "latency_ms": 3}}
    v = Verdict.from_wire(json.loads(json.dumps(wire))["verdict"])
    assert v == Verdict("policy.gate", Decision.BLOCK, None, "no actor", 3)
    assert v.to_wire() == wire["verdict"]


def test_from_wire_tolerates_missing_optional_fields():
    v = Verdict.from_wire({"decision": "flag"})
    assert v.validator == "guard" and v.decision is Decision.FLAG and v.score is None and v.latency_ms == 0

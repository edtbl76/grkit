"""grkit.pipeline — run a hook's validator chain: SHADOW fire-and-forget, FLAG/BLOCK inline, never break the request."""
import asyncio

from grkit.pipeline import GuardrailPipeline
from grkit.verdict import Decision, Hook, Mode, Verdict


class V:
    def __init__(self, name, decision, boom=False):
        self.name, self.decision, self.boom = name, decision, boom
        self.hooks = (Hook.INPUT,)

    def check(self, payload, hook):
        if self.boom:
            raise RuntimeError("model fell over")
        return Verdict(self.name, self.decision, 0.9, "because", 0)


def _run(chain, validators):
    records = []
    p = GuardrailPipeline({v.name: v for v in validators}, lambda hook: chain, lambda **kw: records.append(kw))

    async def go():
        result = await p.run(Hook.INPUT, "r1", {"query": "q"}, actor="a")
        await p.drain()
        return result
    return asyncio.run(go()), records


def test_shadow_never_blocks_but_records_the_verdict():
    result, records = _run([("inj", Mode.SHADOW)], [V("inj", Decision.BLOCK)])
    assert result is None
    assert records[0]["mode"] is Mode.SHADOW and records[0]["verdict"].decision is Decision.BLOCK


def test_block_mode_returns_the_first_blocking_verdict():
    result, records = _run([("a", Mode.FLAG), ("b", Mode.BLOCK), ("c", Mode.BLOCK)],
                           [V("a", Decision.FLAG), V("b", Decision.BLOCK), V("c", Decision.BLOCK)])
    assert result.validator == "b"
    assert [r["verdict"].validator for r in records] == ["a", "b"]          # c never ran: the request was blocked


def test_flag_mode_records_but_does_not_block():
    result, _ = _run([("a", Mode.FLAG)], [V("a", Decision.BLOCK)])
    assert result is None


def test_off_skips_entirely():
    result, records = _run([("a", Mode.OFF)], [V("a", Decision.BLOCK)])
    assert result is None and records == []


def test_a_validator_that_raises_passes_with_the_error_recorded():
    result, records = _run([("a", Mode.BLOCK)], [V("a", Decision.BLOCK, boom=True)])
    assert result is None
    assert records[0]["verdict"].decision is Decision.PASS and "validator error: model fell over" in records[0]["verdict"].reason


def test_a_configured_but_unloaded_validator_passes_and_says_so():
    result, records = _run([("missing", Mode.BLOCK)], [])
    assert result is None and records[0]["verdict"].reason == "validator not loaded"

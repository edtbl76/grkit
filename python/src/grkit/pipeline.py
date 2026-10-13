"""Run a hook's validator chain inside a guard service.

SHADOW runs fire-and-forget in a thread pool (validators are usually CPU-bound models) and only records: ~zero
added latency. FLAG and BLOCK run inline, because they can alter the response. A validator that raises, or one that
is configured but not loaded, PASSES with the reason recorded: inside the answer path a guard must never break the
request (the build-time rule is the opposite; see grkit.checks).
"""
import asyncio
import time
from typing import Callable, Protocol

from .verdict import Decision, Hook, Mode, Verdict


class Validator(Protocol):
    name: str
    hooks: tuple[Hook, ...]

    def check(self, payload: dict, hook: Hook) -> Verdict: ...


class GuardrailPipeline:
    def __init__(self, validators: dict[str, Validator], chain_for: Callable[[Hook], list[tuple[str, Mode]]],
                 record: Callable[..., None]):
        self._validators = validators
        self._chain_for = chain_for            # e.g. ModeTable.chain
        self._record = record                  # record(hook=, mode=, verdict=, request_id=, actor=)
        self._pending: set = set()

    def _run_one(self, name: str, payload: dict, hook: Hook) -> Verdict:
        v = self._validators.get(name)
        if v is None:
            return Verdict(name, Decision.PASS, None, "validator not loaded", 0)
        t0 = time.monotonic()
        try:
            verdict = v.check(payload, hook)
        except Exception as exc:               # a guard must never break the request
            return Verdict(name, Decision.PASS, None, f"validator error: {exc}", 0)
        verdict.latency_ms = int((time.monotonic() - t0) * 1000)
        return verdict

    async def _shadow(self, name, payload, hook, request_id, actor) -> None:
        verdict = await asyncio.get_running_loop().run_in_executor(None, self._run_one, name, payload, hook)
        self._record(hook=hook, mode=Mode.SHADOW, verdict=verdict, request_id=request_id, actor=actor)

    async def run(self, hook: Hook, request_id: str, payload: dict, actor: str | None = None) -> Verdict | None:
        """The first BLOCK verdict from a validator in BLOCK mode, else None."""
        loop = asyncio.get_running_loop()
        for name, mode in self._chain_for(hook):
            if mode == Mode.OFF:
                continue
            if mode == Mode.SHADOW:
                task = asyncio.create_task(self._shadow(name, payload, hook, request_id, actor))
                self._pending.add(task)
                task.add_done_callback(self._pending.discard)
                continue
            verdict = await loop.run_in_executor(None, self._run_one, name, payload, hook)
            self._record(hook=hook, mode=mode, verdict=verdict, request_id=request_id, actor=actor)
            if mode == Mode.BLOCK and verdict.decision == Decision.BLOCK:
                return verdict
        return None

    async def drain(self) -> None:
        """Await the shadow tasks still running (at shutdown, and in tests)."""
        if self._pending:
            await asyncio.gather(*list(self._pending), return_exceptions=True)

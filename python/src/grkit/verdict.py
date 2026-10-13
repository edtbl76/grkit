"""The shared vocabulary of a guard decision. The enum VALUES are the wire format: keep them stable."""
from dataclasses import asdict, dataclass
from enum import Enum


class Decision(str, Enum):
    PASS = "pass"
    FLAG = "flag"
    BLOCK = "block"


class Hook(str, Enum):
    INPUT = "input"      # the prompt / query, before the model sees it
    OUTPUT = "output"    # the answer, before the caller sees it (with its sources, for grounding)
    ACT = "act"          # a tool call or side effect, before it runs


class Mode(str, Enum):
    OFF = "off"          # not run
    SHADOW = "shadow"    # run off the request path, recorded, never alters the response
    FLAG = "flag"        # run inline, recorded, never blocks
    BLOCK = "block"      # run inline, recorded, a BLOCK decision stops the request


@dataclass
class Verdict:
    validator: str
    decision: Decision
    score: float | None
    reason: str
    latency_ms: int

    @classmethod
    def from_wire(cls, data: dict) -> "Verdict":
        return cls(data.get("validator", "guard"), Decision(data.get("decision", "pass")), data.get("score"),
                   data.get("reason", ""), int(data.get("latency_ms", 0) or 0))

    def to_wire(self) -> dict:
        d = asdict(self)
        d["decision"] = self.decision.value
        return d

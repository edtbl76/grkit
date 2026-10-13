"""grkit.client — the caller side of a guard service: fail OPEN on any outage, but never silently."""
import io
import json
import socket
import urllib.error

import pytest

from grkit.client import GuardClient
from grkit.verdict import Decision, Hook


class Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _client(monkeypatch, answer=None, raises=None, seen=None):
    def urlopen(req, timeout=None):
        if seen is not None:
            seen.append((req.full_url, json.loads(req.data), timeout))
        if raises is not None:
            raise raises
        return Resp(answer if isinstance(answer, bytes) else json.dumps(answer).encode())
    monkeypatch.setattr("grkit.client.urllib.request.urlopen", urlopen)
    return GuardClient("http://guard.example:8080", timeout=2.5)


def test_each_hook_posts_to_its_typed_route_with_the_request_and_actor(monkeypatch):
    seen = []
    c = _client(monkeypatch, {"decision": "allow", "verdict": None}, seen=seen)
    assert c.guard(Hook.INPUT, "r1", {"query": "hi"}, actor="agent-a") is None
    c.guard(Hook.OUTPUT, "r2", {"answer": "x", "sources": []})
    c.guard(Hook.ACT, "r3", {"tool": "restart"})
    assert [s[0] for s in seen] == ["http://guard.example:8080/guard/input", "http://guard.example:8080/guard/output",
                                    "http://guard.example:8080/guard/act"]
    assert seen[0][1] == {"request_id": "r1", "actor": "agent-a", "query": "hi"} and seen[0][2] == 2.5


def test_a_block_decision_returns_the_blocking_verdict(monkeypatch):
    c = _client(monkeypatch, {"decision": "block", "verdict": {"validator": "policy.gate", "decision": "block",
                                                               "score": None, "reason": "no actor"}})
    v = c.guard(Hook.ACT, "r", {"tool": "t"})
    assert v.validator == "policy.gate" and v.decision is Decision.BLOCK and v.reason == "no actor"


@pytest.mark.parametrize("raises, cause", [
    (socket.timeout("timed out"), "timeout"),
    (urllib.error.URLError(ConnectionRefusedError("refused")), "connection"),
    (urllib.error.HTTPError("u", 503, "unavailable", {}, io.BytesIO(b"")), "http_5xx"),
    (urllib.error.HTTPError("u", 422, "bad", {}, io.BytesIO(b"")), "http_4xx"),
])
def test_an_outage_fails_open_and_is_counted_by_cause(monkeypatch, raises, cause):
    c = _client(monkeypatch, raises=raises)
    assert c.guard(Hook.INPUT, "r", {"query": "q"}) is None          # allow: a guard outage never takes an answer down
    assert c.failures == {cause: 1}                                   # …but it is never silent


def test_a_non_json_answer_fails_open_and_is_counted(monkeypatch):
    c = _client(monkeypatch, answer=b"<html>gateway error</html>")
    assert c.guard(Hook.OUTPUT, "r", {"answer": "a", "sources": []}) is None
    assert c.failures == {"bad_response": 1}


def test_an_unexpected_decision_value_fails_open_and_is_counted(monkeypatch):
    c = _client(monkeypatch, {"decision": "maybe"})
    assert c.guard(Hook.INPUT, "r", {"query": "q"}) is None
    assert c.failures == {"bad_response": 1}


def test_on_failure_hook_sees_every_fail_open(monkeypatch):
    calls = []
    c = _client(monkeypatch, raises=socket.timeout("t"))
    c.on_failure = lambda hook, cause: calls.append((hook, cause))
    c.guard(Hook.ACT, "r", {"tool": "t"})
    assert calls == [(Hook.ACT, "timeout")]


def test_the_base_url_must_be_http():
    with pytest.raises(ValueError, match="http"):
        GuardClient("file:///etc/passwd")

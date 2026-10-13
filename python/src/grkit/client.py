"""The caller side of a guard service.

FAIL OPEN: any outage (timeout, refused connection, HTTP error, unreadable answer) returns None, meaning allow, so a
guard problem degrades to "not guarded", never "no answer". But never SILENTLY: every fail-open is counted by cause
in `failures` and passed to `on_failure`, so the caller can export it as a metric and alert on a guard that has
quietly stopped guarding.
"""
import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

from .verdict import Decision, Hook, Verdict

PATHS = {Hook.INPUT: "/guard/input", Hook.OUTPUT: "/guard/output", Hook.ACT: "/guard/act"}


class GuardClient:
    def __init__(self, base_url: str, timeout: float = 10.0, on_failure=None):
        if urllib.parse.urlsplit(base_url).scheme not in ("http", "https"):
            raise ValueError(f"guard base_url must be http(s), got {base_url!r}")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.failures: Counter = Counter()
        self.on_failure = on_failure        # callable(hook, cause) — e.g. increment a metric

    def _failed(self, hook: Hook, cause: str) -> None:
        self.failures[cause] += 1
        if self.on_failure is not None:
            self.on_failure(hook, cause)

    def guard(self, hook: Hook, request_id: str, payload: dict, actor: str | None = None) -> Verdict | None:
        """POST one hook. Returns the BLOCK verdict when the service blocked, else None (allow).

        `payload` carries the hook's own keys: input → query; output → answer + sources; act → tool + params.
        `actor` must come from a trusted source (a gateway-injected header), never from the client's own claim."""
        body = json.dumps({"request_id": request_id, "actor": actor, **payload}).encode()
        req = urllib.request.Request(self.base_url + PATHS[hook], data=body, method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            self._failed(hook, "http_5xx" if e.code >= 500 else "http_4xx")
            return None
        except (socket.timeout, TimeoutError):
            self._failed(hook, "timeout")
            return None
        except urllib.error.URLError as e:
            self._failed(hook, "timeout" if isinstance(e.reason, (socket.timeout, TimeoutError)) else "connection")
            return None
        except (ValueError, OSError):
            self._failed(hook, "bad_response")
            return None
        decision = data.get("decision") if isinstance(data, dict) else None
        if decision == "block":
            return Verdict.from_wire({**(data.get("verdict") or {}), "decision": Decision.BLOCK.value})
        if decision != "allow":
            self._failed(hook, "bad_response")
        return None

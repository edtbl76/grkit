"""The caller side of a guard service.

Content hooks (INPUT, OUTPUT) FAIL OPEN: any outage (timeout, refused connection, HTTP error, unreadable answer)
returns None, meaning allow, so a guard problem degrades to "not guarded", never "no answer".

The ACT hook FAILS CLOSED by default: it decides authority, not content, and a guard that is down must not mean
"anyone may act". An outage there returns a BLOCK verdict from `guard-unavailable` naming the cause.
`fail_closed_hooks` changes which hooks do which.

Never SILENTLY, either way: every failure is counted by cause in `failures` and passed to `on_failure`, so the
caller can export it as a metric and alert on a guard that has quietly stopped guarding.
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
    def __init__(self, base_url: str, timeout: float = 10.0, on_failure=None,
                 fail_closed_hooks=frozenset({Hook.ACT})):
        if urllib.parse.urlsplit(base_url).scheme not in ("http", "https"):
            raise ValueError(f"guard base_url must be http(s), got {base_url!r}")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.failures: Counter = Counter()
        self.on_failure = on_failure        # callable(hook, cause) — e.g. increment a metric
        self.fail_closed_hooks = frozenset(fail_closed_hooks)

    def _failed(self, hook: Hook, cause: str) -> Verdict | None:
        """Count the failure; then allow (None) on a fail-open hook, or refuse on a fail-closed one."""
        self.failures[cause] += 1
        if self.on_failure is not None:
            self.on_failure(hook, cause)
        if hook in self.fail_closed_hooks:
            return Verdict("guard-unavailable", Decision.BLOCK, None, f"guard unavailable ({cause}): action refused", 0)
        return None

    def guard(self, hook: Hook, request_id: str, payload: dict, actor: str | None = None) -> Verdict | None:
        """POST one hook. Returns a BLOCK verdict when the service blocked, or when the guard failed on a fail-closed
        hook (ACT by default); else None (allow).

        `payload` carries the hook's own keys: input → query; output → answer + sources; act → tool + params.
        `actor` must come from a trusted source (a gateway-injected header), never from the client's own claim."""
        body = json.dumps({"request_id": request_id, "actor": actor, **payload}).encode()
        req = urllib.request.Request(self.base_url + PATHS[hook], data=body, method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return self._failed(hook, "http_5xx" if e.code >= 500 else "http_4xx")
        except (socket.timeout, TimeoutError):
            return self._failed(hook, "timeout")
        except urllib.error.URLError as e:
            return self._failed(hook, "timeout" if isinstance(e.reason, (socket.timeout, TimeoutError)) else "connection")
        except (ValueError, OSError):
            return self._failed(hook, "bad_response")
        decision = data.get("decision") if isinstance(data, dict) else None
        if decision == "block":
            return Verdict.from_wire({**(data.get("verdict") or {}), "decision": Decision.BLOCK.value})
        if decision != "allow":
            return self._failed(hook, "bad_response")
        return None

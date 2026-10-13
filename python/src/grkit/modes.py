"""Which mode each validator runs in, per hook.

Precedence: a LIVE override (in-process, never persisted: a restart drops it, so a demo left "on" heals itself) >
an env var `GUARDRAIL_MODE__<validator>` (dots as double underscores) > the committed default. Every validator
should default to SHADOW: measure its false-positive rate on real traffic before promoting it.

An invalid env value FAILS CLOSED at construction: a typo ("blok") must not quietly fall back to SHADOW and
disable a block someone meant to enforce.
"""
import os

from .verdict import Hook, Mode

ENV_PREFIX = "GUARDRAIL_MODE__"


class ModeTable:
    def __init__(self, defaults: dict[Hook, list[tuple[str, Mode]]], env=None):
        self._defaults = defaults
        self._env = os.environ if env is None else env
        self._overrides: dict[str, Mode] = {}
        for name in self.validators():         # resolve every env value now, so a bad one stops startup
            self._from_env(name)

    def validators(self) -> list[str]:
        return sorted({name for chain in self._defaults.values() for name, _ in chain})

    def _from_env(self, name: str) -> Mode | None:
        key = ENV_PREFIX + name.replace(".", "__")
        raw = self._env.get(key)
        if raw is None or raw == "":
            return None
        try:
            return Mode(raw)
        except ValueError:
            raise ValueError(f"{key}={raw!r} is not a mode ({', '.join(m.value for m in Mode)})") from None

    def mode(self, name: str, default: Mode) -> Mode:
        if name in self._overrides:
            return self._overrides[name]
        return self._from_env(name) or default

    def chain(self, hook: Hook) -> list[tuple[str, Mode]]:
        return [(name, self.mode(name, default)) for name, default in self._defaults.get(hook, [])]

    def set_override(self, name: str, mode: Mode) -> None:
        if name not in self.validators():
            raise KeyError(f"unknown validator {name!r}")
        self._overrides[name] = mode

    def clear_overrides(self) -> None:
        self._overrides.clear()

    def overrides(self) -> dict[str, str]:
        return {k: v.value for k, v in self._overrides.items()}

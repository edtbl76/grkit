"""The kit is project-neutral: no lab hostname, private address, cluster DNS name or secret-looking value anywhere."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
FORBIDDEN = [
    (re.compile(r"weyland\.lab"), "a lab hostname"),
    (re.compile(r"\b192\.168\.\d+\.\d+\b"), "a private LAN address"),
    (re.compile(r"\.svc\.cluster\.local"), "an in-cluster DNS name"),
    (re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{12,}['\"]"), "a literal credential"),
]
SKIP = {".git", ".venv", "__pycache__", ".pytest_cache", ".tmp"}


def _files():
    for p in ROOT.rglob("*"):
        if p.is_file() and not SKIP & set(p.parts) and p.name != "test_repo_hygiene.py":
            yield p


def test_the_kit_carries_no_lab_specifics_or_secrets():
    hits = []
    for p in _files():
        text = p.read_text(encoding="utf-8", errors="ignore")
        for rx, what in FORBIDDEN:
            for m in rx.finditer(text):
                hits.append(f"{p.relative_to(ROOT)}: {what}: {m.group(0)[:40]}")
    assert hits == []


def test_the_scan_actually_saw_the_repo():
    names = {p.name for p in _files()}
    assert {"README.md", "verdict.py", "copier.yml"} <= names       # scanning nothing must not read as clean

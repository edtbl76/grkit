#!/usr/bin/env bash
# test.sh — the whole grkit test suite, in Docker as the invoking user (nothing installed on the host).
#   1. the package tests (pytest), incl. the repo-hygiene scan, and a real build + install of the package
#      from a copy of the WHOLE repo, as pip sees it from git (0.1.0 shipped un-installable — readme outside the
#      package dir — because nothing here installed it, and a copy of python/ alone does not reproduce that)
#   2. render the Copier template into a scratch dir (answers given non-interactively)
#   3. run the rendered guard's own bats tests (it must be seen failing with 1 and 2)
#   4. run the rendered guard on the rendered repo: it must pass (the template is self-consistent)
# Exit 0 only if every stage passed; the first failing stage's output is shown and the script exits non-zero.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRATCH="$ROOT/.tmp"
rm -rf "$SCRATCH" && mkdir -p "$SCRATCH"
trap 'rm -rf "$SCRATCH"' EXIT
USER_FLAGS=(--user "$(id -u):$(id -g)" -e HOME=/tmp -e PIP_USER=1 -e PYTHONUSERBASE=/tmp/pu -e PATH=/tmp/pu/bin:/usr/local/bin:/usr/bin:/bin)

echo "== 1/4 package tests"
docker run --rm "${USER_FLAGS[@]}" -v "$ROOT":/w -w /w/python python:3.12-slim \
  sh -c 'pip install -q --no-cache-dir pytest >/dev/null 2>&1 && python -m pytest -q -p no:cacheprovider'
docker run --rm "${USER_FLAGS[@]}" -v "$ROOT":/src:ro python:3.12-slim sh -c 'cp -r /src /tmp/repo && rm -rf /tmp/repo/.git /tmp/repo/.tmp && \
  pip install -q --no-cache-dir /tmp/repo/python >/dev/null 2>&1 && cd / && python -c "import grkit, grkit.client, grkit.modes, \
  grkit.pipeline, grkit.checks; print(\"installed grkit\", grkit.__version__)"'

echo "== 2/4 render the template"
docker run --rm "${USER_FLAGS[@]}" -v "$ROOT":/kit:ro -v "$SCRATCH":/out python:3.12-slim \
  sh -c 'pip install -q --no-cache-dir copier >/dev/null 2>&1 && copier copy --defaults --trust \
         --data project_name="Demo Project" --data project_summary="A rendered test of the grkit template." \
         /kit /out/demo >/dev/null && ls -A /out/demo'
for f in AGENTS.md docs/definition-of-done.md scripts/check-required-docs.sh scripts/tests/check-required-docs.bats \
         .grkit/required-docs .copier-answers.yml; do
  [ -s "$SCRATCH/demo/$f" ] || { echo "render missing or empty: $f" >&2; exit 1; }
done
grep -q '^# Demo Project — instructions for every coding agent' "$SCRATCH/demo/AGENTS.md" \
  || { echo "render did not substitute project_name into AGENTS.md" >&2; exit 1; }
if grep -rn '{{\|{%' "$SCRATCH/demo" --include='*.md' >/dev/null; then echo "unrendered Jinja left in the output" >&2; exit 1; fi

echo "== 3/4 the rendered guard's tests"
docker run --rm "${USER_FLAGS[@]}" -v "$SCRATCH/demo":/w:ro -w /w bats/bats:latest scripts/tests/check-required-docs.bats

echo "== 4/4 the rendered guard on the rendered repo"
docker run --rm "${USER_FLAGS[@]}" --entrypoint bash -v "$SCRATCH/demo":/w:ro -w /w bats/bats:latest \
  scripts/check-required-docs.sh

echo "grkit: all 4 stages passed"

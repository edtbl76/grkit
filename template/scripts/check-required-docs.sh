#!/usr/bin/env bash
# check-required-docs.sh — every document listed in .grkit/required-docs exists and has content (grkit worked guard).
#
# A fail-closed guard, the pattern every guard in this repo follows:
#   exit 0  clean — the check ran, and every listed document is present and non-empty
#   exit 1  findings — each missing or empty document is named
#   exit 2  could not check — no list, a list that names nothing, or a path outside the repo. NEVER a pass:
#           "verified nothing" must not look like "verified, all good".
#
# The list: one path per line, relative to the repo root; `#` starts a comment.
# Seams (tests): REQUIRED_DOCS_ROOT (repo root), REQUIRED_DOCS_LIST (the list file).
set -uo pipefail

ROOT="${REQUIRED_DOCS_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
LIST="${REQUIRED_DOCS_LIST:-$ROOT/.grkit/required-docs}"

if [ ! -r "$LIST" ]; then
  echo "check-required-docs: could not check — cannot read the list $LIST (.grkit/required-docs)" >&2
  exit 2
fi

findings=() checked=0
while IFS= read -r line || [ -n "$line" ]; do
  path="${line%%#*}"
  path="$(printf '%s' "$path" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"
  [ -n "$path" ] || continue
  case "/$path/" in
    */../*|//*) echo "check-required-docs: could not check — '$path' is outside the repo" >&2; exit 2 ;;
  esac
  checked=$((checked + 1))
  if [ ! -f "$ROOT/$path" ]; then
    findings+=("$path: missing")
  elif ! grep -q '[^[:space:]]' "$ROOT/$path"; then
    findings+=("$path: empty")
  fi
done < "$LIST"

if [ "$checked" -eq 0 ]; then
  echo "check-required-docs: could not check — $LIST lists no documents" >&2
  exit 2
fi
if [ "${#findings[@]}" -gt 0 ]; then
  printf '  ❌ %s\n' "${findings[@]}"
  echo "check-required-docs: ${#findings[@]} finding(s) of $checked document(s)"
  exit 1
fi
echo "check-required-docs: OK — $checked required document(s) present"

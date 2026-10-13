#!/usr/bin/env bats
# Tests for scripts/check-required-docs.sh — every document listed in .grkit/required-docs exists and is non-empty.
# Each exit code is seen happening, and each test asserts the REASON, not only the status (exit 127 is non-zero too).

setup() {
  SCRIPT="$BATS_TEST_DIRNAME/../check-required-docs.sh"
  export REQUIRED_DOCS_ROOT="$BATS_TEST_TMPDIR/repo"
  mkdir -p "$REQUIRED_DOCS_ROOT/docs" "$REQUIRED_DOCS_ROOT/.grkit"
  printf '# the documents this repo must carry\nAGENTS.md\ndocs/runbook.md\n' > "$REQUIRED_DOCS_ROOT/.grkit/required-docs"
  printf 'rules\n' > "$REQUIRED_DOCS_ROOT/AGENTS.md"
  printf 'how to run it\n' > "$REQUIRED_DOCS_ROOT/docs/runbook.md"
}

@test "every listed document present and non-empty => exit 0" {
  run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  [[ "$output" == *"OK — 2 required document(s) present"* ]]
}

@test "a missing document => exit 1 naming it" {
  rm "$REQUIRED_DOCS_ROOT/docs/runbook.md"
  run bash "$SCRIPT"
  [ "$status" -eq 1 ]
  [[ "$output" == *"docs/runbook.md: missing"* ]]
}

@test "a document with only whitespace => exit 1, empty is not present" {
  printf '  \n\n' > "$REQUIRED_DOCS_ROOT/AGENTS.md"
  run bash "$SCRIPT"
  [ "$status" -eq 1 ]
  [[ "$output" == *"AGENTS.md: empty"* ]]
}

@test "no list file => exit 2: could not check is never a pass" {
  rm "$REQUIRED_DOCS_ROOT/.grkit/required-docs"
  run bash "$SCRIPT"
  [ "$status" -eq 2 ]
  [[ "$output" == *"could not check"*"required-docs"* ]]
}

@test "a list with no entries => exit 2: checking nothing is not clean" {
  printf '# nothing yet\n\n' > "$REQUIRED_DOCS_ROOT/.grkit/required-docs"
  run bash "$SCRIPT"
  [ "$status" -eq 2 ]
  [[ "$output" == *"lists no documents"* ]]
}

@test "a listed path that escapes the repo is refused (exit 2)" {
  printf '../outside.md\n' > "$REQUIRED_DOCS_ROOT/.grkit/required-docs"
  run bash "$SCRIPT"
  [ "$status" -eq 2 ]
  [[ "$output" == *"outside the repo"* ]]
}

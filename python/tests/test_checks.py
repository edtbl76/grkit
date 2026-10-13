"""grkit.checks — a build-time check fails CLOSED: 0 clean · 1 findings (named) · 2 could not check (never a pass)."""
import pytest

from grkit.checks import Exit, run


def test_no_findings_is_exit_0(capsys):
    assert run("docs-present", lambda: []) == Exit.CLEAN == 0
    assert "docs-present: OK" in capsys.readouterr().out


def test_findings_are_exit_1_each_named(capsys):
    assert run("docs-present", lambda: ["README.md missing", "AGENTS.md empty"]) == Exit.FINDINGS == 1
    out = capsys.readouterr().out
    assert "README.md missing" in out and "AGENTS.md empty" in out and "2 finding(s)" in out


def test_an_exception_is_exit_2_with_the_reason(capsys):
    def boom():
        raise OSError("permission denied: /repo")
    assert run("docs-present", boom) == Exit.CANNOT_CHECK == 2
    err = capsys.readouterr().err
    assert "could not check" in err and "permission denied: /repo" in err


def test_an_absent_result_is_exit_2_not_clean(capsys):
    # the class this exists for: a check that returned nothing must not read as "found nothing"
    assert run("docs-present", lambda: None) == 2
    assert "returned no result" in capsys.readouterr().err


def test_a_non_list_result_is_exit_2(capsys):
    assert run("docs-present", lambda: "all good") == 2
    assert "expected a list of findings" in capsys.readouterr().err


@pytest.mark.parametrize("code", [0, 1, 2])
def test_exit_values_are_stable(code):
    assert Exit(code).value == code

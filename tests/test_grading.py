"""Unit tests for the grader."""

from __future__ import annotations

from eml_research.grading import grade
from eml_research.problems import Problem


def _p(**kwargs):
    defaults = {
        "pid": "t",
        "category": "test",
        "question": "q",
        "truth": None,
        "check": "exact",
        "eml_equals": None,
        "atol": 1e-6,
        "rtol": 1e-6,
        "tags": [],
    }
    defaults.update(kwargs)
    return Problem(**defaults)


def test_numeric_correct_within_tol():
    p = _p(check="numeric", truth=7.38905609893065, atol=1e-6, rtol=1e-6)
    v = grade("7.389056099", p)
    assert v.correct


def test_numeric_wrong():
    p = _p(check="numeric", truth=7.38905609893065, atol=1e-6, rtol=1e-6)
    v = grade("7.0", p)
    assert not v.correct


def test_exact_equivalent_forms():
    p = _p(check="exact", truth="E - 1")
    v = grade("-1 + E", p)
    assert v.correct, v.reason


def test_exact_wrong():
    p = _p(check="exact", truth="1/2")
    v = grade("1/3", p)
    assert not v.correct


def test_set_unordered():
    p = _p(check="set", truth=["1", "2"])
    v = grade("[2, 1]", p)
    assert v.correct


def test_set_wrong():
    p = _p(check="set", truth=["1", "2"])
    v = grade("[1, 3]", p)
    assert not v.correct


def test_eml_tree_correct():
    p = _p(check="eml_tree", truth="eml(x, 1)", eml_equals="exp(x)")
    v = grade("eml(x, 1)", p)
    assert v.correct, v.reason


def test_eml_tree_wrong():
    p = _p(check="eml_tree", truth="eml(x, 1)", eml_equals="exp(x)")
    v = grade("eml(1, x)", p)
    assert not v.correct


def test_missing_answer():
    p = _p(check="exact", truth="1")
    v = grade(None, p)
    assert not v.correct
    assert "FINAL ANSWER" in v.reason

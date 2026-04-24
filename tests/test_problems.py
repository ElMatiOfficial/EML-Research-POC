"""Validate that every benchmark problem's ground truth is actually correct.

These tests compute the expected answer via sympy / numpy and check that the
declared ``truth`` agrees. This guards against drift in the problem set and
means the benchmark can be trusted as a grader.
"""

from __future__ import annotations

import math

import pytest
import sympy

from eml_research.grading import grade
from eml_research.problems import PROBLEMS, by_pid


def test_every_problem_passes_its_own_grader_when_given_truth():
    """Feed each problem's ``truth`` back into the grader -- they must all pass."""
    for p in PROBLEMS:
        if p.check == "eml_tree":
            # truth already holds the EML form for these.
            answer = str(p.truth)
        elif p.check == "set":
            answer = str(list(p.truth))
        else:
            answer = str(p.truth)
        verdict = grade(answer, p)
        assert verdict.correct, f"{p.pid}: grader rejected its own truth -- {verdict.reason}"


def test_eml_identities_numerically_correct():
    """Paper identities must actually evaluate correctly."""
    import eml

    # exp(x) = eml(x, 1)
    tree = eml.parse("eml(x, 1)")
    assert abs(eml.evaluate(tree, {"x": 1.0}) - math.exp(1.0)) < 1e-12

    # ln(x) = eml(1, eml(eml(1, x), 1))
    tree = eml.parse("eml(1, eml(eml(1, x), 1))")
    for x in [0.5, 2.0, 10.0]:
        assert abs(eml.evaluate(tree, {"x": x}) - math.log(x)) < 1e-9

    # e = eml(1, 1)
    assert abs(complex(eml.evaluate(eml.parse("eml(1, 1)"))).real - math.e) < 1e-12


def test_kolmogorov_lengths_match_paper():
    import eml

    assert len(eml.to_rpn(eml.to_eml("exp(x)")).split()) == 3
    assert len(eml.to_rpn(eml.to_eml("log(x)")).split()) == 7
    # e = eml(1, 1) -> K=3
    assert len(eml.to_rpn(eml.parse("eml(1, 1)")).split()) == 3


def test_eval_01_exp_2():
    p = by_pid("eval-01")
    assert p is not None
    assert abs(float(p.truth) - math.exp(2)) < 1e-12


def test_eval_02_ln_10():
    p = by_pid("eval-02")
    assert p is not None
    assert abs(float(p.truth) - math.log(10)) < 1e-12


def test_calc_03_integral_of_exp_is_e_minus_1():
    p = by_pid("calc-03")
    assert p is not None
    # E - 1 as sympy
    truth = sympy.sympify(p.truth, locals={"E": sympy.E})
    assert abs(float(truth) - (math.e - 1)) < 1e-12


def test_calc_05_limit_is_e():
    p = by_pid("calc-05")
    assert p is not None
    truth = sympy.sympify(p.truth, locals={"E": sympy.E})
    assert truth == sympy.E


def test_alg_01_roots_are_pm_one():
    p = by_pid("alg-01")
    assert p is not None
    assert sorted(p.truth) == ["-1", "1"]


def test_problem_ids_are_unique():
    pids = [p.pid for p in PROBLEMS]
    assert len(pids) == len(set(pids))


# -- Hard-track ground-truth validation -----------------------------------

def test_hard_01_gaussian_integral():
    """integral_{-oo}^{oo} exp(-x^2) dx = sqrt(pi)"""
    import sympy as sp

    x = sp.Symbol("x")
    got = sp.integrate(sp.exp(-x**2), (x, -sp.oo, sp.oo))
    p = by_pid("hard-01")
    truth = sp.sympify(p.truth, locals={"pi": sp.pi, "sqrt": sp.sqrt})
    assert sp.simplify(got - truth) == 0


def test_hard_02_dirichlet_integral():
    """integral_0^{oo} sin(x)/x dx = pi/2"""
    import sympy as sp

    x = sp.Symbol("x", positive=True)
    got = sp.integrate(sp.sin(x) / x, (x, 0, sp.oo))
    p = by_pid("hard-02")
    truth = sp.sympify(p.truth, locals={"pi": sp.pi})
    assert sp.simplify(got - truth) == 0


def test_hard_03_quartic_reciprocal():
    """integral_0^{oo} 1/(x**4 + 1) dx = sqrt(2)*pi/4"""
    import sympy as sp

    x = sp.Symbol("x", positive=True)
    got = sp.integrate(1 / (x**4 + 1), (x, 0, sp.oo))
    p = by_pid("hard-03")
    truth = sp.sympify(p.truth, locals={"pi": sp.pi, "sqrt": sp.sqrt})
    assert sp.simplify(got - truth) == 0


def test_hard_04_stirling_limit():
    """lim n!/(n^n * e^{-n} * sqrt(n)) = sqrt(2*pi)"""
    import sympy as sp

    n = sp.Symbol("n", positive=True)
    got = sp.limit(
        sp.factorial(n) / (n**n * sp.exp(-n) * sp.sqrt(n)), n, sp.oo
    )
    p = by_pid("hard-04")
    truth = sp.sympify(p.truth, locals={"pi": sp.pi, "sqrt": sp.sqrt})
    assert sp.simplify(got - truth) == 0


def test_hard_05_nested_limit():
    """lim ((1+x)^{1/x} - E)/x as x->0 is -E/2"""
    import sympy as sp

    x = sp.Symbol("x")
    got = sp.limit(((1 + x) ** (1 / x) - sp.E) / x, x, 0)
    p = by_pid("hard-05")
    truth = sp.sympify(p.truth, locals={"E": sp.E})
    assert sp.simplify(got - truth) == 0

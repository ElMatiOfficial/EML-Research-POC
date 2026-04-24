"""Benchmark problems with verified ground-truth answers.

Each problem exercises either the EML path explicitly (e.g. "translate exp(x)
to EML") or a classical math skill with a known closed form that the agent can
solve via its tools. Ground truths are sympy expressions and are validated at
import time by tests/test_problems.py.

Check categories:
    numeric   - compare as a float within atol/rtol
    exact     - sympy.simplify(answer - truth) == 0
    set       - compare as unordered sets of sympy expressions
    eml_tree  - parse the agent's EML string and verify it equals the given math
    string    - fallback case-insensitive string compare (rare)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Problem:
    pid: str
    category: str  # "eml", "calculus", "algebra", "evaluation"
    question: str
    truth: Any  # sympy expression, number, list, or string — interpreted by `check`
    check: str  # "numeric" | "exact" | "set" | "eml_tree" | "string"
    # Optional metadata for eml_tree checks: the equivalent math expression to
    # numerically compare the agent's EML tree against.
    eml_equals: str | None = None
    # For numeric checks: tolerance overrides.
    atol: float = 1e-6
    rtol: float = 1e-6
    tags: list[str] = field(default_factory=list)


PROBLEMS: list[Problem] = [
    # --- EML-native warmups --------------------------------------------------
    Problem(
        pid="eml-01",
        category="eml",
        question=(
            "Translate exp(x) into its EML tree (exp-minus-log form). "
            "Return the textual EML expression as the final answer."
        ),
        truth="eml(x, 1)",
        check="eml_tree",
        eml_equals="exp(x)",
        tags=["translate", "paper-identity"],
    ),
    Problem(
        pid="eml-02",
        category="eml",
        question=(
            "Translate ln(x) into its EML tree. Return the textual EML expression "
            "as the final answer."
        ),
        truth="eml(1, eml(eml(1, x), 1))",
        check="eml_tree",
        eml_equals="log(x)",
        tags=["translate", "paper-identity"],
    ),
    Problem(
        pid="eml-03",
        category="eml",
        question="What is the Kolmogorov length K (RPN token count) of ln(x) in EML? Return a single integer.",
        truth=7,
        check="exact",
        tags=["kolmogorov-length"],
    ),
    Problem(
        pid="eml-04",
        category="eml",
        question=(
            "What is the EML tree for Euler's number e, and what is its Kolmogorov length K? "
            "Return just K as a single integer."
        ),
        truth=3,
        check="exact",
        tags=["kolmogorov-length"],
    ),
    Problem(
        pid="eml-05",
        category="eml",
        question=(
            "Using the EML tools, translate exp(x) - 1 to EML and report the size of the tree "
            "(total node count). Return a single integer."
        ),
        # exp(x) - 1 = minus_one(exp(x)) = eml(ln(exp(x)), e). size(ln(exp(x)))=9, e=3, outer=1 -> 13.
        truth=13,
        check="exact",
        tags=["tree-size"],
    ),
    # --- Evaluation ----------------------------------------------------------
    Problem(
        pid="eval-01",
        category="evaluation",
        question="Evaluate exp(2) numerically. Use the EML representation of exp.",
        truth=7.38905609893065,
        check="numeric",
        atol=1e-9,
        rtol=1e-9,
        tags=["numeric", "eml-path"],
    ),
    Problem(
        pid="eval-02",
        category="evaluation",
        question="Evaluate ln(10) numerically. Use the EML representation of ln.",
        truth=2.302585092994046,
        check="numeric",
        atol=1e-9,
        rtol=1e-9,
        tags=["numeric", "eml-path"],
    ),
    Problem(
        pid="eval-03",
        category="evaluation",
        question="Evaluate exp(1) - 1 numerically.",
        truth=1.718281828459045,
        check="numeric",
        atol=1e-9,
        rtol=1e-9,
        tags=["numeric"],
    ),
    # --- Calculus (sympy escape hatch expected) ------------------------------
    Problem(
        pid="calc-01",
        category="calculus",
        question="Compute d/dx [exp(x)] at x = 0. Return the exact value.",
        truth=1,
        check="exact",
        tags=["derivative"],
    ),
    Problem(
        pid="calc-02",
        category="calculus",
        question="Compute the definite integral of x from 0 to 1. Return the exact value.",
        truth="1/2",
        check="exact",
        tags=["integral"],
    ),
    Problem(
        pid="calc-03",
        category="calculus",
        question="Compute the definite integral of exp(x) from 0 to 1. Return the exact value.",
        truth="E - 1",
        check="exact",
        tags=["integral", "eml-relevant"],
    ),
    Problem(
        pid="calc-04",
        category="calculus",
        question="Compute lim_{x -> 0} sin(x)/x. Return the exact value.",
        truth=1,
        check="exact",
        tags=["limit"],
    ),
    Problem(
        pid="calc-05",
        category="calculus",
        question="Compute lim_{x -> infinity} (1 + 1/x)^x. Return the exact value.",
        truth="E",
        check="exact",
        tags=["limit", "eml-relevant"],
    ),
    # --- Algebra -------------------------------------------------------------
    Problem(
        pid="alg-01",
        category="algebra",
        question="Solve x**2 - 1 = 0 for x. Return the solution set as a Python list.",
        truth=["-1", "1"],
        check="set",
        tags=["polynomial-roots"],
    ),
    Problem(
        pid="alg-02",
        category="algebra",
        question="Solve x**2 - 3*x + 2 = 0 for x. Return the solution set as a Python list.",
        truth=["1", "2"],
        check="set",
        tags=["polynomial-roots"],
    ),
    Problem(
        pid="alg-03",
        category="algebra",
        question="Simplify exp(log(x)) assuming x > 0. Return the simplified expression.",
        truth="x",
        check="exact",
        tags=["simplify", "eml-relevant"],
    ),
]


def by_pid(pid: str) -> Problem | None:
    return next((p for p in PROBLEMS if p.pid == pid), None)

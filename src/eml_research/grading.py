"""Grade an agent's answer against a ground truth.

Each problem declares a ``check`` strategy (numeric / exact / set / eml_tree /
string) and the grader returns a structured verdict so downstream reports can
show *why* an answer was wrong.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sympy

import eml
from eml.parser import ParseError


@dataclass
class Verdict:
    correct: bool
    reason: str
    normalized_answer: str | None = None
    normalized_truth: str | None = None
    diff: float | None = None


_SYMPY_LOCALS = {
    "pi": sympy.pi,
    "E": sympy.E,
    "I": sympy.I,
    "oo": sympy.oo,
    "exp": sympy.exp,
    "log": sympy.log,
    "ln": sympy.log,
    "sin": sympy.sin,
    "cos": sympy.cos,
    "tan": sympy.tan,
    "sqrt": sympy.sqrt,
}


def _as_sympy(value: Any) -> sympy.Expr:
    if isinstance(value, sympy.Expr):
        return value
    if isinstance(value, (int, float)):
        return sympy.sympify(value)
    return sympy.sympify(str(value), locals=_SYMPY_LOCALS)


def _strip_answer(ans: str) -> str:
    ans = ans.strip()
    # Strip enclosing backticks or $...$
    while ans.startswith("`") and ans.endswith("`"):
        ans = ans[1:-1].strip()
    if ans.startswith("$") and ans.endswith("$"):
        ans = ans[1:-1].strip()
    return ans


def grade(answer: str | None, problem) -> Verdict:
    if answer is None or not answer.strip():
        return Verdict(correct=False, reason="no FINAL ANSWER emitted")
    answer = _strip_answer(answer)

    check = problem.check

    if check == "numeric":
        return _grade_numeric(answer, problem)
    if check == "exact":
        return _grade_exact(answer, problem)
    if check == "set":
        return _grade_set(answer, problem)
    if check == "eml_tree":
        return _grade_eml_tree(answer, problem)
    if check == "string":
        return _grade_string(answer, problem)
    return Verdict(correct=False, reason=f"unknown check strategy {check!r}")


def _grade_numeric(answer: str, problem) -> Verdict:
    try:
        expr = _as_sympy(answer)
        value = float(expr.evalf())
    except Exception as err:
        return Verdict(
            correct=False,
            reason=f"could not parse {answer!r} as number: {err}",
            normalized_answer=answer,
        )
    truth = float(problem.truth)
    diff = abs(value - truth)
    tol = max(problem.atol, problem.rtol * abs(truth))
    return Verdict(
        correct=diff <= tol,
        reason=f"|diff|={diff:.3e}, tol={tol:.3e}",
        normalized_answer=str(value),
        normalized_truth=str(truth),
        diff=diff,
    )


def _grade_exact(answer: str, problem) -> Verdict:
    try:
        ans_expr = _as_sympy(answer)
        truth_expr = _as_sympy(problem.truth)
    except Exception as err:
        return Verdict(
            correct=False,
            reason=f"parse failure: {err}",
            normalized_answer=answer,
            normalized_truth=str(problem.truth),
        )
    try:
        diff = sympy.simplify(ans_expr - truth_expr)
    except Exception as err:
        return Verdict(
            correct=False,
            reason=f"sympy.simplify failed: {err}",
            normalized_answer=str(ans_expr),
            normalized_truth=str(truth_expr),
        )
    correct = diff == 0
    return Verdict(
        correct=correct,
        reason="exact match" if correct else f"simplify(a - t) = {diff}",
        normalized_answer=str(ans_expr),
        normalized_truth=str(truth_expr),
    )


def _grade_set(answer: str, problem) -> Verdict:
    # Try to parse as a Python list / sympy set.
    import ast

    try:
        parsed = ast.literal_eval(answer)
        items = list(parsed) if isinstance(parsed, (list, tuple, set)) else [parsed]
    except Exception:
        # Fall back: split on comma/semicolon, allow { } or [ ] wrappers.
        stripped = answer.strip().lstrip("[{(").rstrip("]})")
        items = [s for s in (p.strip() for p in stripped.split(",")) if s]

    try:
        ans_set = {sympy.simplify(_as_sympy(str(x))) for x in items}
        truth_set = {sympy.simplify(_as_sympy(str(x))) for x in problem.truth}
    except Exception as err:
        return Verdict(correct=False, reason=f"parse failure: {err}")

    correct = ans_set == truth_set
    return Verdict(
        correct=correct,
        reason="set match" if correct else f"diff={ans_set.symmetric_difference(truth_set)}",
        normalized_answer=str(sorted(map(str, ans_set))),
        normalized_truth=str(sorted(map(str, truth_set))),
    )


def _grade_eml_tree(answer: str, problem) -> Verdict:
    try:
        if "(" in answer:
            tree = eml.parse(answer)
        else:
            tree = eml.parse_rpn(answer)
    except ParseError as err:
        return Verdict(
            correct=False,
            reason=f"could not parse EML {answer!r}: {err}",
            normalized_answer=answer,
            normalized_truth=str(problem.truth),
        )
    target_src = problem.eml_equals or problem.truth
    try:
        target_expr = _as_sympy(target_src)
    except Exception as err:
        return Verdict(correct=False, reason=f"bad eml_equals: {err}")

    variables = sorted({s.name for s in target_expr.free_symbols})
    if not variables:
        import cmath

        lhs = complex(eml.evaluate(tree))
        rhs = complex(target_expr)
        diff = abs(lhs - rhs)
        return Verdict(
            correct=diff < 1e-9,
            reason=f"|lhs-rhs|={diff:.3e}",
            normalized_answer=eml.to_text(tree),
            normalized_truth=str(target_expr),
            diff=diff,
        )

    target_fn = sympy.lambdify(variables, target_expr, modules="cmath")
    from eml.search import verify_match

    ok = verify_match(tree, target_fn, variables)
    return Verdict(
        correct=bool(ok),
        reason="EML tree matches target on sample grid" if ok else "EML tree differs from target on sample grid",
        normalized_answer=eml.to_text(tree),
        normalized_truth=str(target_expr),
    )


def _grade_string(answer: str, problem) -> Verdict:
    correct = answer.strip().lower() == str(problem.truth).strip().lower()
    return Verdict(
        correct=correct,
        reason="string match" if correct else "string mismatch",
        normalized_answer=answer.strip(),
        normalized_truth=str(problem.truth).strip(),
    )

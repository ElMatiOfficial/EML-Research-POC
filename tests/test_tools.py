"""Unit tests for the EML tool adapters (no Anthropic API involvement)."""

from __future__ import annotations

import json

import pytest

from eml_research.tools import TOOL_DEFINITIONS, run_tool


def _call(name: str, **kwargs):
    return json.loads(run_tool(name, kwargs))


def test_tool_definitions_are_valid_shapes():
    names = {t["name"] for t in TOOL_DEFINITIONS}
    assert names == {
        "math_to_eml",
        "eml_to_math",
        "evaluate_eml",
        "list_eml_identities",
        "search_eml_identity",
        "verify_eml",
        "sympy_compute",
    }
    for t in TOOL_DEFINITIONS:
        assert set(t.keys()) == {"name", "description", "input_schema"}
        schema = t["input_schema"]
        assert schema["type"] == "object"
        assert "properties" in schema


def test_math_to_eml_exp():
    out = _call("math_to_eml", expression="exp(x)")
    assert out["status"] == "ok"
    assert out["text"] == "eml(x, 1)"
    assert out["kolmogorov_length"] == 3


def test_math_to_eml_log_has_k_7():
    out = _call("math_to_eml", expression="log(x)")
    assert out["status"] == "ok"
    assert out["kolmogorov_length"] == 7


def test_eml_to_math_roundtrip():
    out = _call("eml_to_math", eml_expression="eml(x, 1)")
    assert out["status"] == "ok"
    assert out["math"] == "exp(x)"


def test_evaluate_eml_numeric():
    out = _call("evaluate_eml", eml_expression="eml(x, 1)", bindings={"x": 2.0})
    assert out["status"] == "ok"
    assert abs(out["value"] - 7.38905609893065) < 1e-9


def test_evaluate_eml_missing_binding():
    out = _call("evaluate_eml", eml_expression="eml(x, 1)")
    assert out["status"] == "error"
    assert "variable" in out["message"].lower()


def test_list_eml_identities_has_canonicals():
    out = _call("list_eml_identities")
    assert out["status"] == "ok"
    names = {row["name"] for row in out["identities"]}
    assert {"exp", "ln", "e", "zero", "sub"}.issubset(names)


def test_search_eml_identity_finds_exp():
    out = _call("search_eml_identity", target="exp(x)", variables=["x"], max_size=5, max_results=1)
    assert out["status"] == "ok"
    assert out["matches"]
    assert out["matches"][0]["text"] == "eml(x, 1)"


def test_search_eml_identity_respects_max_size_cap():
    out = _call("search_eml_identity", target="exp(x)", variables=["x"], max_size=20)
    assert out["status"] == "error"


def test_verify_eml_success():
    out = _call("verify_eml", eml_expression="eml(x, 1)", math_expression="exp(x)")
    assert out["status"] == "ok"
    assert out["match"] is True


def test_verify_eml_failure():
    out = _call("verify_eml", eml_expression="eml(x, 1)", math_expression="log(x)")
    assert out["status"] == "ok"
    assert out["match"] is False


def test_sympy_compute_diff():
    out = _call("sympy_compute", op="diff", expression="exp(x)", variable="x")
    assert out["status"] == "ok"
    assert out["result"] == "exp(x)"


def test_sympy_compute_definite_integral():
    out = _call("sympy_compute", op="integrate", expression="x", variable="x", bounds=[0, 1])
    assert out["status"] == "ok"
    assert out["result"] == "1/2"
    assert out["numeric"] == 0.5


def test_sympy_compute_solve_quadratic():
    out = _call("sympy_compute", op="solve", expression="x**2 - 1", variable="x")
    assert out["status"] == "ok"
    # sympy returns [-1, 1]
    assert "1" in out["result"] and "-1" in out["result"]


def test_sympy_compute_limit_e():
    out = _call("sympy_compute", op="limit", expression="(1 + 1/x)**x", variable="x", point=float("inf"))
    # sympy prints oo for infinity; allow either "E" or stringified float
    assert out["status"] == "ok"


def test_unknown_tool_returns_error():
    raw = run_tool("does_not_exist", {})
    payload = json.loads(raw)
    assert payload["status"] == "error"


# -- Extended sympy_compute: string bounds / point / diff order -----------

def test_sympy_compute_integrate_infinite_bounds():
    out = _call(
        "sympy_compute",
        op="integrate",
        expression="exp(-x**2)",
        variable="x",
        bounds=["-oo", "oo"],
    )
    assert out["status"] == "ok"
    assert out["result"] == "sqrt(pi)"


def test_sympy_compute_integrate_symbolic_upper_bound():
    # integral_0^{pi/2} cos(x) dx = 1
    out = _call(
        "sympy_compute",
        op="integrate",
        expression="cos(x)",
        variable="x",
        bounds=[0, "pi/2"],
    )
    assert out["status"] == "ok"
    assert out["result"] == "1"


def test_sympy_compute_limit_at_infinity_string():
    out = _call(
        "sympy_compute",
        op="limit",
        expression="1/x",
        variable="x",
        point="oo",
    )
    assert out["status"] == "ok"
    assert out["result"] == "0"


def test_sympy_compute_diff_higher_order():
    # d^2/dx^2 [x**3] = 6*x
    out = _call("sympy_compute", op="diff", expression="x**3", variable="x", order=2)
    assert out["status"] == "ok"
    assert out["result"] == "6*x"


def test_sympy_compute_factorial_available():
    # sympify should accept factorial now
    out = _call("sympy_compute", op="simplify", expression="factorial(5)")
    assert out["status"] == "ok"
    assert out["result"] == "120"

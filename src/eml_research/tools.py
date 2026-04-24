"""EML-flavored tools exposed to the Claude agent via tool-use.

The agent gets a focused toolbox built around the EML primitive:

* ``math_to_eml``        - translate standard math into an EML tree
* ``eml_to_math``        - translate an EML tree back into a sympy expression
* ``evaluate_eml``       - numerically evaluate an EML tree at a given binding
* ``list_eml_identities`` - inspect the registered EML identities
* ``search_eml_identity`` - exhaustively search for an EML decomposition
* ``verify_eml``         - check an EML tree equals a math expression numerically
* ``sympy_compute``      - safe sympy evaluator (simplify, solve, integrate, diff, limit)

The first six are pure EML ops and keep the agent thinking in the paper's
primitive. ``sympy_compute`` is a deliberate escape hatch: Odrzywolek's paper
notes that many elementary operators (multiplication K=41, sin, cos, sqrt, ...)
have Kolmogorov length beyond brute-force search, so a symbolic-math backend
is the realistic way to get final answers to benchmark problems the EML
library does not yet register.
"""

from __future__ import annotations

import cmath
import json
import math
from typing import Any

import sympy

import eml
from eml.forward import TranslationError
from eml.parser import ParseError


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "math_to_eml",
        "description": (
            "Translate a standard math expression into an EML (Exp-Minus-Log) tree. "
            "EML defines eml(x, y) = exp(x) - ln(y); Odrzywolek (2026, arXiv:2603.21852) "
            "shows every elementary function is expressible over the single literal 1 and "
            "nested eml(...) calls. Returns the EML tree in multiple forms plus its "
            "Kolmogorov length K (RPN token count). "
            "Use this to put a problem into normal form before reasoning."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A sympy-parseable expression, e.g. 'exp(x) - 1' or 'log(x)'.",
                },
            },
            "required": ["expression"],
            "additionalProperties": False,
        },
    },
    {
        "name": "eml_to_math",
        "description": (
            "Translate an EML tree back into standard mathematical notation "
            "(a simplified sympy expression). Accepts either textual form like "
            "'eml(x, 1)' or RPN form like 'x 1 eml'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "eml_expression": {
                    "type": "string",
                    "description": "EML tree in textual or RPN form.",
                },
                "simplify": {
                    "type": "boolean",
                    "description": "Whether to run sympy.simplify on the result. Default true.",
                },
            },
            "required": ["eml_expression"],
            "additionalProperties": False,
        },
    },
    {
        "name": "evaluate_eml",
        "description": (
            "Numerically evaluate an EML tree at a given variable binding. "
            "Uses the principal branch of the complex logarithm."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "eml_expression": {
                    "type": "string",
                    "description": "EML tree in textual or RPN form.",
                },
                "bindings": {
                    "type": "object",
                    "description": "Map of variable name -> real number value.",
                    "additionalProperties": {"type": "number"},
                },
            },
            "required": ["eml_expression"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_eml_identities",
        "description": (
            "List every EML identity currently registered in the library "
            "(e.g. exp, ln, e, zero, sub, one_minus, minus_one). Returns the "
            "builder name, parameter list, and the EML-tree template."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "search_eml_identity",
        "description": (
            "Exhaustively search for an EML decomposition of a target math expression. "
            "Enumerates EML trees up to max_size and returns those that match the target "
            "numerically on a sample grid. Search is exponential in max_size; "
            "practical values are 3..9 for a single variable."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Target math expression, e.g. 'exp(x)' or 'exp(x) - 1'.",
                },
                "variables": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Variable names, e.g. ['x'] or ['x','y'].",
                },
                "max_size": {
                    "type": "integer",
                    "description": "Max tree size (total node count). Default 7.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Stop after this many matches. Default 3.",
                },
            },
            "required": ["target"],
            "additionalProperties": False,
        },
    },
    {
        "name": "verify_eml",
        "description": (
            "Check numerically that an EML tree equals a standard math expression. "
            "Samples both on a grid and reports whether they agree within 1e-8."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "eml_expression": {
                    "type": "string",
                    "description": "EML tree in textual or RPN form.",
                },
                "math_expression": {
                    "type": "string",
                    "description": "Target math expression to compare against.",
                },
            },
            "required": ["eml_expression", "math_expression"],
            "additionalProperties": False,
        },
    },
    {
        "name": "sympy_compute",
        "description": (
            "Symbolic-math escape hatch. Many elementary operations have EML-length "
            "beyond brute-force search (multiplication K=41, sin/cos/pi K>100, etc.); "
            "use this tool to get a final answer when pure EML would be impractical. "
            "Supported ops: 'simplify', 'evalf', 'solve', 'integrate', 'diff', 'limit', "
            "'series', 'factor', 'expand'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "op": {
                    "type": "string",
                    "enum": [
                        "simplify",
                        "evalf",
                        "solve",
                        "integrate",
                        "diff",
                        "limit",
                        "series",
                        "factor",
                        "expand",
                    ],
                },
                "expression": {
                    "type": "string",
                    "description": "sympy-parseable expression.",
                },
                "variable": {
                    "type": "string",
                    "description": "Variable of integration/differentiation/etc. Not used by simplify/evalf/factor/expand.",
                },
                "point": {
                    "type": ["number", "string"],
                    "description": "Point for 'limit' / expansion point for 'series'. Strings are sympified so you can pass 'oo', '-oo', 'pi', 'pi/2', 'E', etc.",
                },
                "bounds": {
                    "type": "array",
                    "items": {"type": ["number", "string"]},
                    "description": "[lower, upper] for definite 'integrate'. Each bound may be a number or a sympy-parseable string (e.g. 'oo', '-oo', 'pi/2'). Omit for indefinite.",
                },
                "order": {
                    "type": "integer",
                    "description": "Derivative order for 'diff' (default 1); truncation order for 'series' (default 6).",
                },
                "precision": {
                    "type": "integer",
                    "description": "Digits for 'evalf'. Default 15.",
                },
            },
            "required": ["op", "expression"],
            "additionalProperties": False,
        },
    },
]


def _ok(payload: dict[str, Any]) -> str:
    return json.dumps({"status": "ok", **payload}, default=str)


def _err(message: str, hint: str | None = None) -> str:
    body: dict[str, Any] = {"status": "error", "message": message}
    if hint:
        body["hint"] = hint
    return json.dumps(body)


def _tool_math_to_eml(args: dict[str, Any]) -> str:
    expr = args["expression"]
    try:
        tree = eml.to_eml(expr)
    except (TranslationError, sympy.SympifyError, Exception) as err:
        return _err(
            f"Could not translate {expr!r} to EML: {err}",
            hint="Try simpler subexpressions or use search_eml_identity / sympy_compute.",
        )
    rpn = eml.to_rpn(tree)
    return _ok(
        {
            "text": eml.to_text(tree),
            "rpn": rpn,
            "latex": eml.to_latex(tree),
            "size": eml.tree_size(tree),
            "kolmogorov_length": len(rpn.split()),
        }
    )


def _parse_eml(src: str):
    src = src.strip()
    if "(" in src:
        return eml.parse(src)
    return eml.parse_rpn(src)


def _tool_eml_to_math(args: dict[str, Any]) -> str:
    src = args["eml_expression"]
    simplify = bool(args.get("simplify", True))
    try:
        tree = _parse_eml(src)
    except ParseError as err:
        return _err(f"Could not parse EML {src!r}: {err}")
    result = eml.from_eml(tree, simplify=simplify)
    return _ok({"math": str(result), "latex": sympy.latex(result)})


def _tool_evaluate_eml(args: dict[str, Any]) -> str:
    src = args["eml_expression"]
    bindings = args.get("bindings") or {}
    try:
        tree = _parse_eml(src)
    except ParseError as err:
        return _err(f"Could not parse EML {src!r}: {err}")
    try:
        value = eml.evaluate(tree, bindings)
    except KeyError as err:
        return _err(
            f"Missing variable binding: {err}",
            hint="Pass every free variable in bindings: {'x': 2.0, ...}",
        )
    except (ValueError, OverflowError, ZeroDivisionError) as err:
        return _err(f"Numeric failure: {err}")
    if isinstance(value, complex):
        out: dict[str, Any] = {"real": value.real, "imag": value.imag}
        if abs(value.imag) < 1e-12:
            out["value"] = value.real
        else:
            out["value"] = f"{value.real}+{value.imag}j"
    else:
        out = {"value": float(value)}
    return _ok(out)


def _tool_list_eml_identities(args: dict[str, Any]) -> str:
    import inspect
    from eml.ast import Var

    rows: list[dict[str, Any]] = []
    for name, builder in sorted(eml.IDENTITIES.items()):
        params = list(inspect.signature(builder).parameters)
        arg_nodes = [Var(p) for p in params]
        tree = builder(*arg_nodes)
        rows.append(
            {
                "name": name,
                "arity": len(params),
                "parameters": params,
                "eml_template": eml.to_text(tree),
                "kolmogorov_length": len(eml.to_rpn(tree).split()),
            }
        )
    return _ok({"identities": rows})


def _tool_search_eml_identity(args: dict[str, Any]) -> str:
    target_expr = args["target"]
    variables = args.get("variables") or ["x"]
    max_size = int(args.get("max_size", 7))
    max_results = int(args.get("max_results", 3))
    if max_size > 11:
        return _err(
            f"max_size={max_size} is beyond practical brute-force limits.",
            hint="Stay <= 11. For large identities use sympy_compute instead.",
        )
    try:
        expr = sympy.sympify(target_expr)
    except sympy.SympifyError as err:
        return _err(f"Could not parse target {target_expr!r}: {err}")
    free = sorted({s.name for s in expr.free_symbols})
    if free and set(free) - set(variables):
        return _err(
            f"Target has free variables {free} but search variables are {variables}.",
            hint="Pass variables=['x'] (etc.) covering every free symbol.",
        )
    try:
        target_fn = sympy.lambdify(variables, expr, modules="cmath")
    except Exception as err:
        return _err(f"Could not lambdify {target_expr!r}: {err}")
    # For 0-arity targets (constants), lambdify still works with variables=[]; otherwise search needs
    # at least one variable. If the caller passed none and the target is a constant, supply a dummy.
    search_vars = variables or []
    try:
        matches = eml.search_identity(
            target_fn,
            variables=search_vars,
            max_size=max_size,
            max_results=max_results,
        )
    except Exception as err:
        return _err(f"search_identity failed: {err}")
    if not matches:
        return _ok(
            {
                "matches": [],
                "note": f"No EML tree up to size {max_size} matches {target_expr!r}.",
            }
        )
    out = []
    for t in matches:
        rpn = eml.to_rpn(t)
        out.append(
            {
                "text": eml.to_text(t),
                "rpn": rpn,
                "size": eml.tree_size(t),
                "kolmogorov_length": len(rpn.split()),
            }
        )
    return _ok({"matches": out})


def _tool_verify_eml(args: dict[str, Any]) -> str:
    eml_src = args["eml_expression"]
    math_src = args["math_expression"]
    try:
        tree = _parse_eml(eml_src)
    except ParseError as err:
        return _err(f"Could not parse EML {eml_src!r}: {err}")
    try:
        math_expr = sympy.sympify(math_src)
    except sympy.SympifyError as err:
        return _err(f"Could not parse math {math_src!r}: {err}")

    variables = sorted({s.name for s in math_expr.free_symbols})
    if not variables:
        try:
            lhs = complex(eml.evaluate(tree))
            rhs = complex(math_expr)
        except Exception as err:
            return _err(f"Numeric evaluation failed: {err}")
        diff = abs(lhs - rhs)
        return _ok(
            {
                "match": diff < 1e-9,
                "diff": diff,
                "lhs": str(lhs),
                "rhs": str(rhs),
            }
        )

    target_fn = sympy.lambdify(variables, math_expr, modules="cmath")
    from eml.search import verify_match

    ok = verify_match(tree, target_fn, variables)
    return _ok({"match": bool(ok), "variables": variables})


_SYMPY_LOCALS: dict[str, Any] = {
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
    "asin": sympy.asin,
    "acos": sympy.acos,
    "atan": sympy.atan,
    "sinh": sympy.sinh,
    "cosh": sympy.cosh,
    "tanh": sympy.tanh,
    "sqrt": sympy.sqrt,
    "Abs": sympy.Abs,
    "factorial": sympy.factorial,
    "gamma": sympy.gamma,
    "zeta": sympy.zeta,
    "erf": sympy.erf,
}


def _parse_math(src: str) -> sympy.Expr:
    return sympy.sympify(src, locals=_SYMPY_LOCALS)


def _parse_bound(value: Any) -> sympy.Expr:
    """Coerce an integrate bound or limit point to a sympy expression.

    Accepts a plain number (JSON doesn't carry infinity) or a sympy-parseable
    string like 'oo', '-oo', 'pi/2', 'E'.
    """
    if isinstance(value, (int, float)):
        return sympy.Float(value) if isinstance(value, float) else sympy.Integer(value)
    return sympy.sympify(str(value), locals=_SYMPY_LOCALS)


def _tool_sympy_compute(args: dict[str, Any]) -> str:
    op = args["op"]
    expr_src = args["expression"]
    try:
        expr = _parse_math(expr_src)
    except sympy.SympifyError as err:
        return _err(f"Could not parse {expr_src!r}: {err}")

    var_name = args.get("variable")
    symbol = sympy.Symbol(var_name) if var_name else None

    try:
        if op == "simplify":
            result: Any = sympy.simplify(expr)
        elif op == "expand":
            result = sympy.expand(expr)
        elif op == "factor":
            result = sympy.factor(expr)
        elif op == "evalf":
            precision = int(args.get("precision", 15))
            result = expr.evalf(precision)
        elif op == "solve":
            if symbol is None:
                return _err("'solve' requires 'variable'.")
            result = sympy.solve(expr, symbol)
        elif op == "diff":
            if symbol is None:
                return _err("'diff' requires 'variable'.")
            order = int(args.get("order", 1))
            result = sympy.diff(expr, symbol, order)
        elif op == "integrate":
            if symbol is None:
                return _err("'integrate' requires 'variable'.")
            bounds = args.get("bounds")
            if bounds:
                if len(bounds) != 2:
                    return _err("'bounds' must be [lower, upper].")
                lower = _parse_bound(bounds[0])
                upper = _parse_bound(bounds[1])
                result = sympy.integrate(expr, (symbol, lower, upper))
            else:
                result = sympy.integrate(expr, symbol)
        elif op == "limit":
            if symbol is None:
                return _err("'limit' requires 'variable'.")
            point = _parse_bound(args.get("point", 0))
            result = sympy.limit(expr, symbol, point)
        elif op == "series":
            if symbol is None:
                return _err("'series' requires 'variable'.")
            point = _parse_bound(args.get("point", 0))
            order = int(args.get("order", 6))
            result = sympy.series(expr, symbol, point, order).removeO()
        else:
            return _err(f"Unknown op {op!r}.")
    except Exception as err:
        return _err(f"sympy.{op} failed: {err}")

    # Best-effort numeric form for the agent.
    numeric: Any = None
    try:
        if isinstance(result, (list, tuple)):
            numeric = [float(x) if x.is_real else complex(x) for x in (sympy.sympify(r) for r in result)]
        elif hasattr(result, "is_number") and result.is_number:
            n = complex(result)
            numeric = n.real if abs(n.imag) < 1e-12 else f"{n.real}+{n.imag}j"
    except Exception:
        numeric = None

    return _ok(
        {
            "result": str(result),
            "latex": sympy.latex(result) if not isinstance(result, (list, tuple)) else None,
            "numeric": numeric,
        }
    )


TOOL_DISPATCH: dict[str, Any] = {
    "math_to_eml": _tool_math_to_eml,
    "eml_to_math": _tool_eml_to_math,
    "evaluate_eml": _tool_evaluate_eml,
    "list_eml_identities": _tool_list_eml_identities,
    "search_eml_identity": _tool_search_eml_identity,
    "verify_eml": _tool_verify_eml,
    "sympy_compute": _tool_sympy_compute,
}


def run_tool(name: str, arguments: dict[str, Any]) -> str:
    """Execute a tool by name and return the JSON-encoded tool_result string."""
    fn = TOOL_DISPATCH.get(name)
    if fn is None:
        return _err(f"Unknown tool {name!r}.")
    try:
        return fn(arguments or {})
    except Exception as err:  # last-ditch safety net
        return _err(f"{name} raised {type(err).__name__}: {err}")

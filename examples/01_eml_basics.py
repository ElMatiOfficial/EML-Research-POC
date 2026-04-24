"""Basics: the seven EML tools in a single pass.

Shows math_to_eml, eml_to_math, evaluate_eml, verify_eml, list_eml_identities,
search_eml_identity, and sympy_compute -- driven through the same `run_tool`
dispatch the Claude subagents use via the `eml-tool` CLI.

Run with:
    python examples/01_eml_basics.py
"""

from __future__ import annotations

import json

from eml_research.tools import run_tool


def show(title: str, name: str, args: dict) -> None:
    print(f"\n== {title} ==")
    print(f"  call: eml-tool {name} {json.dumps(args)}")
    raw = run_tool(name, args)
    payload = json.loads(raw)
    # Pretty-print the most relevant fields
    for key in ("text", "rpn", "kolmogorov_length", "size", "math", "value", "result", "numeric", "match", "matches", "identities"):
        if key in payload:
            value = payload[key]
            if isinstance(value, list) and len(value) > 4:
                value = f"{value[:4]} ... ({len(value)} total)"
            print(f"  {key}: {value}")


def main() -> None:
    # 1) Translate forward: standard math -> EML tree
    show("math_to_eml -- exp(x)", "math_to_eml", {"expression": "exp(x)"})
    show("math_to_eml -- ln(x)", "math_to_eml", {"expression": "log(x)"})
    show("math_to_eml -- exp(x) - 1", "math_to_eml", {"expression": "exp(x) - 1"})

    # 2) Translate inverse: EML tree -> sympy expression
    show("eml_to_math -- eml(x, 1)", "eml_to_math", {"eml_expression": "eml(x, 1)"})

    # 3) Numeric evaluation over a binding
    show(
        "evaluate_eml -- exp(2)",
        "evaluate_eml",
        {"eml_expression": "eml(x, 1)", "bindings": {"x": 2.0}},
    )

    # 4) Inspect the registry
    show("list_eml_identities", "list_eml_identities", {})

    # 5) Exhaustive search -- rediscover exp(x) as eml(x, 1) from first principles
    show(
        "search_eml_identity -- rediscover exp(x)",
        "search_eml_identity",
        {"target": "exp(x)", "variables": ["x"], "max_size": 5, "max_results": 1},
    )

    # 6) Verify an EML tree numerically equals a math expression
    show(
        "verify_eml -- eml(x, 1) == exp(x)",
        "verify_eml",
        {"eml_expression": "eml(x, 1)", "math_expression": "exp(x)"},
    )

    # 7) Escape hatch: symbolic math for operations whose EML length is impractical
    show(
        "sympy_compute -- integrate exp(x) from 0 to 1",
        "sympy_compute",
        {"op": "integrate", "expression": "exp(x)", "variable": "x", "bounds": [0, 1]},
    )


if __name__ == "__main__":
    main()

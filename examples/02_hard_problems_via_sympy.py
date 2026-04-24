"""Solve the five graduate-level hard problems from the benchmark via sympy_compute.

Each of these problems was solved by a Claude Code subagent in one tool call
during the hard-track run (see RESULTS.md Run 2). This script executes the same
tool invocations directly so you can verify the closed forms without an agent.

Run with:
    python examples/02_hard_problems_via_sympy.py
"""

from __future__ import annotations

import json

from eml_research.tools import run_tool


HARD_PROBLEMS = [
    {
        "pid": "hard-01",
        "label": "Gaussian integral -- integral_{-oo}^{oo} exp(-x**2) dx",
        "call": {
            "op": "integrate",
            "expression": "exp(-x**2)",
            "variable": "x",
            "bounds": ["-oo", "oo"],
        },
        "expected": "sqrt(pi)",
    },
    {
        "pid": "hard-02",
        "label": "Dirichlet integral -- integral_0^{oo} sin(x)/x dx",
        "call": {
            "op": "integrate",
            "expression": "sin(x)/x",
            "variable": "x",
            "bounds": [0, "oo"],
        },
        "expected": "pi/2",
    },
    {
        "pid": "hard-03",
        "label": "Rational improper -- integral_0^{oo} 1/(x**4 + 1) dx",
        "call": {
            "op": "integrate",
            "expression": "1/(x**4 + 1)",
            "variable": "x",
            "bounds": [0, "oo"],
        },
        "expected": "sqrt(2)*pi/4",
    },
    {
        "pid": "hard-04",
        "label": "Stirling's limit -- lim n!/(n**n * exp(-n) * sqrt(n))",
        "call": {
            "op": "limit",
            "expression": "factorial(n)/(n**n * exp(-n) * sqrt(n))",
            "variable": "n",
            "point": "oo",
        },
        "expected": "sqrt(2)*sqrt(pi)",  # sympy's form; == sqrt(2*pi)
    },
    {
        "pid": "hard-05",
        "label": "Nested limit -- lim_{x->0} ((1+x)**(1/x) - E)/x",
        "call": {
            "op": "limit",
            "expression": "((1 + x)**(1/x) - E)/x",
            "variable": "x",
            "point": 0,
        },
        "expected": "-E/2",
    },
]


def main() -> None:
    print(f"{'PID':10s} {'LABEL':60s} {'RESULT':25s} {'EXPECTED'}")
    print("-" * 120)
    for p in HARD_PROBLEMS:
        raw = run_tool("sympy_compute", p["call"])
        payload = json.loads(raw)
        result = payload.get("result", "?")
        match = " OK " if result in (p["expected"], f"-1 + E" if p["expected"] == "E - 1" else p["expected"]) else " !! "
        print(f"{p['pid']:10s} {p['label']:60s} {result:25s} {p['expected']} {match}")


if __name__ == "__main__":
    main()

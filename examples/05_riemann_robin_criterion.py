"""Riemann T3: Robin's criterion sigma(n) < e^gamma * n * log(log(n)) for 5040 < n.

Robin (1984) showed that the Riemann Hypothesis is equivalent to
    sigma(n) / (n * log(log(n))) < e^gamma    for all n > 5040,
where sigma is the sum-of-divisors function and gamma = 0.5772156649...

This script checks the bound for every integer n in (5040, 10000]. The
argmax on this range is expected to be 7560 (a highly composite number);
the bound is satisfied with a healthy margin.

Run with:
    python examples/05_riemann_robin_criterion.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import sympy


def main(n_start: int = 5041, n_end: int = 10000) -> None:
    e_gamma = math.exp(0.5772156649015329)  # e^gamma ~= 1.78107241799

    max_ratio = 0.0
    argmax_n = n_start
    for n in range(n_start, n_end + 1):
        sigma = int(sympy.divisor_sigma(n, 1))
        ratio = sigma / (n * math.log(math.log(n)))
        if ratio > max_ratio:
            max_ratio = ratio
            argmax_n = n

    margin = e_gamma - max_ratio
    print(f"range:      [{n_start}, {n_end}]")
    print(f"argmax_n:   {argmax_n}  (sigma({argmax_n}) / ({argmax_n}*log log {argmax_n}))")
    print(f"max_ratio:  {max_ratio:.10f}")
    print(f"e^gamma:    {e_gamma:.10f}")
    print(f"margin:     {margin:.10f}")
    print(f"Robin bound holds on this range: {max_ratio < e_gamma}")

    out = Path("benchmark_results/riemann/T3_reference.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "source": "examples/05_riemann_robin_criterion.py",
                "n_range": [n_start, n_end],
                "max_ratio": max_ratio,
                "argmax_n": argmax_n,
                "e_gamma": e_gamma,
                "margin": margin,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()

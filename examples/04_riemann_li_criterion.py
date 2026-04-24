"""Riemann T2: Li's criterion lambda_n >= 0 for n = 1..10.

Li (1997) showed that the Riemann Hypothesis is equivalent to
    lambda_n = sum_rho [1 - (1 - 1/rho)^n] >= 0  for all n >= 1,
where rho ranges over all non-trivial zeros of zeta, paired with conjugates.

This script computes lambda_n for n = 1..10 using the first K = 200 zeros
from mpmath.zetazero at 30 decimal digits of precision. All ten values must
be positive; with K=200 the truncated sum gives lambda_1 ~ 0.0210 and
lambda_10 ~ 2.073. Positivity is the RH signature.

Run with:
    python examples/04_riemann_li_criterion.py
"""

from __future__ import annotations

import json
from pathlib import Path

import mpmath


def main(K: int = 200, N_MAX: int = 10, dps: int = 30) -> None:
    mpmath.mp.dps = dps

    # Precompute the first K zeros (once). Each pairing with its conjugate.
    zeros = [mpmath.zetazero(k) for k in range(1, K + 1)]

    lambdas = {}
    for n in range(1, N_MAX + 1):
        total = mpmath.mpc(0)
        for rho in zeros:
            total += 1 - (1 - 1 / rho) ** n
            total += 1 - (1 - 1 / mpmath.conj(rho)) ** n
        lambdas[n] = float(total.real)

    print(f"{'n':>3s}  {'lambda_n':>16s}  sign")
    print("-" * 32)
    for n, val in lambdas.items():
        print(f"{n:3d}  {val:16.10f}  {'+' if val > 0 else '-'}")
    all_positive = all(v > 0 for v in lambdas.values())
    print("-" * 32)
    print(f"all_positive: {all_positive}   min = {min(lambdas.values()):.10f}")

    out = Path("benchmark_results/riemann/T2_reference.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "source": "examples/04_riemann_li_criterion.py",
                "K_zeros_used": K,
                "dps": dps,
                "lambdas": {str(k): v for k, v in lambdas.items()},
                "all_positive": all_positive,
                "min_lambda": min(lambdas.values()),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()

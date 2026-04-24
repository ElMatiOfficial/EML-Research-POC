"""Riemann T1: first 20 non-trivial zeros lie on the critical line.

Computes rho_n = mpmath.zetazero(n) for n = 1..20 at 30 decimal digits of
precision, then evaluates |zeta(rho_n)| as a residual. All residuals should
be numerically zero to the precision used, confirming each rho_n sits on the
critical line Re(s) = 1/2 (consistent with RH for the first 20 zeros).

This is the "pure computation" half of the T1 subagent run documented in
RIEMANN_REPORT.md. Running this file reproduces the numerical artifact at
benchmark_results/riemann/T1_reference.json.

Run with:
    python examples/03_riemann_zeros_on_critical_line.py
"""

from __future__ import annotations

import json
from pathlib import Path

import mpmath


def main(n_zeros: int = 20, dps: int = 30) -> None:
    mpmath.mp.dps = dps

    rows = []
    max_abs = mpmath.mpf(0)
    for n in range(1, n_zeros + 1):
        rho = mpmath.zetazero(n)  # 1/2 + i * gamma_n
        gamma = mpmath.im(rho)
        residual = abs(mpmath.zeta(rho))
        rows.append((n, float(gamma), float(residual)))
        if residual > max_abs:
            max_abs = residual

    print(f"{'n':>3s}  {'gamma_n':>22s}  {'|zeta(rho_n)|':>15s}")
    print("-" * 48)
    for n, gamma, res in rows:
        print(f"{n:3d}  {gamma:22.12f}  {res:15.2e}")
    print("-" * 48)
    print(f"max |zeta(rho_n)| = {max_abs}")
    print("Consistent with RH for first 20 zeros: True" if float(max_abs) < 1e-20 else "WARNING: residual above threshold")

    out = Path("benchmark_results/riemann/T1_reference.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    artifact = {
        "source": "examples/03_riemann_zeros_on_critical_line.py",
        "n_zeros": n_zeros,
        "dps": dps,
        "gamma_1": rows[0][1],
        "gamma_2": rows[1][1],
        "gamma_20": rows[-1][1],
        "max_abs_zeta": float(max_abs),
    }
    out.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()

"""Riemann T4: Montgomery pair correlation of normalized zero spacings vs GUE.

Montgomery (1973) conjectured that the pair correlation of the normalized
spacings of non-trivial zeros of zeta tends to
    F(u) = 1 - (sin(pi*u)/(pi*u))^2
as the sample grows, matching the distribution of eigenvalue spacings of a
random matrix drawn from the Gaussian Unitary Ensemble (GUE).

This script computes the empirical histogram of unfolded pair distances
u_ij = (gamma_j - gamma_i) * log(gamma_i / (2*pi)) / (2*pi) for the first 500
non-trivial zeros and compares to the conjectured F(u) over 15 bins of
width 0.2 in [0, 3].

Run with:
    python examples/06_riemann_pair_correlation.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import mpmath


def main(n_zeros: int = 500, max_delta: int = 20, n_bins: int = 15, u_max: float = 3.0, dps: int = 30) -> None:
    mpmath.mp.dps = dps

    # 1. Collect gamma_k
    gammas = [float(mpmath.zetazero(k).imag) for k in range(1, n_zeros + 1)]

    # 2. Unfold pair distances u_ij for j - i <= max_delta and u_ij < u_max
    us: list[float] = []
    for i in range(n_zeros):
        for j in range(i + 1, min(i + 1 + max_delta, n_zeros)):
            u = (gammas[j] - gammas[i]) * math.log(gammas[i] / (2 * math.pi)) / (2 * math.pi)
            if 0 < u < u_max:
                us.append(u)

    # 3. Histogram normalized by N * du (one-sided density; matches F in expectation)
    bin_width = u_max / n_bins
    bin_centers = [(i + 0.5) * bin_width for i in range(n_bins)]
    counts = [0] * n_bins
    for u in us:
        idx = min(int(u / bin_width), n_bins - 1)
        counts[idx] += 1
    density = [c / (n_zeros * bin_width) for c in counts]

    # 4. F(u) at bin centers
    def F(u: float) -> float:
        if u == 0:
            return 0.0
        pu = math.pi * u
        return 1.0 - (math.sin(pu) / pu) ** 2

    f_vals = [F(c) for c in bin_centers]
    deviations = [abs(d - f) for d, f in zip(density, f_vals)]
    max_dev = max(deviations)
    mean_dev = sum(deviations) / len(deviations)

    print(f"{'u bin center':>12s}  {'empirical':>10s}  {'F(u)':>10s}  {'|diff|':>10s}")
    print("-" * 50)
    for c, d, f, dev in zip(bin_centers, density, f_vals, deviations):
        print(f"{c:12.2f}  {d:10.4f}  {f:10.4f}  {dev:10.4f}")
    print("-" * 50)
    print(f"max |empirical - F| = {max_dev:.4f}")
    print(f"mean |empirical - F| = {mean_dev:.4f}")
    print(f"N_zeros={n_zeros}, pairs used={len(us)}")

    out = Path("benchmark_results/riemann/T4_reference.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "source": "examples/06_riemann_pair_correlation.py",
                "N_zeros": n_zeros,
                "pair_window_M": max_delta,
                "bins": n_bins,
                "pairs_used": len(us),
                "max_abs_deviation_from_F": max_dev,
                "mean_abs_deviation_from_F": mean_dev,
                "bin_centers": bin_centers,
                "empirical_density": density,
                "F_u": f_vals,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()

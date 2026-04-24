"""Sub-tasks for the multi-agent Riemann investigation.

Each task encodes a well-known RH-equivalent numerical criterion that a
specialist agent can check within a single session. Ground-truth values come
from the published literature (Li, Robin, Keating-Snaith, Montgomery) and are
cross-validated against mpmath.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RiemannTask:
    tid: str
    title: str
    bombieri_ref: str          # which section of the Bombieri PDF motivates this task
    objective: str             # what to compute
    method_hint: str           # concrete numerical recipe
    success_criterion: str     # what "pass" means
    expected_signals: dict[str, Any]  # spot-check values
    eml_angle: str             # how EML framing might contribute (empirical, may be "nothing")
    tags: list[str] = field(default_factory=list)


TASKS: list[RiemannTask] = [
    RiemannTask(
        tid="T1",
        title="First 20 non-trivial zeros lie on the critical line",
        bombieri_ref="III. Evidence for the Riemann hypothesis -- numerical verification",
        objective=(
            "Compute the imaginary parts gamma_n of the first 20 non-trivial zeros of zeta(s), "
            "evaluate |zeta(1/2 + i*gamma_n)| at each, and report the max."
        ),
        method_hint=(
            "Use mpmath.zetazero(n) for n=1..20 (returns 0.5 + i*gamma_n to full precision). "
            "For each zero rho, evaluate mpmath.zeta(rho) and record |zeta(rho)|."
        ),
        success_criterion=(
            "All 20 zeros have Re(rho) == 0.5 exactly (mpmath returns the critical line value), "
            "and |zeta(rho)| < 1e-20 for every n."
        ),
        expected_signals={
            "gamma_1": 14.134725141734693,
            "gamma_2": 21.022039638771555,
            "gamma_3": 25.010857580145688,
            "max_abs_zeta": "< 1e-20",
        },
        eml_angle=(
            "log|zeta(s)| = -sum_p log(1 - p^-s). In EML, each summand is a subtract-of-logs. "
            "The EML-track agent should note whether expressing log|zeta| through EML gives any "
            "structural handle on why zeros cluster on Re=1/2. (Honest answer: probably no.)"
        ),
        tags=["numerical-verification", "critical-line"],
    ),
    RiemannTask(
        tid="T2",
        title="Li's criterion: lambda_n >= 0 for n=1..10",
        bombieri_ref="III. Evidence for the Riemann hypothesis (analytical criteria)",
        objective=(
            "Compute Li's numbers lambda_n for n=1..10 using the first K=200 non-trivial zeros. "
            "Li (1997): RH is equivalent to lambda_n >= 0 for every n >= 1, where "
            "lambda_n = sum_rho [1 - (1 - 1/rho)^n] with rho ranging over all non-trivial zeros "
            "(paired with their conjugates). Confirm positivity."
        ),
        method_hint=(
            "rho_k = mpmath.zetazero(k) for k=1..K; include both rho_k and its conjugate. "
            "Then lambda_n = sum_k [ (1 - (1 - 1/rho_k)^n) + (1 - (1 - 1/conj(rho_k))^n) ]. "
            "Use mpmath with at least 30 decimal digits of precision."
        ),
        success_criterion=(
            "lambda_n > 0 for every n in 1..10, with values agreeing to ~4 decimals with "
            "the published table."
        ),
        expected_signals={
            # Values computed in-repo with mpmath.mp.dps=30, K=200 zeros. These are
            # truncated sums -- they converge slowly to the "true" lambda_n as K->oo.
            # All should be STRICTLY POSITIVE regardless of K (that's the RH signature).
            "lambda_1_at_K200": 0.0210348603,
            "lambda_2_at_K200": 0.0841023444,
            "lambda_3_at_K200": 0.1890913054,
            "lambda_10_at_K200": 2.0732576202,
            "sign_required": "all > 0",
        },
        eml_angle=(
            "The expansion of (1 - 1/rho)^n uses pure exp/log via (1 - 1/rho)^n = exp(n * log(1 - 1/rho)). "
            "log(1 - 1/rho) and subtraction from 1 are both EML-native. The EML-track agent should "
            "express the summand in EML and note whether the form is more revealing."
        ),
        tags=["li-criterion", "zero-sum"],
    ),
    RiemannTask(
        tid="T3",
        title="Robin's criterion: sigma(n) < e^gamma * n * log(log(n)) for 5040 < n <= 10000",
        bombieri_ref="III. Evidence for the Riemann hypothesis (elementary criteria)",
        objective=(
            "Robin (1984): RH is equivalent to sigma(n)/(n * log(log(n))) < e^gamma for all n > 5040, "
            "where sigma(n) is the sum of divisors and gamma = 0.5772156649... "
            "For every integer n in [5041, 10000], compute the ratio and report the maximum."
        ),
        method_hint=(
            "sigma(n): use sympy.divisor_sigma(n, 1) or a direct loop. "
            "gamma = mpmath.euler or math.euler. Target: max ratio < e^gamma = 1.7810724179..."
        ),
        success_criterion=(
            "max_{5040 < n <= 10000} sigma(n) / (n * log(log(n))) is strictly less than e^gamma."
        ),
        expected_signals={
            "e_gamma": 1.7810724179901979,
            "max_ratio_expected": "< 1.78",
            "argmax_expected_near": 5040,
        },
        eml_angle=(
            "The criterion *is* a bound of the form e^X > Y where Y is arithmetic; taking logs gives "
            "a subtraction of logs. EML-track agent should express e^gamma - sigma(n)/(n * log log n) > 0 "
            "in EML form and note whether sign-structure is clearer."
        ),
        tags=["robin-criterion", "divisor-function"],
    ),
    RiemannTask(
        tid="T4",
        title="Montgomery pair correlation matches the GUE form",
        bombieri_ref="V. Further evidence: explicit formula (Montgomery-Odlyzko-Dyson)",
        objective=(
            "Compute the pair-correlation histogram of normalized spacings of the first N=500 "
            "non-trivial zeros and compare to Montgomery's conjectured form "
            "F(u) = 1 - (sin(pi*u)/(pi*u))^2 for u > 0. "
            "Normalized spacing: delta_k = (gamma_{k+1} - gamma_k) * log(gamma_k / (2*pi)) / (2*pi). "
            "Histogram the pairwise gaps over a coarse grid in u in [0, 3]."
        ),
        method_hint=(
            "Collect gamma_k for k=1..500 via mpmath.zetazero. Compute normalized spacings. "
            "Bin pairwise differences |delta_i - delta_j|/(|i-j|) or equivalently the CDF of "
            "'u' values between consecutive zeros. Compare bin counts/expected counts from F(u). "
            "Report the max absolute deviation from the Montgomery curve over the grid."
        ),
        success_criterion=(
            "The empirical histogram tracks F(u) qualitatively (mean absolute deviation in counts "
            "across bins < 20% for 500 zeros -- noisy but consistent)."
        ),
        expected_signals={
            "repulsion_at_small_u": "F(u) -> 0 as u -> 0",
            "F_infty": 1.0,
            "first_peak_near_u": 1.0,
        },
        eml_angle=(
            "The GUE form sin^2(pi*u)/(pi*u)^2 has no EML-natural route (sin has K>100). "
            "This task is deliberately included to see whether the EML-track agent correctly "
            "abandons EML and falls back to numerics -- i.e., it is a negative-control task."
        ),
        tags=["pair-correlation", "gue", "negative-control"],
    ),
]


def by_tid(tid: str) -> RiemannTask | None:
    return next((t for t in TASKS if t.tid == tid), None)

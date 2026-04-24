# Riemann Hypothesis — multi-agent investigation report

**Run date:** 2026-04-23
**Agents:** 8 × Claude Code `general-purpose` subagents, spawned in parallel (4 EML-track + 4 Classical-track), one per (task, track) pair.
**Source problem:** Bombieri's Clay Millennium Institute paper on the Riemann Hypothesis (in-repo at `riemann.pdf`).
**Result:** 8/8 artifacts pass grading. **0 evidence gathered against RH.** (Obviously — every tested criterion is either already proven or known to hold numerically for billions of zeros; this confirms the infrastructure works, not that RH is true.)

## What this report is and isn't

- **Is:** 4 narrow, verifiable sub-investigations of RH-equivalent criteria, run in parallel with a controlled EML-vs-Classical A/B split, each producing a reproducible numerical artifact on disk.
- **Isn't:** a proof attempt, a survey of the RH literature, or a head-to-head "which approach is closer to a proof" comparison. The hard analytic content of RH is not being approached here.

## What the EML-vs-Classical split revealed

Across all four tasks, the EML-track agents uniformly reported that **EML did not provide a computational shortcut or structural insight over mpmath** for the RH sub-problems tested. Specific findings from the EML agents (paraphrased from their artifacts):

- **T1:** `log(1 − p⁻ˢ)` requires a multiplication `−s · log(p)` to land inside the EML registry; since multiplication has K=41, the Euler product has no practical pure-EML form. `math_to_eml` refused `log(1 − p**(−s))` outright. mpmath did the actual work.
- **T2:** individual fragments of Li's summand (`exp(x)`, `log(x)`, `1 − y`) are EML-native (K = 3, 7, 11), but the composition `exp(n · log(1 − y))` fails: `math_to_eml` errors on the inner multiplication. The summand as a whole is outside the registry without a registered `pow(x, n)` identity.
- **T3:** `eml-tool evaluate_eml '{"eml_expression": "eml(x, 1)", "bindings": {"x": 0.5772156649}}'` correctly reproduces e^γ ≈ 1.78107…, but this is identical to what `math.exp(0.5772…)` gives. The EML form is structural, not computational.
- **T4:** `search_eml_identity` on `sin(x)` with `max_size=7` returned no matches — a **signature negative result**, since F(u) = 1 − sin²(πu)/(πu)² is central to Montgomery's conjecture and sin is known to have K > 100 in EML. EML demonstrably cannot reach the pair-correlation form in practical brute-force range.

The honest take is that **EML is well-suited for the paper's core identities** (exp, ln, e, small subtractions — K ≤ 11) but the analytic-number-theory regime uses *products* and *trig* pervasively, both of which have EML lengths that are infeasible today. The registry needs registered identities for multiplication, sin/cos, and general integer powers before EML becomes a real substrate for RH-style calculations. The Classical track matched the EML track on every task because the EML track itself ultimately used mpmath for the load-bearing work.

## Scoreboard

This report is the head-to-head output of 4 tasks × 2 tracks (EML vs Classical) run as parallel Claude Code subagents. Each task checks an RH-equivalent (or RH-consistent) numerical criterion motivated by Bombieri's Clay Institute paper.

| TID | Task | EML verdict | Classical verdict | EML passes grader | Classical passes grader |
| --- | --- | --- | --- | --- | --- |
| T1 | First 20 non-trivial zeros lie on the critical line | consistent_with_RH | PASS — gamma_1 matches (14.134725); max|zeta(rho_n)| = 1.28e-29 < 1e-15 | consistent_with_RH | PASS — gamma_1 matches (14.134725); max|zeta(rho_n)| = 1.28e-29 < 1e-15 |
| T2 | Li's criterion: lambda_n >= 0 for n=1..10 | consistent_with_RH | PASS — all 10 positive; lambda_1=0.02103, lambda_10=2.0733 | consistent_with_RH | PASS — all 10 positive; lambda_1=0.02103, lambda_10=2.0733 |
| T3 | Robin's criterion: sigma(n) < e^gamma * n * log(log(n)) for  | consistent_with_RH | PASS — max sigma(n)/(n*log log n) = 1.739917 < e^gamma = 1.781072 | consistent_with_RH | PASS — max sigma(n)/(n*log log n) = 1.739917 < e^gamma = 1.781072 |
| T4 | Montgomery pair correlation matches the GUE form | consistent_with_RH | PASS — max |empirical - F(u)| = 0.155 (tolerance <= 0.30) | consistent_with_RH | PASS — max |empirical - F(u)| = 0.155 (tolerance <= 0.30) |

## Tallies

- **EML track:** 4/4 tasks pass the grader
- **Classical track:** 4/4 tasks pass the grader

## Per-task details

### T1: First 20 non-trivial zeros lie on the critical line

**Bombieri ref:** III. Evidence for the Riemann hypothesis -- numerical verification

**Objective:** Compute the imaginary parts gamma_n of the first 20 non-trivial zeros of zeta(s), evaluate |zeta(1/2 + i*gamma_n)| at each, and report the max.

**EML track** — verdict: `consistent_with_RH`; grader: PASS (gamma_1 matches (14.134725); max|zeta(rho_n)| = 1.28e-29 < 1e-15)

  Approach: Computed the first 20 non-trivial zeros of the Riemann zeta function via mpmath.zetazero(n) at 30-digit precision, obtaining rho_n = 1/2 + i*gamma_n. For each rho_n, evaluated |zeta(rho_n)| using mpmath.zeta and took the maximum over n = 1..20. A value within numerical noise of zero confirms that each computed zero satisfies Re(s) = 1/2 (consistent with the Riemann Hypothesis for the first 20 zeros; this is a numerical check, not a proof).

  Key results: gamma_1 = 14.134725141734695 \| gamma_2 = 21.022039638771556 \| gamma_20 = 77.1448400688748 \| max_abs_zeta = 1.2760743662970368e-29 \| zeros_checked = 20

  EML observations: log|zeta(s)| = -Re sum_p log(1 - p^{-s}) is not directly expressible in the current EML registry. math_to_eml fails on log(1 - p**(-s)) because general power p**(-s) has no registered identity (only E**x is built in), and it fails on log(zeta(s)) because zeta is not registered. However, the per-term primitive log(1 - y) IS EML-expressible (K=17), and exp(x) - log(y) is literally eml(x, y) by definition. Structural observation: each Euler-product term log(1 - p^{-s}) = log(1 - exp(-s * log(p))) needs only one multiplication (-s * log(p)) to fall inside EML; multiplication itself has K >= 41 in EML, so the Euler product expressed purely in EML is dominated by the multiplication of complex s by real log(p). EML therefore offers no computational shortcut for verifying zeros numerically, and the numerical check was done with mpmath. Reporting honestly: EML is not the right tool for this task.

**Classical track** — verdict: `consistent_with_RH`; grader: PASS (gamma_1 matches (14.134725); max|zeta(rho_n)| = 1.28e-29 < 1e-15)

  Approach: Set mpmath.mp.dps = 30. For n = 1..20, computed the nth non-trivial zero via mpmath.zetazero(n), which returns rho_n = 0.5 + i*gamma_n on the critical line by construction of the algorithm. For each rho_n evaluated |zeta(rho_n)| using mpmath.zeta and took the maximum across n as the residual. A residual on the order of machine/mpmath precision (<< 1e-20) confirms these zeros are numerically consistent with lying exactly on Re(s) = 1/2, i.e. consistent with RH for n<=20.

  Key results: gamma_1 = 14.134725141734695 \| gamma_2 = 21.022039638771556 \| gamma_20 = 77.1448400688748 \| max_abs_zeta = 1.2760743662970368e-29 \| zeros_checked = 20


### T2: Li's criterion: lambda_n >= 0 for n=1..10

**Bombieri ref:** III. Evidence for the Riemann hypothesis (analytical criteria)

**Objective:** Compute Li's numbers lambda_n for n=1..10 using the first K=200 non-trivial zeros. Li (1997): RH is equivalent to lambda_n >= 0 for every n >= 1, where lambda_n = sum_rho [1 - (1 - 1/rho)^n] with rho ranging over all non-trivial zeros (paired with their conjugates). Confirm positivity.

**EML track** — verdict: `consistent_with_RH`; grader: PASS (all 10 positive; lambda_1=0.02103, lambda_10=2.0733)

  Approach: Computed Li's coefficients lambda_n = sum_rho [1 - (1 - 1/rho)^n] for n=1..10 using the first K=200 non-trivial zeros of the Riemann zeta function obtained via mpmath.zetazero at mp.dps=30. For each zero rho we added the contribution from both rho and its complex conjugate (so the implicit 2*Re is exact under the pairing), then took the real part. The EML angle was explored by feeding sub-fragments of the summand through eml-tool math_to_eml: exp(x), log(x), and 1-y each produce valid EML trees, but the composition exp(n*log(1-1/rho)) fails at the multiplication node (Mul is unregistered, K=41 per the tool's documentation), so EML normal form cannot express the full summand today.

  Key results: K_zeros_used = 200 \| lambdas = {1=0.02103486031742673, 2=0.08410234441738831, 3=0.18909130542077532, 4=0.3358169767953985, 5=0.5240216874492751, 6=0.7533758582603037, 7=1.0234792754681374, 8=1.3338626350851954, 9=1.6839893512431605, 10=2.0732576201849873} \| all_positive = True \| min_lambda = 0.02103486031742673

  EML observations: Feeding fragments of the Li summand into eml-tool math_to_eml: (1) exp(x) yields eml(x, 1) [K=3]; (2) log(x) yields eml(1, eml(eml(1, x), 1)) [K=7]; (3) 1 - y yields a K=11 tree via one_minus/sub; (4) exp(log(1-y)) composes cleanly (K=11, equivalent to 1-y) since there is no intervening scalar multiplication. However exp(n * log(1 - 1/rho)) — which is the natural EML-structured rewrite of (1-1/rho)^n — FAILS: math_to_eml returns an error 'No EML identity registered for Mul', because integer scalar multiplication has EML-length ~41 and is not in the registered identity set. So EML does not presently surface any shortcut for Li's summand: the exp/log pieces are trivially in EML form, but the power (n-fold multiplication inside exp) is the barrier. A useful future registration would be a pow(x, n) identity or nat-mult identity — that would put the entire summand in EML normal form. Numerically, the bottleneck (zetazero) is what dominates cost, so EML normal form offers no computational speedup here; its value would be symbolic/structural.

**Classical track** — verdict: `consistent_with_RH`; grader: PASS (all 10 positive; lambda_1=0.02103, lambda_10=2.0733)

  Approach: Computed Li's coefficients lambda_n = sum_rho [1 - (1 - 1/rho)^n] for n=1..10 using the first K=200 non-trivial zeros of the Riemann zeta function obtained via mpmath.zetazero(k) at 30 decimal digits of precision. Each zero rho was paired with its complex conjugate conj(rho) in the sum to account for the symmetric zero pairs in the critical strip. For each n, both terms (1 - (1 - 1/rho)^n) and (1 - (1 - 1/conj(rho))^n) were accumulated as mpc complex numbers, and the real part of the final sum was returned. Li (1997) proved RH is equivalent to lambda_n >= 0 for all n >= 1; positivity of the partial-sum lambda_n over a finite set of zeros is a necessary but not sufficient numerical consistency check with RH.

  Key results: K_zeros_used = 200 \| lambdas = {1=0.02103486031742673, 2=0.08410234441738831, 3=0.18909130542077532, 4=0.3358169767953985, 5=0.5240216874492751, 6=0.7533758582603037, 7=1.0234792754681374, 8=1.3338626350851954, 9=1.6839893512431605, 10=2.0732576201849873} \| all_positive = True \| min_lambda = 0.02103486031742673


### T3: Robin's criterion: sigma(n) < e^gamma * n * log(log(n)) for 5040 < n <= 10000

**Bombieri ref:** III. Evidence for the Riemann hypothesis (elementary criteria)

**Objective:** Robin (1984): RH is equivalent to sigma(n)/(n * log(log(n))) < e^gamma for all n > 5040, where sigma(n) is the sum of divisors and gamma = 0.5772156649... For every integer n in [5041, 10000], compute the ratio and report the maximum.

**EML track** — verdict: `consistent_with_RH`; grader: PASS (max sigma(n)/(n*log log n) = 1.739917 < e^gamma = 1.781072)

  Approach: Iterated n from 5041 to 10000, computed sigma(n) via sympy.divisor_sigma(n,1), and evaluated the Robin ratio r_n = sigma(n) / (n * log(log(n))). Tracked the maximum ratio and its argmax, then compared to e^gamma. To obtain the threshold e^gamma via the EML framework, used eml-tool math_to_eml on exp(x) which yields the minimal K=3 tree eml(x, 1), then evaluate_eml on eml(x, 1) with x = gamma (0.5772156649015329) to recover 1.7810724179901979 — matching the standard value. Verdict reflects whether max(r_n) < e^gamma on this range.

  Key results: n_range = [5041, 10000] \| max_ratio = 1.7399165192027595 \| argmax_n = 7560 \| e_gamma = 1.781072417990198 \| margin = 0.04115589878743853

  EML observations: math_to_eml(exp(x)) returns the minimal K=3 tree eml(x, 1) (RPN: "x 1 eml"), confirming exp is the primitive EML identity with ln(1)=0 absorbed into the second slot. Evaluating eml(x, 1) at x = Euler-Mascheroni gamma = 0.5772156649015329 gives 1.781072417990198, reproducing e^gamma to 15 digits. Honest assessment: EML adds no computational advantage here — gamma itself is transcendental with no finite EML tree, so the number must still be supplied externally; the eml(x,1) wrapper is structurally identical to a direct exp() call. EML is useful as a normal-form lens: the Robin inequality r_n < e^gamma is equivalent to ln(r_n) < gamma, i.e. eml(0, r_n) < gamma (since eml(0, y) = 1 - ln(y)), but this rewrite does not simplify the arithmetic check.

**Classical track** — verdict: `consistent_with_RH`; grader: PASS (max sigma(n)/(n*log log n) = 1.739917 < e^gamma = 1.781072)

  Approach: Iterated n from 5041 to 10000 inclusive. For each n, computed sigma(n) = sum of divisors of n using sympy.divisor_sigma(n, 1), then the Robin ratio r_n = sigma(n) / (n * log(log(n))) using Python's math.log for natural logarithms. Tracked the maximum ratio and its argmax across the range, then compared against e^gamma = 1.7810724179901979. Robin (1984) proved that RH is equivalent to r_n < e^gamma for all n > 5040; any violation in this range would refute RH, while the absence of one provides a numerical consistency check (not a proof).

  Key results: n_range = [5041, 10000] \| max_ratio = 1.7399165192027595 \| argmax_n = 7560 \| e_gamma = 1.781072417990198 \| margin = 0.04115589878743853


### T4: Montgomery pair correlation matches the GUE form

**Bombieri ref:** V. Further evidence: explicit formula (Montgomery-Odlyzko-Dyson)

**Objective:** Compute the pair-correlation histogram of normalized spacings of the first N=500 non-trivial zeros and compare to Montgomery's conjectured form F(u) = 1 - (sin(pi*u)/(pi*u))^2 for u > 0. Normalized spacing: delta_k = (gamma_{k+1} - gamma_k) * log(gamma_k / (2*pi)) / (2*pi). Histogram the pairwise gaps over a coarse grid in u in [0, 3].

**EML track** — verdict: `consistent_with_RH`; grader: PASS (max |empirical - F(u)| = 0.155 (tolerance <= 0.30))

  Approach: Computed the first 500 non-trivial zeros gamma_k of zeta(s) via mpmath.zetazero at 30-digit precision. Formed the normalized pair distances u_ij = (gamma_j - gamma_i) * log(gamma_i/(2 pi))/(2 pi) for all i<j with j-i <= M=20 and u_ij<3. Density-normalized histogram on [0,3] with 15 bins of width 0.2 (ordered-pair count / (N * dx)) and compared bin-center values to Montgomery's F(u) = 1 - (sin(pi u)/(pi u))^2. EML-side: search_eml_identity('sin(x)', max_size=7) returned zero matches, confirming the conjectured F has no practical brute-force EML decomposition (K>100 for trig), so the numerical check was carried out with mpmath as instructed.

  Key results: N_zeros = 500 \| pair_window_M = 20 \| bins = 15 \| max_abs_deviation_from_F = 0.15533790946735215 \| mean_abs_deviation_from_F = 0.06900778433141194 \| F_u_zero_limit = 0.0 \| empirical_density_at_u_0_1 = 0.0

  EML observations: Ran eml-tool search_eml_identity with target='sin(x)', variables=['x'], max_size=7, max_results=3. Result: matches=[], note='No EML tree up to size 7 matches sin(x)'. This is a signature NEGATIVE EML result: Montgomery's pair-correlation form F(u) = 1 - (sin(pi u)/(pi u))^2 is outside the practical brute-force EML reach (trig has K>100 per Odrzywolek 2026). The EML substrate does not touch this identity at accessible tree sizes; the numerical verification proceeded via mpmath.

**Classical track** — verdict: `consistent_with_RH`; grader: PASS (max |empirical - F(u)| = 0.155 (tolerance <= 0.30))

  Approach: Computed the first 500 non-trivial Riemann zeros gamma_k via mpmath.zetazero at 30 decimal digits. Formed unfolded spacings u_ij = (gamma_j - gamma_i) * log(gamma_i/(2*pi))/(2*pi) for all pairs i<j with j-i <= M=20 and u_ij < 3. Built a density-normalized histogram on [0,3] with 15 bins of width 0.2, normalizing bin count by (N * dx) so the histogram approximates the Montgomery pair-correlation density (one-sided: unordered pairs j>i). Compared bin-center values to Montgomery's conjectured F(u) = 1 - (sin(pi u)/(pi u))^2 and recorded max/mean absolute deviations.

  Key results: N_zeros = 500 \| pair_window_M = 20 \| bins = 15 \| max_abs_deviation_from_F = 0.15533790946735215 \| mean_abs_deviation_from_F = 0.06900778433141194 \| F_u_zero_limit = 0.0 \| empirical_density_at_u_0_1 = 0.0


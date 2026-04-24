# Benchmark Results — Claude Code agent on EML Research POC

**Date:** 2026-04-23
**Agent:** Claude Code (16 `general-purpose` subagents in parallel, one per problem)
**Tool interface:** `eml-tool` CLI at [src/eml_research/cli.py](src/eml_research/cli.py), wrapping the seven EML tools from [src/eml_research/tools.py](src/eml_research/tools.py)
**Problem suite:** 16 problems across 4 categories, see [src/eml_research/problems.py](src/eml_research/problems.py)
**Grader:** [src/eml_research/grading.py](src/eml_research/grading.py) — five check strategies (`numeric`, `exact`, `set`, `eml_tree`, `string`)

## Summary

| Category | Pass | Total | Accuracy |
| --- | ---: | ---: | ---: |
| `eml` | 5 | 5 | 100.0% |
| `evaluation` | 3 | 3 | 100.0% |
| `calculus` | 5 | 5 | 100.0% |
| `algebra` | 3 | 3 | 100.0% |
| **Overall** | **16** | **16** | **100.0%** |

## Per-problem results

| PID | Category | Check | Agent answer | Ground truth | Verdict |
| --- | --- | --- | --- | --- | --- |
| eml-01 | eml | eml_tree | `eml(x, 1)` | `eml(x, 1)` (≡ exp(x)) | PASS — tree matches target on sample grid |
| eml-02 | eml | eml_tree | `eml(1, eml(eml(1, x), 1))` | `eml(1, eml(eml(1, x), 1))` (≡ log(x)) | PASS — tree matches target on sample grid |
| eml-03 | eml | exact | `7` | `7` | PASS — exact match (K-length of ln(x)) |
| eml-04 | eml | exact | `3` | `3` | PASS — exact match (K-length of e) |
| eml-05 | eml | exact | `13` | `13` | PASS — exact match (tree size of exp(x) − 1) |
| eval-01 | evaluation | numeric | `7.38905609893065` | `7.38905609893065` | PASS — `|diff|=0.000e+00` |
| eval-02 | evaluation | numeric | `2.302585092994046` | `2.302585092994046` | PASS — `|diff|=0.000e+00` |
| eval-03 | evaluation | numeric | `1.71828182845905` | `1.718281828459045` | PASS — `|diff|=4.885e-15` |
| calc-01 | calculus | exact | `1` | `1` | PASS — d/dx[exp(x)] at x=0 |
| calc-02 | calculus | exact | `1/2` | `1/2` | PASS — ∫₀¹ x dx |
| calc-03 | calculus | exact | `-1 + E` | `E - 1` | PASS — ∫₀¹ exp(x) dx (sympy.simplify of diff = 0) |
| calc-04 | calculus | exact | `1` | `1` | PASS — lim_{x→0} sin(x)/x |
| calc-05 | calculus | exact | `E` | `E` | PASS — lim_{x→∞} (1+1/x)^x |
| alg-01 | algebra | set | `[-1, 1]` | `[-1, 1]` | PASS — set match |
| alg-02 | algebra | set | `[1, 2]` | `[1, 2]` | PASS — set match |
| alg-03 | algebra | exact | `x` | `x` | PASS — simplify(exp(log(x))) |

## Token / tool-use profile

16 subagents, 276,116 total tokens (≈17K avg per subagent), 1–4 tool calls per problem. Typical agent trace was `eml-tool --list → math_to_eml → verify_eml → final answer`. The calculus/algebra problems used `sympy_compute` directly (as instructed — EML length for multiplication is K=41, sin/cos K>100, so pure-EML is impractical there; this is the expected and documented behavior).

Wall clock: ~13 minutes dominated by one long-running subagent (`calc-05`, ~5 min) that explored several `sympy_compute` paths before settling on `E`.

## Interesting finding: the benchmark caught a ground-truth bug

On problem `eml-05` (tree size of `exp(x) − 1`), the agent returned `13` but my declared truth was `11`. I investigated with `eml-tool math_to_eml '{"expression": "exp(x) - 1"}'`, which produced:

```
eml(eml(1, eml(eml(1, eml(x, 1)), 1)), eml(1, 1))   size=13
```

The derivation:

- `exp(x) − 1` ≡ `minus_one(exp(x))` ≡ `eml(ln(exp(x)), e)`
- `size(ln(z)) = 6 + size(z)`, so `size(ln(exp(x))) = 6 + 3 = 9`
- `size(e) = 3`, outer `eml = 1` → total `9 + 3 + 1 = 13`

I had originally written `truth=11`, which is the correct size for `x − 1` (`sub(x, 1) = eml(ln(x), e)`, `size = 1 + 7 + 3 = 11`) — not `exp(x) − 1`. The [self-consistency test `test_every_problem_passes_its_own_grader_when_given_truth`](tests/test_problems.py) didn't catch this because it only verified that the grader accepts its own declared truth, not that the declared truth is itself correct.

Fix at [src/eml_research/problems.py:91](src/eml_research/problems.py#L91) — `truth=13` with an inline comment documenting the `minus_one(exp(x))` derivation. All 34 unit tests pass after the fix.

This is exactly the kind of finding a benchmark like this is supposed to surface: a fresh agent armed with the library's own primitives computes the answer directly and flags disagreements with the declared truth.

## How to reproduce

1. Install the package and EML translator:
   ```bash
   pip install -e .
   ```
2. Verify tools (no API key needed):
   ```bash
   pytest
   ```
3. Use Claude Code to run the benchmark. From a Claude Code session in this repo, ask it to spawn one `general-purpose` subagent per problem with the prompt template used in this run (context + `eml-tool` usage + problem text + `FINAL ANSWER:` requirement). Save the answers to a JSON file mapping PID → answer string.
4. Grade:
   ```bash
   python scripts/grade_run.py benchmark_results/claude_code_answers.json
   ```

The raw answers used for this run are at [benchmark_results/claude_code_answers.json](benchmark_results/claude_code_answers.json) (gitignored by default; regenerate per-run).

Alternatively, the SDK-based runner in [src/eml_research/benchmark.py](src/eml_research/benchmark.py) can be used instead of Claude Code subagents — it takes the same 16 problems through the Anthropic Messages API with the same seven tools.

## Research takeaways

- **Small paper identities are correctly reproduced** (`exp(x) = eml(x, 1)`, `ln(x) = eml(1, eml(eml(1, x), 1))`, `e = eml(1, 1)`) — the agent gets both the tree shape and the K-length right on a first pass.
- **The EML tools work as a reasoning primitive** for problems the library's registry already covers. The agent consistently translates into EML first, then either evaluates or delegates calculus to `sympy_compute` as instructed.
- **Tool-use restraint is good.** 1–2 tool calls per problem on average — the agent didn't thrash or loop. Even `calc-05`, which explored multiple paths, converged to the correct closed form.
- **The escape hatch is doing load-bearing work.** Pure-EML would be impractical for calculus/algebra problems with K>11 (multiplication alone is K=41, sin/cos K>100). `sympy_compute` is the right tool there, and the agent correctly selects it.

A natural follow-up: rerun with `sympy_compute` removed to measure how far pure-EML reasoning gets on harder problems, and seed the library with new registered identities from the paper's supplementary (addition, multiplication, trig) so the agent can use them instead of falling back to sympy.

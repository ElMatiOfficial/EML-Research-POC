# EML Research POC

> **Benchmark runs (2026-04-23): 21/21 (100%)** — 16/16 on the easy–medium track plus 5/5 on a graduate-level hard track (Gaussian / Dirichlet / 1/(x⁴+1) integrals, Stirling's constant, ((1+x)^(1/x)−e)/x limit). All runs via Claude Code subagents through the `eml-tool` CLI. Full breakdown in [RESULTS.md](RESULTS.md).

Research proof-of-concept: can an AI agent solve mathematical problems more faithfully if it reasons through the **EML (Exp-Minus-Log) primitive** from Odrzywołek (2026, [arXiv:2603.21852](https://arxiv.org/abs/2603.21852))?

EML defines a single binary operator
```
eml(x, y) = exp(x) - ln(y)
```
and shows every elementary function can be expressed as a tree over the single literal `1` and nested `eml(...)` calls — the continuous-math analogue of NAND. This repo wires that primitive up as a Claude tool and measures whether the agent's answers match known ground truths.

Built on top of the upstream library [ElMatiOfficial/EML-Matemathical-Translator-for-AI](https://github.com/ElMatiOfficial/EML-Matemathical-Translator-for-AI).

## What this POC contains

| Module | Purpose |
| --- | --- |
| [`src/eml_research/tools.py`](src/eml_research/tools.py) | Seven EML-flavored tools exposed to the agent via Claude's tool-use API: `math_to_eml`, `eml_to_math`, `evaluate_eml`, `list_eml_identities`, `search_eml_identity`, `verify_eml`, `sympy_compute` |
| [`src/eml_research/agent.py`](src/eml_research/agent.py) | `MathAgent` — manual tool-use loop against Claude Opus 4.7 with prompt caching on the system prompt + tools |
| [`src/eml_research/problems.py`](src/eml_research/problems.py) | 16 benchmark problems with verified ground truths (EML translation, numeric evaluation, calculus, algebra) |
| [`src/eml_research/grading.py`](src/eml_research/grading.py) | Structured grader with 5 check strategies: `numeric`, `exact`, `set`, `eml_tree`, `string` |
| [`src/eml_research/benchmark.py`](src/eml_research/benchmark.py) | Runner that executes every problem, grades the agent's output, and emits a JSON report |
| [`tests/`](tests/) | 34 unit tests covering tools, grader, and ground-truth integrity (runs without the API) |

The `sympy_compute` tool is a deliberate escape hatch: the paper notes that multiplication's EML tree has K=41 and π's has K=193, which are beyond brute-force search, so the agent is told to fall back to symbolic math for those and to *note in its reasoning* why EML alone is impractical there.

## Setup

```bash
# Python 3.10+
pip install -e .
```

This installs the EML translator directly from its GitHub repository as a dependency, plus `anthropic` and `sympy`.

## Run the benchmark

Set your API key and run:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
eml-benchmark                                    # runs all 16 problems
eml-benchmark --pid eml-01 --pid eval-01         # run specific ones
eml-benchmark --model claude-sonnet-4-6          # override the model
```

Each problem runs through the agent; the agent's `FINAL ANSWER:` line is compared to the ground truth. Results are written to `benchmark_results/benchmark_<timestamp>.json` with full tool-call traces.

Example expected console output:

```
[1/16] eml-01 (eml) ...
    -> PASS  final="eml(x, 1)"  truth='eml(x, 1)'  [EML tree matches target on sample grid]  tools=[math_to_eml=1, verify_eml=1]  2.3s
[2/16] eml-02 (eml) ...
    ...
================================================================
Overall: 14/16 (87.5%) in 182s on claude-opus-4-7
----------------------------------------------------------------
  algebra     : 3/3  (100.0%)
  calculus    : 4/5  (80.0%)
  eml         : 5/5  (100.0%)
  evaluation  : 2/3  (66.7%)
================================================================
```

## Run the tests (no API key needed)

```bash
PYTHONPATH=src pytest
```

All 34 tests run offline — they verify the tool wiring, the grader, and that every benchmark ground truth is actually correct.

## Benchmark problem categories

| Category | Problems | What it tests |
| --- | --- | --- |
| `eml` | 5 | Translation to EML, tree size, Kolmogorov length — the core EML path |
| `evaluation` | 3 | Numeric evaluation via `evaluate_eml` |
| `calculus` | 5 | Derivatives, integrals, limits — expected to use `sympy_compute` |
| `algebra` | 3 | Polynomial roots and simplification |

Ground truths include `exp(2) = 7.389...`, `lim (1 + 1/x)^x = e`, `integrate exp(x) from 0 to 1 = e - 1`, and the paper's canonical EML identities like `exp(x) = eml(x, 1)` (K=3) and `ln(x) = eml(1, eml(eml(1, x), 1))` (K=7).

## Research questions this harness can answer

- Does the agent produce correct EML decompositions for problems where the paper-identified trees exist?
- When a problem would require EML trees with K > 11, does the agent correctly fall back to sympy and flag the limitation?
- Does prompt caching the EML system prompt + tools keep per-problem cost low? (`usage.cache_read_input_tokens` in each run trace answers this.)
- On which problem categories does grounding-in-EML help vs hurt accuracy? (Compare by category in the report.)

## Citing

If you use this repo, please also cite the paper and the upstream library:

```bibtex
@article{Odrzywolek2026EML,
  title   = {All elementary functions from a single operator},
  author  = {Odrzywo{\l}ek, Andrzej},
  journal = {arXiv preprint arXiv:2603.21852},
  year    = {2026},
  url     = {https://arxiv.org/abs/2603.21852},
}
```

## License

MIT (matches the upstream EML translator).

# EML Research POC

> **Run summary (latest: 2026-04-24):**
> - **General math benchmark:** 21/21 (100%) across easy–medium + graduate-level hard tracks. Details: [RESULTS.md](RESULTS.md).
> - **Riemann Hypothesis sub-investigation (4 criteria × 2 tracks = 8 subagents):** 8/8 artifacts consistent with RH, head-to-head EML vs Classical A/B. Details: [RIEMANN_REPORT.md](RIEMANN_REPORT.md).
> - **Tests:** 44/44 offline unit tests passing.
> - **Project bio, motivation, and credits:** [BIO.md](BIO.md).

Research proof-of-concept: can an AI agent solve mathematical problems more faithfully if it reasons through the **EML (Exp-Minus-Log) primitive** from Odrzywołek (2026, [arXiv:2603.21852](https://arxiv.org/abs/2603.21852))?

EML defines a single binary operator
```
eml(x, y) = exp(x) - ln(y)
```
and shows every elementary function can be expressed as a tree over the single literal `1` and nested `eml(...)` calls — the continuous-math analogue of NAND. This repo wires that primitive up as a Claude tool and measures whether the agent's answers match known ground truths.

Built on top of the upstream library [ElMatiOfficial/EML-Matemathical-Translator-for-AI](https://github.com/ElMatiOfficial/EML-Matemathical-Translator-for-AI).

## Repository layout

| Path | Purpose |
| --- | --- |
| [`src/eml_research/tools.py`](src/eml_research/tools.py) | Seven EML-flavored tools exposed to the agent via Claude's tool-use API: `math_to_eml`, `eml_to_math`, `evaluate_eml`, `list_eml_identities`, `search_eml_identity`, `verify_eml`, `sympy_compute` |
| [`src/eml_research/cli.py`](src/eml_research/cli.py) | `eml-tool` CLI wrapper — subagents call tools via bash |
| [`src/eml_research/agent.py`](src/eml_research/agent.py) | `MathAgent` — manual tool-use loop against Claude Opus 4.7 with prompt caching |
| [`src/eml_research/problems.py`](src/eml_research/problems.py) | 21 benchmark problems across `eml`, `eval`, `calc`, `alg`, and `hard` categories with verified ground truths |
| [`src/eml_research/grading.py`](src/eml_research/grading.py) | Structured grader with 5 check strategies: `numeric`, `exact`, `set`, `eml_tree`, `string` |
| [`src/eml_research/benchmark.py`](src/eml_research/benchmark.py) | SDK-based runner (alternative to Claude Code subagents) |
| [`src/eml_research/riemann/`](src/eml_research/riemann/) | Riemann-Hypothesis multi-agent investigation — 4 RH-equivalent criteria, EML-vs-Classical A/B |
| [`examples/`](examples/) | Six self-contained, runnable demonstrations — start here |
| [`scripts/`](scripts/) | Grader + compiler scripts for subagent-produced artifacts |
| [`tests/`](tests/) | 44 offline unit tests (tool wiring, grader, every ground truth) |
| [`benchmark_results/riemann/`](benchmark_results/riemann/) | Archived subagent artifacts from Run 3 (RH investigation) |
| [`riemann.pdf`](riemann.pdf) | Bombieri's Clay Institute paper (the source for Run 3) |

The `sympy_compute` tool is a deliberate escape hatch: the paper notes that multiplication's EML tree has K=41 and π's has K=193, which are beyond brute-force search, so the agent is told to fall back to symbolic math for those and to *note in its reasoning* why EML alone is impractical there.

## Quickstart

```bash
# Install (Python 3.10+)
pip install -e .

# Walk through the seven EML tools in one pass
python examples/01_eml_basics.py

# Solve five hard graduate-level problems via sympy_compute
python examples/02_hard_problems_via_sympy.py

# Independently reproduce the Riemann T1 numerical check (no API key)
python examples/03_riemann_zeros_on_critical_line.py

# Run the tests (44, offline)
pytest
```

Full index of examples: [`examples/README.md`](examples/README.md).

## Running the benchmarks

Two routes exist; both have been used in this repo.

**Route A — Claude Code subagents (what Runs 1–3 used).** From a Claude Code session in this repo, spawn `general-purpose` subagents with one problem each via the `Agent` tool. Each subagent calls `eml-tool <name> '<json>'` via bash and returns a `FINAL ANSWER:` line. The grader at [`scripts/grade_run.py`](scripts/grade_run.py) compares each answer to the ground truth. No separate API billing — this uses your Claude Code subscription quota.

**Route B — Anthropic SDK runner.** With an `ANTHROPIC_API_KEY` set, `eml-benchmark` runs the same 21 problems through the `MathAgent` class (Opus 4.7 with prompt caching on the tool+system prefix). This is billed per-token to the API account attached to the key.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
eml-benchmark                             # run all problems
eml-benchmark --pid hard-01 --pid hard-02 # run specific ones
eml-benchmark --model claude-sonnet-4-6   # override the model
```

## What the runs revealed

Short version: the agents reach 100% on every task we've tried, but for calculus / algebra / RH-analytic work they go through `sympy_compute` and largely *ignore* the EML tools. EML pays its rent on the eml-translate / evaluate / verify problems where the paper's K ≤ 11 identities live. The honest A/B analysis is in [BIO.md](BIO.md) and [RIEMANN_REPORT.md](RIEMANN_REPORT.md).

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

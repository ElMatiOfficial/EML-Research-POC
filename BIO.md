# About this repo

## The question this POC exists to answer

Can an AI agent do better mathematical research if it reasons through the **EML (Exp-Minus-Log) primitive** — a single binary operator `eml(x, y) = exp(x) − ln(y)` — rather than the usual menu of operators (`+`, `−`, `×`, `/`, `^`, trig, log, exp, …)?

Odrzywołek (2026, [arXiv:2603.21852](https://arxiv.org/abs/2603.21852)) proved that EML, combined with the literal `1`, is **universal for elementary mathematics** — the continuous-math analogue of NAND in digital logic. This repo wires EML up as a tool-use capability the agent can call and runs controlled benchmarks to see whether that framing helps.

## What's here

- [`src/eml_research/tools.py`](src/eml_research/tools.py) — seven EML tools exposed to the agent (`math_to_eml`, `eml_to_math`, `evaluate_eml`, `list_eml_identities`, `search_eml_identity`, `verify_eml`, `sympy_compute`)
- [`src/eml_research/cli.py`](src/eml_research/cli.py) — `eml-tool` CLI wrapper so Claude Code subagents can call the tools via bash
- [`src/eml_research/agent.py`](src/eml_research/agent.py) — `MathAgent` (Anthropic SDK loop with prompt caching on the tool+system prefix)
- [`src/eml_research/problems.py`](src/eml_research/problems.py) — 21-problem math benchmark with verified ground truths (easy → graduate-level hard)
- [`src/eml_research/grading.py`](src/eml_research/grading.py) — structured grader (numeric / exact / set / eml_tree / string checks)
- [`src/eml_research/riemann/`](src/eml_research/riemann/) — a multi-agent investigation of RH-equivalent numerical criteria motivated by Bombieri's Clay Institute exposition
- [`examples/`](examples/) — runnable, self-contained demos (basics, hard problems, and each of the four Riemann criteria)
- [`tests/`](tests/) — 44 offline unit tests covering tools, grader, and ground-truth integrity

## Run history (documented)

| Run | Scope | Result | Report |
|---|---|---|---|
| 1 | 16 easy–medium math problems via 16 Claude Code subagents | 16/16 | [RESULTS.md](RESULTS.md) |
| 2 | 5 graduate-level hard problems (Gaussian/Dirichlet/1/(x⁴+1) integrals, Stirling, nested limit) | 5/5 | [RESULTS.md](RESULTS.md) |
| 3 | Riemann Hypothesis — 4 criteria × 2 tracks (EML vs Classical) | 8/8 artifacts consistent with RH | [RIEMANN_REPORT.md](RIEMANN_REPORT.md) |

All subagent artifacts from Run 3 live at [`benchmark_results/riemann/`](benchmark_results/riemann/). The tests directory validates every ground truth independently (44/44 passing).

## Honest framing

- **This repo will not prove the Riemann Hypothesis.** RH has been open since 1859; no swarm of language-model agents is closing it. What we built is a rigorous harness for checking RH-equivalent sub-criteria and comparing EML-flavored vs classical approaches on the same sub-problems.
- **EML did not provide a computational shortcut on the RH tasks we tested.** The analytic number-theory regime leans heavily on products and trig, both of which have infeasible EML Kolmogorov length in the currently registered identity set. The EML-track agents correctly fell back to mpmath on every load-bearing computation. See [RIEMANN_REPORT.md](RIEMANN_REPORT.md) for the A/B analysis.
- **EML *is* a natural substrate for the paper's core identities** (exp, ln, e, small subtractions — K ≤ 11) and for the 8/8 eml/eval problems in Run 1 the agents used EML tools directly. The limitation is about where the registry is today, not about EML as a concept.

## Credits

- **Andrzej Odrzywołek** — EML primitive and the universality theorem ([arXiv:2603.21852](https://arxiv.org/abs/2603.21852)).
- **ElMatiOfficial** — upstream [EML-Matemathical-Translator-for-AI](https://github.com/ElMatiOfficial/EML-Matemathical-Translator-for-AI) library, which this POC vendors as a git dependency; also the repository owner and author of this POC.
- **Enrico Bombieri** — the Clay Millennium Institute paper on the Riemann Hypothesis (the PDF in-repo at [`riemann.pdf`](riemann.pdf)), which motivated the task decomposition for Run 3.
- **Claude Code** — Anthropic's Claude Opus 4.7 (1M context) running in Claude Code. Used both as the orchestration layer and, via the `Agent` tool, as the worker pool for every benchmark subagent.

## Reproducing the runs

```bash
pip install -e .
pytest                                  # 44 offline unit tests
python examples/01_eml_basics.py        # walk through the seven tools
python examples/03_riemann_zeros_on_critical_line.py   # reference T1 computation
```

For the subagent-orchestrated benchmark runs (Runs 1–3), use Claude Code with the prompt templates referenced in [`examples/README.md`](examples/README.md). The subagent runs consume your Claude Code subscription quota; there is no separate API billing. See the cost notes in the session history of past commits for details.

## License

MIT (matches the upstream EML translator library).

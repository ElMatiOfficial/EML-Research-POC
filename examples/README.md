# Examples

Curated, runnable demonstrations of the EML tool layer and the multi-agent investigations built on top of it. Every example in this directory is self-contained and runnable with `python examples/<name>.py` after `pip install -e .`.

| File | What it shows |
|---|---|
| [`01_eml_basics.py`](01_eml_basics.py) | The seven EML tools in one pass — translate, evaluate, verify, search |
| [`02_hard_problems_via_sympy.py`](02_hard_problems_via_sympy.py) | `sympy_compute` solving the five graduate-level hard problems |
| [`03_riemann_zeros_on_critical_line.py`](03_riemann_zeros_on_critical_line.py) | Computes the first 20 non-trivial zeros of ζ and verifies they sit on Re(s)=½ |
| [`04_riemann_li_criterion.py`](04_riemann_li_criterion.py) | Computes Li's λₙ for n=1..10 and confirms positivity (RH-equivalent, Li 1997) |
| [`05_riemann_robin_criterion.py`](05_riemann_robin_criterion.py) | Checks σ(n) < e^γ·n·log log n for 5040 < n ≤ 10000 (RH-equivalent, Robin 1984) |
| [`06_riemann_pair_correlation.py`](06_riemann_pair_correlation.py) | Empirical pair correlation of normalized zero spacings vs Montgomery's GUE form |

## Running them

```bash
pip install -e .
python examples/01_eml_basics.py
python examples/03_riemann_zeros_on_critical_line.py   # takes ~1 min; high precision
```

All six run offline and require no Claude API key. The subagent-orchestration flow (which needs Claude Code) is documented in [`../RESULTS.md`](../RESULTS.md) and [`../RIEMANN_REPORT.md`](../RIEMANN_REPORT.md); the examples here are the *pure computation* half of those runs and can be used to verify the agents' numerical claims independently.

## Subagent prompt templates

The exact prompts used to spawn Claude Code subagents for the benchmark and Riemann runs are embedded in [`../src/eml_research/benchmark.py`](../src/eml_research/benchmark.py) (for the general math benchmark via the Anthropic SDK) and in [`../src/eml_research/riemann/README.md`](../src/eml_research/riemann/README.md) (for the RH investigation). See those files for the templates and the track-split (EML-first vs Classical-only) rules.

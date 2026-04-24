# Riemann Hypothesis multi-agent investigation

This subpackage frames an **agentic investigation** of the Riemann Hypothesis (RH),
using the Bombieri Clay Institute exposition as the motivating source.

**This will not prove RH.** The Riemann Hypothesis has been open for 166 years; a swarm of
Claude Code subagents armed with mpmath, sympy, and EML will not close it. What this POC
*does* is produce verifiable numerical artifacts on **RH-equivalent criteria** with a clean
A/B split between two tracks:

- **EML track** — the agent is told to express the quantity it is investigating in EML
  (Odrzywolek 2026) form first, then compute numerically. Any exp/log/subtract fragment
  becomes a candidate for `math_to_eml`.
- **Classical track** — the agent is forbidden from using the `eml-tool` CLI and must
  work only with `sympy` and `mpmath`.

Each of 4 sub-tasks is run independently by both tracks, so every agent's work has a
head-to-head counterpart.

## Architecture

```
                [Strategist -- hardcoded in this README]
                                │
            ┌───────────────────┴───────────────────┐
            │                                       │
    ┌───────▼───────┐                       ┌───────▼───────┐
    │   EML Track   │                       │   Classical   │
    └───┬───────────┘                       └───┬───────────┘
        │                                       │
        ├── T1: first 20 zeros on Re=1/2 ───────┤
        ├── T2: Li's lambda_n >= 0 --───────────┤
        ├── T3: Robin's sigma-bound ────────────┤
        └── T4: Montgomery GUE pair-correlation ┘
                            │
                [Synthesis -- scripts/riemann_compile.py]
```

## Tasks

See [`tasks.py`](tasks.py) for the full structured definitions, each carrying:
- `bombieri_ref` — which section of the PDF motivates the task
- `objective` — what to compute
- `method_hint` — a concrete numerical recipe
- `success_criterion` — what counts as confirming / refuting RH on this criterion
- `expected_signals` — spot-check values (independently verified in the repo's tests)
- `eml_angle` — how EML framing might contribute (empirical — may well be "not at all")

| TID | Criterion | RH equivalent? |
|-----|-----------|----------------|
| T1 | First 20 non-trivial zeros have Re(s)=1/2 and |ζ(s)|≈0 | necessary (not equivalent — finite check) |
| T2 | Li's λₙ ≥ 0 for n=1..10 computed with first 200 zeros | equivalent (Li 1997) |
| T3 | σ(n)/(n·log log n) < e^γ for 5040 < n ≤ 10000 | equivalent (Robin 1984) |
| T4 | Normalized zero spacings match Montgomery's GUE form | conjecturally related |

## Running

Subagents are spawned with pre-written prompts (one per track×task cell). Each writes
a JSON artifact to `benchmark_results/riemann/{TID}_{TRACK}.json` and returns a
`VERDICT:` line for coarse scoreboarding.

Run compilation/synthesis with:
```
python scripts/riemann_compile.py benchmark_results/riemann/
```
It grades each artifact against the task's `expected_signals` and writes a head-to-head
comparison to `RIEMANN_REPORT.md` at the repo root.

## What an EML-vs-Classical split can and cannot tell us

- **Can:** measure whether EML framing adds information on sub-problems where the raw
  machinery (log ζ, the explicit formula's exp/log pieces, the Li sum's log expansion)
  has exp-minus-log structure. The comparison is fair only in this local sense.
- **Cannot:** adjudicate which approach is "closer to a proof". The sub-tasks here are
  numerical or elementary-analytic; the hard analytic content of RH lives elsewhere.

Treat this as infrastructure for a broader investigation, not as a proof attempt.

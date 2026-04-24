"""Compile Riemann-investigation subagent artifacts into a head-to-head report.

Each subagent writes `benchmark_results/riemann/{TID}_{TRACK}.json` with a small
structured payload. This script reads every artifact, grades its numeric claims
against the task's expected_signals, and writes RIEMANN_REPORT.md at the repo root.

Artifact schema (per agent):
{
  "task_id": "T1",
  "track":   "EML" | "Classical",
  "approach": "string describing method",
  "key_results": { task-specific numeric fields },
  "verdict":  "consistent_with_RH" | "inconsistent_with_RH" | "inconclusive",
  "eml_observations": "string"   # EML track only; may be empty
}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from eml_research.riemann.tasks import TASKS, by_tid


ARTIFACT_DIR_DEFAULT = Path("benchmark_results/riemann")
REPORT_PATH_DEFAULT = Path("RIEMANN_REPORT.md")


def load_artifacts(root: Path) -> dict[tuple[str, str], dict]:
    found: dict[tuple[str, str], dict] = {}
    for path in root.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            print(f"[skip] {path}: bad JSON ({err})", file=sys.stderr)
            continue
        tid = payload.get("task_id") or path.stem.split("_")[0]
        track = payload.get("track") or path.stem.split("_")[-1]
        found[(tid, track)] = payload
    return found


def grade_T1(key: dict) -> tuple[bool, str]:
    max_abs_zeta = float(key.get("max_abs_zeta", 1.0))
    gamma_1 = float(key.get("gamma_1", 0.0))
    gamma_1_ref = 14.134725141734693
    ok_zeta = max_abs_zeta < 1e-15
    ok_gamma = abs(gamma_1 - gamma_1_ref) < 1e-6
    if ok_zeta and ok_gamma:
        return True, f"gamma_1 matches ({gamma_1:.6f}); max|zeta(rho_n)| = {max_abs_zeta:.2e} < 1e-15"
    reasons = []
    if not ok_zeta:
        reasons.append(f"max|zeta(rho)| = {max_abs_zeta:.2e} not < 1e-15")
    if not ok_gamma:
        reasons.append(f"gamma_1 = {gamma_1:.6f} vs ref {gamma_1_ref:.6f}")
    return False, "; ".join(reasons)


def grade_T2(key: dict) -> tuple[bool, str]:
    lambdas = key.get("lambdas") or {}
    if not lambdas:
        return False, "no 'lambdas' field"
    values = []
    for n in range(1, 11):
        key_n = str(n)
        if key_n not in lambdas:
            return False, f"missing lambda_{n}"
        values.append(float(lambdas[key_n]))
    if not all(v > 0 for v in values):
        neg = [(i + 1, v) for i, v in enumerate(values) if v <= 0]
        return False, f"non-positive lambda at {neg}"
    # sanity: lambda_1 should be near 0.021 with K=200
    ok_l1 = abs(values[0] - 0.02103) < 0.005
    ok_l10 = abs(values[9] - 2.0733) < 0.2
    msg = f"all 10 positive; lambda_1={values[0]:.5f}, lambda_10={values[9]:.4f}"
    return ok_l1 and ok_l10, msg


def grade_T3(key: dict) -> tuple[bool, str]:
    max_ratio = float(key.get("max_ratio", 99.0))
    e_gamma = 1.7810724179901979
    if max_ratio >= e_gamma:
        return False, f"max_ratio {max_ratio:.6f} >= e^gamma {e_gamma:.6f}"
    return True, f"max sigma(n)/(n*log log n) = {max_ratio:.6f} < e^gamma = {e_gamma:.6f}"


def grade_T4(key: dict) -> tuple[bool, str]:
    dev = key.get("max_abs_deviation_from_F")
    if dev is None:
        return False, "no 'max_abs_deviation_from_F' field"
    try:
        dev_f = float(dev)
    except (TypeError, ValueError):
        return False, f"non-numeric deviation: {dev!r}"
    # 500 zeros gives noisy pair-correlation; accept <= 0.30 as consistent with RH
    ok = dev_f <= 0.30
    return ok, f"max |empirical - F(u)| = {dev_f:.3f} (tolerance <= 0.30)"


GRADERS = {"T1": grade_T1, "T2": grade_T2, "T3": grade_T3, "T4": grade_T4}


def _fmt_key_results(key: dict) -> str:
    if not isinstance(key, dict):
        return str(key)
    parts = []
    for k, v in key.items():
        if isinstance(v, dict) and len(v) <= 12:
            inner = ", ".join(f"{kk}={vv}" for kk, vv in v.items())
            parts.append(f"{k} = {{{inner}}}")
        else:
            parts.append(f"{k} = {v}")
    return " \\| ".join(parts)


def compile_report(artifacts: dict[tuple[str, str], dict], out: Path) -> int:
    lines: list[str] = []
    lines.append("# Riemann Hypothesis — multi-agent investigation report")
    lines.append("")
    lines.append(
        "This report is the head-to-head output of 4 tasks × 2 tracks (EML vs Classical) "
        "run as parallel Claude Code subagents. Each task checks an RH-equivalent (or "
        "RH-consistent) numerical criterion motivated by Bombieri's Clay Institute paper."
    )
    lines.append("")
    lines.append("| TID | Task | EML verdict | Classical verdict | EML passes grader | Classical passes grader |")
    lines.append("| --- | --- | --- | --- | --- | --- |")

    totals = {"EML": [0, 0], "Classical": [0, 0]}
    per_task_rows: list[tuple[str, str, str, str, str, str, str]] = []

    for task in TASKS:
        tid = task.tid
        row = [tid, task.title[:60]]
        per_task_detail: list[str] = [f"### {tid}: {task.title}", ""]
        per_task_detail.append(f"**Bombieri ref:** {task.bombieri_ref}")
        per_task_detail.append("")
        per_task_detail.append(f"**Objective:** {task.objective}")
        per_task_detail.append("")
        for track in ("EML", "Classical"):
            art = artifacts.get((tid, track))
            if art is None:
                row.append("_missing_")
                row.append("_missing_")
                continue
            verdict = art.get("verdict", "inconclusive")
            grader = GRADERS.get(tid)
            grader_pass, grader_msg = grader(art.get("key_results", {})) if grader else (False, "no grader")
            totals[track][1] += 1
            if grader_pass:
                totals[track][0] += 1
            row.append(verdict)
            row.append(f"{'PASS' if grader_pass else 'FAIL'} — {grader_msg}")

            per_task_detail.append(f"**{track} track** — verdict: `{verdict}`; grader: "
                                    f"{'PASS' if grader_pass else 'FAIL'} ({grader_msg})")
            per_task_detail.append("")
            per_task_detail.append(f"  Approach: {art.get('approach','-')}")
            per_task_detail.append("")
            per_task_detail.append(f"  Key results: {_fmt_key_results(art.get('key_results', {}))}")
            per_task_detail.append("")
            if track == "EML":
                eml_obs = art.get("eml_observations", "")
                per_task_detail.append(f"  EML observations: {eml_obs or '_none_'}")
                per_task_detail.append("")
        per_task_rows.append(tuple(row))  # for header row assembly

        # Flatten into the main summary row
        eml_verdict = row[2] if len(row) > 2 else "_missing_"
        cls_verdict = row[3] if len(row) > 3 else "_missing_"
        eml_grade = row[4] if len(row) > 4 else "_missing_"
        cls_grade = row[5] if len(row) > 5 else "_missing_"
        lines.append(f"| {tid} | {task.title[:60]} | {eml_verdict} | {cls_verdict} | {eml_grade} | {cls_grade} |")

        # Save details for later
        task.__dict__["_detail_block"] = "\n".join(per_task_detail)

    lines.append("")
    lines.append("## Tallies")
    lines.append("")
    lines.append(f"- **EML track:** {totals['EML'][0]}/{totals['EML'][1]} tasks pass the grader")
    lines.append(f"- **Classical track:** {totals['Classical'][0]}/{totals['Classical'][1]} tasks pass the grader")
    lines.append("")
    lines.append("## Per-task details")
    lines.append("")
    for task in TASKS:
        lines.append(task.__dict__.get("_detail_block", f"### {task.tid}\n(no artifacts)"))
        lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written to {out}")
    failures = (totals["EML"][1] - totals["EML"][0]) + (totals["Classical"][1] - totals["Classical"][0])
    return 0 if failures == 0 else 1


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else ARTIFACT_DIR_DEFAULT
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else REPORT_PATH_DEFAULT
    if not root.exists():
        print(f"ERROR: artifact dir {root} does not exist", file=sys.stderr)
        return 2
    artifacts = load_artifacts(root)
    if not artifacts:
        print(f"ERROR: no JSON artifacts found in {root}", file=sys.stderr)
        return 2
    print(f"Loaded {len(artifacts)} artifacts from {root}")
    return compile_report(artifacts, out)


if __name__ == "__main__":
    sys.exit(main())

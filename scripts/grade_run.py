"""Grade a set of agent answers collected from Claude Code subagents.

Usage:
    python scripts/grade_run.py <answers.json>

The JSON file maps problem_id -> agent final-answer string.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from eml_research.grading import grade
from eml_research.problems import PROBLEMS, by_pid


def run(answers: dict[str, str]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for pid, ans in answers.items():
        p = by_pid(pid)
        if p is None:
            results.append({"pid": pid, "correct": False, "reason": "unknown problem id"})
            continue
        verdict = grade(ans, p)
        results.append(
            {
                "pid": pid,
                "category": p.category,
                "question": p.question,
                "agent_final": ans,
                "truth": str(p.truth),
                "check": p.check,
                "correct": verdict.correct,
                "reason": verdict.reason,
                "normalized_answer": verdict.normalized_answer,
                "normalized_truth": verdict.normalized_truth,
            }
        )
    # any problems we have but didn't run
    missing = [p.pid for p in PROBLEMS if p.pid not in answers]
    passed = sum(1 for r in results if r.get("correct"))
    return {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "accuracy": passed / max(len(results), 1),
        "missing": missing,
        "by_category": _per_category(results),
        "results": results,
    }


def _per_category(results):
    acc: dict[str, dict] = {}
    for r in results:
        cat = r.get("category", "?")
        slot = acc.setdefault(cat, {"total": 0, "passed": 0})
        slot["total"] += 1
        if r.get("correct"):
            slot["passed"] += 1
    for slot in acc.values():
        slot["accuracy"] = slot["passed"] / max(slot["total"], 1)
    return acc


def _print_report(report: dict[str, Any]) -> None:
    print("=" * 72)
    print(f"Claude Code subagent benchmark")
    print(f"Overall: {report['passed']}/{report['total']} "
          f"({report['accuracy']*100:.1f}%)")
    print("-" * 72)
    print(f"{'PID':10s} {'CAT':10s} {'OK':4s} {'AGENT':28s} {'TRUTH':18s} {'REASON'}")
    for r in report["results"]:
        status = "PASS" if r.get("correct") else "FAIL"
        agent = (r.get("agent_final") or "")[:28]
        truth = (r.get("truth") or "")[:18]
        print(f"{r['pid']:10s} {r.get('category','?'):10s} {status:4s} {agent:28s} {truth:18s} {r.get('reason','')}")
    print("-" * 72)
    for cat, slot in sorted(report["by_category"].items()):
        print(f"  {cat:12s}: {slot['passed']}/{slot['total']} ({slot['accuracy']*100:.1f}%)")
    if report["missing"]:
        print(f"  (skipped: {report['missing']})")
    print("=" * 72)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    answers = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    report = run(answers)
    _print_report(report)
    out_path = Path("benchmark_results") / "claude_code_run.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nReport written to {out_path}")
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

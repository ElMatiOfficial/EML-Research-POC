"""Benchmark runner: for each problem, run the agent and grade against ground truth."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

from eml_research.agent import DEFAULT_MODEL, MathAgent
from eml_research.grading import Verdict, grade
from eml_research.problems import PROBLEMS, Problem, by_pid


def _render_tool_summary(run) -> str:
    if not run.tool_calls:
        return "<no tool calls>"
    counts: dict[str, int] = {}
    for call in run.tool_calls:
        counts[call["name"]] = counts.get(call["name"], 0) + 1
    return ", ".join(f"{name}={n}" for name, n in sorted(counts.items()))


def run_benchmark(
    problems: list[Problem],
    *,
    model: str = DEFAULT_MODEL,
    max_iterations: int = 12,
    output_dir: Path | None = None,
    verbose: bool = True,
) -> dict:
    agent = MathAgent(model=model, max_iterations=max_iterations)
    results: list[dict] = []
    t_start = time.time()

    for i, p in enumerate(problems, 1):
        if verbose:
            print(f"[{i}/{len(problems)}] {p.pid} ({p.category}) ...", flush=True)
        t0 = time.time()
        run = agent.solve(p.question)
        elapsed = time.time() - t0
        verdict = grade(run.final_answer, p) if run.error is None else Verdict(
            correct=False, reason=f"agent error: {run.error}"
        )
        results.append(
            {
                "pid": p.pid,
                "category": p.category,
                "tags": p.tags,
                "question": p.question,
                "truth": str(p.truth),
                "check": p.check,
                "agent_final": run.final_answer,
                "agent_answer_text": run.answer_text,
                "correct": verdict.correct,
                "reason": verdict.reason,
                "normalized_answer": verdict.normalized_answer,
                "normalized_truth": verdict.normalized_truth,
                "iterations": run.iterations,
                "stop_reason": run.stop_reason,
                "tool_calls_count": len(run.tool_calls),
                "tool_call_summary": _render_tool_summary(run),
                "usage": run.usage,
                "elapsed_sec": round(elapsed, 2),
                "error": run.error,
            }
        )
        if verbose:
            status = "PASS" if verdict.correct else "FAIL"
            print(
                f"    -> {status}  final={run.final_answer!r}  truth={p.truth!r}  "
                f"[{verdict.reason}]  tools=[{_render_tool_summary(run)}]  {elapsed:.1f}s",
                flush=True,
            )

    total_elapsed = time.time() - t_start
    passed = sum(1 for r in results if r["correct"])
    report = {
        "model": model,
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "accuracy": passed / max(len(results), 1),
        "elapsed_sec": round(total_elapsed, 2),
        "by_category": _per_category(results),
        "results": results,
    }

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"benchmark_{int(time.time())}.json"
        out_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        if verbose:
            print(f"\nReport written to {out_path}", flush=True)

    if verbose:
        _print_summary(report)

    return report


def _per_category(results: list[dict]) -> dict[str, dict]:
    acc: dict[str, dict] = {}
    for r in results:
        cat = r["category"]
        slot = acc.setdefault(cat, {"total": 0, "passed": 0})
        slot["total"] += 1
        if r["correct"]:
            slot["passed"] += 1
    for cat, slot in acc.items():
        slot["accuracy"] = slot["passed"] / max(slot["total"], 1)
    return acc


def _print_summary(report: dict) -> None:
    print("\n" + "=" * 64)
    print(f"Overall: {report['passed']}/{report['total']} "
          f"({report['accuracy']*100:.1f}%) in {report['elapsed_sec']}s on {report['model']}")
    print("-" * 64)
    for cat, slot in sorted(report["by_category"].items()):
        print(f"  {cat:12s}: {slot['passed']}/{slot['total']} ({slot['accuracy']*100:.1f}%)")
    print("=" * 64)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the EML Research POC benchmark.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Anthropic model ID.")
    parser.add_argument("--max-iterations", type=int, default=12)
    parser.add_argument(
        "--pid",
        action="append",
        default=None,
        help="Run only the given problem IDs (repeatable). Omit to run all.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmark_results"),
        help="Directory to write the JSON report to.",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY is not set.", file=sys.stderr)
        print(
            "Set it and retry, e.g.:  export ANTHROPIC_API_KEY=sk-ant-...",
            file=sys.stderr,
        )
        return 2

    if args.pid:
        selected = [p for pid in args.pid if (p := by_pid(pid)) is not None]
        missing = set(args.pid) - {p.pid for p in selected}
        if missing:
            print(f"ERROR: unknown problem IDs: {sorted(missing)}", file=sys.stderr)
            return 2
    else:
        selected = PROBLEMS

    report = run_benchmark(
        selected,
        model=args.model,
        max_iterations=args.max_iterations,
        output_dir=args.output_dir,
        verbose=not args.quiet,
    )
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

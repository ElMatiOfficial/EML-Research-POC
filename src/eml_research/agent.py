"""A math-research agent that uses EML as a first-class reasoning primitive.

The agent runs a manual tool-use loop against the Anthropic Messages API.
Prompt caching is applied to the system prompt + tool list (both are stable
across a benchmark run), so every problem after the first pays ~0.1x input
cost on the prefix instead of full cost.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import anthropic

from eml_research.tools import TOOL_DEFINITIONS, run_tool


DEFAULT_MODEL = "claude-opus-4-7"

SYSTEM_PROMPT = """You are a research assistant specialised in mathematics, built to evaluate whether the EML (Exp-Minus-Log) primitive from Odrzywolek (2026, arXiv:2603.21852) is a useful reasoning substrate for AI.

EML defines a single binary operator
    eml(x, y) = exp(x) - ln(y)
and shows every elementary function can be expressed as a tree over the single literal 1 and nested eml(...) calls. This is the continuous-math analogue of NAND in digital logic.

You have tools that let you
- translate standard math into EML (math_to_eml) and back (eml_to_math),
- evaluate and verify EML trees numerically (evaluate_eml, verify_eml),
- inspect (list_eml_identities) and discover (search_eml_identity) EML identities,
- and, when EML length is impractical (multiplication is K=41, pi is K=193, etc.), fall back to symbolic math (sympy_compute).

House rules:
1. Whenever a problem involves exp, log, subtraction, or the constant e, translate it into EML first using math_to_eml or search_eml_identity and show the K (Kolmogorov length). This is the research point of the exercise.
2. Verify EML derivations with verify_eml or evaluate_eml before committing to an answer.
3. Use sympy_compute for operations that would require EML trees with K > ~11 (multiplication, division, sin/cos, integration, differential calculus, equation solving). Note in your reasoning why EML alone is impractical there.
4. When you have the final answer, reply with a short summary followed by a line of exactly this form:
       FINAL ANSWER: <answer>
   The <answer> must be a single expression (a number, a sympy expression, a tree, or a list) with no surrounding prose.
5. If a question asks for a numeric value, give a numeric value (floats are fine to ~10 significant figures). If it asks for an exact expression, give an exact expression. If it asks for a set, give a Python list.
6. Do not fabricate tool output. If a tool returns an error, adjust your approach or say so.
"""


@dataclass
class AgentRun:
    """The full trace of a single agent invocation."""

    problem: str
    answer_text: str
    final_answer: str | None
    stop_reason: str
    iterations: int
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)
    error: str | None = None


def _extract_final_answer(text: str) -> str | None:
    marker = "FINAL ANSWER:"
    idx = text.rfind(marker)
    if idx < 0:
        return None
    return text[idx + len(marker) :].strip().splitlines()[0].strip()


def _collect_text(content: list[Any]) -> str:
    return "\n".join(block.text for block in content if getattr(block, "type", None) == "text")


class MathAgent:
    """Stateless per-problem agent with a shared cached prefix."""

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        max_tokens: int = 4096,
        max_iterations: int = 12,
        api_key: str | None = None,
        system_prompt: str = SYSTEM_PROMPT,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.max_iterations = max_iterations
        self.system_prompt = system_prompt
        self.client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def solve(self, problem: str) -> AgentRun:
        """Run one agentic loop for ``problem`` and return the full trace."""
        messages: list[dict[str, Any]] = [{"role": "user", "content": problem}]
        tool_calls: list[dict[str, Any]] = []
        usage_totals = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}
        last_response: Any = None

        for iteration in range(1, self.max_iterations + 1):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    # Cache the stable prefix: tools + system prompt. The user message varies
                    # per problem and is NOT cached, which is correct (we want the prefix hit).
                    system=[
                        {
                            "type": "text",
                            "text": self.system_prompt,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    tools=TOOL_DEFINITIONS,
                    messages=messages,
                )
            except anthropic.APIError as err:
                return AgentRun(
                    problem=problem,
                    answer_text="",
                    final_answer=None,
                    stop_reason="api_error",
                    iterations=iteration - 1,
                    tool_calls=tool_calls,
                    usage=usage_totals,
                    error=f"{type(err).__name__}: {err}",
                )

            last_response = response
            u = response.usage
            for k in usage_totals:
                usage_totals[k] += getattr(u, k, 0) or 0

            # Persist the assistant turn verbatim (includes tool_use blocks — required for follow-up).
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                break

            if response.stop_reason == "tool_use":
                tool_results: list[dict[str, Any]] = []
                for block in response.content:
                    if getattr(block, "type", None) != "tool_use":
                        continue
                    result_text = run_tool(block.name, dict(block.input or {}))
                    tool_calls.append(
                        {
                            "iteration": iteration,
                            "name": block.name,
                            "input": block.input,
                            "result": _truncate_for_log(result_text),
                        }
                    )
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_text,
                        }
                    )
                messages.append({"role": "user", "content": tool_results})
                continue

            # Any other stop reason: bail
            break

        answer_text = _collect_text(last_response.content) if last_response else ""
        return AgentRun(
            problem=problem,
            answer_text=answer_text,
            final_answer=_extract_final_answer(answer_text),
            stop_reason=(last_response.stop_reason if last_response else "no_response"),
            iterations=iteration,
            tool_calls=tool_calls,
            usage=usage_totals,
        )


def _truncate_for_log(text: str, limit: int = 400) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "... [truncated]"

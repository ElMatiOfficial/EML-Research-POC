"""CLI wrapper for the EML tools.

Exposes each tool in ``eml_research.tools`` as a subcommand so an agent
(including a Claude Code subagent) can invoke them from a shell::

    eml-tool --list
    eml-tool math_to_eml '{"expression": "exp(x)"}'
    eml-tool evaluate_eml '{"eml_expression": "eml(x, 1)", "bindings": {"x": 2}}'
    eml-tool sympy_compute '{"op": "integrate", "expression": "exp(x)", "variable": "x", "bounds": [0, 1]}'

All tools return a single-line JSON object with ``status: ok`` or
``status: error`` plus tool-specific fields.
"""

from __future__ import annotations

import json
import sys

from eml_research.tools import TOOL_DEFINITIONS, run_tool


def _print_tool_catalog(stream=sys.stdout) -> None:
    for t in TOOL_DEFINITIONS:
        print(f"- {t['name']}", file=stream)
        print(f"    {t['description']}", file=stream)
        print(f"    input_schema: {json.dumps(t['input_schema'])}", file=stream)


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv or argv[0] in ("-h", "--help"):
        print(
            "usage: eml-tool <tool_name> [json_args]\n"
            "       eml-tool --list\n"
            "\n"
            "Run 'eml-tool --list' to see every tool with its input schema.",
            file=sys.stderr,
        )
        return 0 if argv and argv[0] in ("-h", "--help") else 2

    if argv[0] in ("-l", "--list"):
        _print_tool_catalog()
        return 0

    name = argv[0]
    raw = argv[1] if len(argv) > 1 else "{}"
    try:
        args = json.loads(raw)
    except json.JSONDecodeError as err:
        print(
            json.dumps({"status": "error", "message": f"invalid JSON for args: {err}"}),
        )
        return 2

    if not isinstance(args, dict):
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": "args must be a JSON object, e.g. '{\"expression\": \"exp(x)\"}'",
                }
            )
        )
        return 2

    print(run_tool(name, args))
    return 0


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .ingest import TraceFormatError, sessions_from_payload
from .verification import report_to_dict, summarize_session


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-verify", description="Verify coding-agent traces.")
    commands = parser.add_subparsers(dest="command", required=True)

    analyze = commands.add_parser("analyze", help="Analyze a JSON trace file.")
    analyze.add_argument("trace", help="Trace path, or - for stdin.")
    analyze.add_argument("--source", choices=("auto", "generic", "nemo", "otel"), default="auto")
    analyze.add_argument("--format", choices=("text", "json"), default="text")
    analyze.add_argument("--output", type=Path, help="Write output to this file instead of stdout.")

    serve = commands.add_parser("serve", help="Run the FastAPI service.")
    serve.add_argument("--host", default=os.getenv("HOST", "0.0.0.0"))
    serve.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    serve.add_argument("--reload", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "serve":
        import uvicorn

        uvicorn.run(
            "agent_verification_engine.app:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
        )
        return 0

    try:
        payload = _read_payload(args.trace)
        reports = [report_to_dict(summarize_session(session)) for session in sessions_from_payload(payload, args.source)]
    except (OSError, json.JSONDecodeError, TraceFormatError, KeyError, TypeError, ValueError) as error:
        print(f"agent-verify: {error}", file=sys.stderr)
        return 2

    output = _render_json(reports) if args.format == "json" else _render_text(reports)
    if args.output:
        args.output.write_text(f"{output}\n", encoding="utf-8")
    else:
        print(output)
    return 0


def _read_payload(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open(encoding="utf-8") as trace_file:
        return json.load(trace_file)


def _render_json(reports: list[dict[str, Any]]) -> str:
    payload: Any = reports[0] if len(reports) == 1 else reports
    return json.dumps(payload, indent=2)


def _render_text(reports: list[dict[str, Any]]) -> str:
    sections: list[str] = []
    for index, report in enumerate(reports, start=1):
        lines = [
            f"Report {index}: {report['verification_status']}",
            f"Requirement: {report['requirement']}",
            "Checklist: "
            + ", ".join(f"{name}={status}" for name, status in report["verification_checklist"].items()),
            "Review order:",
        ]
        if not report["review_hotspots"]:
            lines.append("  No findings.")
        for finding in report["review_hotspots"]:
            lines.append(
                f"  {finding['review_priority']}. [{finding['severity']}] "
                f"{finding['type']}: {finding['subject']}"
            )
            lines.append(f"     Why: {finding['reason']}")
        sections.append("\n".join(lines))
    return "\n\n".join(sections)

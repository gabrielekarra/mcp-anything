"""Grade a list of MCP servers and write a leaderboard.

    python scripts/leaderboard.py                       # scripts/servers.yaml -> docs/leaderboard.md
    python scripts/leaderboard.py my-list.yaml -o board.md --timeout 120

Each server is started with its own command and graded with `mcp-anything
grade`. A server that cannot be started, or whose variables are not set, is
listed as not graded, with the reason. Running it starts every server on
the list, so run it on a machine where you are happy to do that.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

import yaml

from mcp_anything import __version__
from mcp_anything.grade import grade, grade_tools
from mcp_anything.grade.client import TargetError, tools_from_json

ROOT = Path(__file__).parent.parent


def grade_entry(entry: dict, timeout: float, base: Path) -> dict:
    row = {"name": entry["name"], "source": entry.get("source", "")}
    missing = [name for name in entry.get("env", []) if not os.environ.get(name)]
    if missing:
        return {**row, "error": f"needs {', '.join(missing)}"}
    try:
        if "tools" in entry:
            report = grade_tools(tools_from_json(json.loads((base / entry["tools"]).read_text())), entry["name"])
        else:
            report = grade(entry["target"], timeout=timeout)
    except (TargetError, OSError, ValueError) as exc:
        return {**row, "error": str(exc).split("\n")[0][:120]}
    top = report.findings[0] if report.findings else None
    return {**row, "score": report.score, "grade": report.grade, "tools": report.tools, "tokens": report.tokens,
            "top": f"{top['title']} (-{top['points']})" if top else "none"}


def render(rows: list[dict], today: str, version: str) -> str:
    graded = sorted((r for r in rows if "score" in r), key=lambda r: (-r["score"], r["name"]))
    failed = [r for r in rows if "score" not in r]
    lines = [
        "# MCP server leaderboard", "",
        f"Graded on {today} with mcp-anything {version} (`python scripts/leaderboard.py`). The grade is a static "
        "review of each server's tool list: how easy it is for an agent to choose a tool and call it correctly. "
        "It does not test whether the tools work. See `mcp-anything grade --help` for the rules.", "",
        "| Rank | Server | Grade | Score | Tools | Tool list (tokens) | Biggest finding |",
        "|---|---|---|---|---|---|---|",
    ]
    for rank, r in enumerate(graded, 1):
        name = f"[{r['name']}]({r['source']})" if r["source"] else r["name"]
        lines.append(f"| {rank} | {name} | {r['grade']} | {r['score']} | {r['tools']} | {r['tokens']:,} | {r['top']} |")
    if failed:
        lines += ["", "Not graded:", ""]
        lines += [f"- {r['name']}: {r['error']}" for r in failed]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("servers", nargs="?", type=Path, default=ROOT / "scripts" / "servers.yaml")
    parser.add_argument("-o", "--output", type=Path, default=ROOT / "docs" / "leaderboard.md")
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    entries = yaml.safe_load(args.servers.read_text())["servers"]
    rows = []
    for entry in entries:
        print(f"grading {entry['name']}...", file=sys.stderr, flush=True)
        rows.append(grade_entry(entry, args.timeout, args.servers.parent))
    args.output.write_text(render(rows, args.date, __version__))
    args.output.with_suffix(".json").write_text(json.dumps(rows, indent=2) + "\n")
    print(f"wrote {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()

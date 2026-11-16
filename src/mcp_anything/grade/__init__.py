"""Grade how usable an MCP server is for agents.

    mcp-anything grade "npx -y @modelcontextprotocol/server-filesystem ."
    mcp-anything grade https://example.com/mcp
    mcp-anything grade tools.json --format markdown --badge grade.svg --min-score 80

The score starts at 100 and each rule in rules.py takes off points. It is a
static review of the tool list (names, descriptions, schemas, annotations):
it says how easy the server is for an agent to choose from and call
correctly, not whether its tools work. `mcp-anything eval` measures that.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from mcp_anything.grade.rules import BY_ID, RULES, Finding, check, estimated_tokens, penalty

GRADES = [(90, "A"), (80, "B"), (70, "C"), (60, "D"), (0, "F")]
COLORS = {"A": "#4c1", "B": "#97ca00", "C": "#dfb317", "D": "#fe7d37", "F": "#e05d44"}
SHIELDS = {"A": "brightgreen", "B": "green", "C": "yellow", "D": "orange", "F": "red"}


@dataclass
class Report:
    target: str
    score: int
    grade: str
    tools: int
    tokens: int
    findings: list[dict] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def grade_tools(tools: list[dict], target: str = "") -> Report:
    findings = check(tools)
    lost = sum(penalty(finding, len(tools)) for finding in findings)
    score = max(0, round(100 - lost)) if tools else 0
    letter = next(letter for floor, letter in GRADES if score >= floor)
    details = []
    for finding in sorted(findings, key=lambda f: -penalty(f, len(tools))):
        rule = BY_ID[finding.rule]
        details.append({
            "rule": finding.rule, "title": rule.title, "points": round(penalty(finding, len(tools)), 1),
            "message": finding.message, "fix": rule.fix, "tools": finding.tools,
        })
    return Report(target, score, letter, len(tools), estimated_tokens(tools), details)


def grade(target: str, timeout: float = 60) -> Report:
    from mcp_anything.grade.client import load_tools

    tools, source = load_tools(target, timeout)
    return grade_tools(tools, source)


# --- reports --------------------------------------------------------------------------------


def to_text(report: Report) -> str:
    lines = [f"{report.target}", f"Grade {report.grade}  {report.score}/100   "
             f"{report.tools} tools, about {report.tokens:,} tokens of tool list", ""]
    if not report.findings:
        lines.append("No findings.")
    for item in report.findings:
        lines.append(f"-{item['points']:>5}  {item['rule']} {item['title']}: {item['message']}")
        if item["tools"]:
            shown = ", ".join(item["tools"][:8]) + (f" and {len(item['tools']) - 8} more" if len(item["tools"]) > 8 else "")
            lines.append(f"         {shown}")
        lines.append(f"         Fix: {item['fix']}")
    return "\n".join(lines)


def to_markdown(report: Report) -> str:
    lines = [f"## MCP grade: {report.grade} ({report.score}/100)", "",
             f"`{report.target}`: {report.tools} tools, about {report.tokens:,} tokens of tool list.", ""]
    if not report.findings:
        lines.append("No findings.")
        return "\n".join(lines)
    lines += ["| Points | Rule | Finding | Fix |", "|---|---|---|---|"]
    for item in report.findings:
        message = item["message"].replace("|", "\\|")
        if item["tools"]:
            message += " (" + ", ".join(f"`{name}`" for name in item["tools"][:5]) + (", ..." if len(item["tools"]) > 5 else "") + ")"
        lines.append(f"| -{item['points']} | {item['rule']} {item['title']} | {message} | {item['fix']} |")
    lines += ["", "Graded with [mcp-anything](https://github.com/gabrielekarra/mcp-anything)."]
    return "\n".join(lines)


def badge_svg(report: Report, label: str = "mcp grade") -> str:
    """A flat badge in the shields.io style, made locally."""
    value = f"{report.grade} {report.score}"
    left, right = 6 * len(label) + 12, 7 * len(value) + 12
    width, color = left + right, COLORS[report.grade]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" role="img" aria-label="{label}: {value}">'
        f'<title>{label}: {value}</title>'
        f'<linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/>'
        f'<stop offset="1" stop-opacity=".1"/></linearGradient>'
        f'<clipPath id="r"><rect width="{width}" height="20" rx="3" fill="#fff"/></clipPath>'
        f'<g clip-path="url(#r)"><rect width="{left}" height="20" fill="#555"/>'
        f'<rect x="{left}" width="{right}" height="20" fill="{color}"/>'
        f'<rect width="{width}" height="20" fill="url(#s)"/></g>'
        f'<g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">'
        f'<text x="{left / 2}" y="14">{label}</text><text x="{left + right / 2}" y="14">{value}</text></g></svg>'
    )


def shields_endpoint(report: Report, label: str = "mcp grade") -> str:
    """A shields.io endpoint file: https://img.shields.io/endpoint?url=<where you host it>."""
    return json.dumps({"schemaVersion": 1, "label": label, "message": f"{report.grade} {report.score}",
                       "color": SHIELDS[report.grade]})


__all__ = ["RULES", "Finding", "Report", "grade", "grade_tools", "to_text", "to_markdown", "badge_svg", "shields_endpoint"]

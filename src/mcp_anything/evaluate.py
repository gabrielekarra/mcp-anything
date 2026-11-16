"""Run a server's eval cases against the live server, directly or through an agent.

    mcp-anything eval ./my-server                          # call each case's tool, check the result
    mcp-anything eval ./my-server --agent --model ...      # give each use case to a model with the tools
    mcp-anything eval "npx -y some-server" --cases eval_cases.json --min-pass 0.8

Direct mode checks the tools work: each case's tool is called with its
inputs, and passes when the output matches its pattern (or the expected
error happens). Agent mode checks the server is usable: each use case is
given to a model as a task, and passes when the model calls one of the
tools the cases expect for it, within the step limit.
"""

from __future__ import annotations

import json
import re
from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Optional

SYSTEM = "You are an agent using the tools of an MCP server. Use them to do the task, then say briefly what you did."


@dataclass
class CaseResult:
    id: str
    task: str
    passed: bool
    expected: list[str]
    called: list[str] = field(default_factory=list)
    detail: str = ""
    steps: int = 0


@dataclass
class EvalReport:
    target: str
    mode: str
    results: list[CaseResult]

    @property
    def pass_rate(self) -> float:
        return sum(r.passed for r in self.results) / len(self.results) if self.results else 0.0

    def to_json(self) -> str:
        return json.dumps({"target": self.target, "mode": self.mode, "pass_rate": round(self.pass_rate, 3),
                           "passed": sum(r.passed for r in self.results), "total": len(self.results),
                           "results": [asdict(r) for r in self.results]}, indent=2)

    def to_text(self) -> str:
        lines = [f"{self.target} ({self.mode} mode)",
                 f"Passed {sum(r.passed for r in self.results)} of {len(self.results)} ({self.pass_rate:.0%})", ""]
        for r in self.results:
            mark = "pass" if r.passed else "FAIL"
            lines.append(f"  {mark}  {r.id}: {r.task[:70]}")
            if not r.passed:
                lines.append(f"        {r.detail}")
        return "\n".join(lines)


def load_cases(path: Path) -> list[dict]:
    data = json.loads(Path(path).read_text())
    return data["eval_cases"] if isinstance(data, dict) and "eval_cases" in data else data


def load_use_cases(folder: Optional[Path]) -> dict:
    """Use case id -> description, from the server's domain_model.json when there is one."""
    if not folder or not (Path(folder) / "domain_model.json").exists():
        return {}
    model = json.loads((Path(folder) / "domain_model.json").read_text())
    return {case["id"]: case["description"] for case in model.get("use_cases", []) if "id" in case}


def _text(result: dict) -> str:
    return "\n".join(part.get("text", json.dumps(part)) for part in result.get("content", []) if isinstance(part, dict))


# --- direct mode -------------------------------------------------------------------------------


def run_direct(session, cases: list[dict], target: str = "") -> EvalReport:
    results = []
    for case in cases:
        expected_error = case.get("expected_error")
        try:
            result = session.call_tool(case["tool_name"], case.get("input_params") or {})
            output, failed = _text(result), bool(result.get("isError"))
        except Exception as exc:  # the server rejected the call outright
            output, failed = str(exc), True
        if expected_error:
            passed = failed and expected_error.lower() in output.lower() or failed and not expected_error.strip()
            detail = "" if passed else f"expected an error containing {expected_error!r}, got: {output[:200]}"
        else:
            pattern = case.get("expected_output_pattern") or ""
            passed = not failed and (not pattern or bool(re.search(pattern, output)))
            detail = "" if passed else (f"the tool failed: {output[:200]}" if failed else
                                        f"output does not match {pattern!r}: {output[:200]}")
        results.append(CaseResult(case["id"], f"{case['tool_name']}({json.dumps(case.get('input_params') or {})})",
                                  passed, [case["tool_name"]], [case["tool_name"]], detail, 1))
    return EvalReport(target, "direct", results)


# --- agent mode ----------------------------------------------------------------------------------


def tasks_from(cases: list[dict], use_cases: dict) -> list[tuple[str, str, list[str]]]:
    """(use case id, task text, expected tools), one per use case covered by happy-path cases."""
    grouped: "OrderedDict[str, list[str]]" = OrderedDict()
    for case in cases:
        if case.get("case_type", "happy_path") != "happy_path":
            continue
        tools = grouped.setdefault(case.get("brief_item_id") or case["id"], [])
        if case["tool_name"] not in tools:
            tools.append(case["tool_name"])
    return [(item, use_cases.get(item) or f"Do what {', '.join(tools)} is for.", tools) for item, tools in grouped.items()]


def run_agent(session, tasks, step: Callable, target: str = "", max_steps: int = 8) -> EvalReport:
    """`step(transcript, tools, system)` returns the model's next assistant turn (see llm.tool_step)."""
    tools = session.list_tools()
    results = []
    for item, task, expected in tasks:
        transcript, called, steps, detail = [{"role": "user", "content": task}], [], 0, ""
        try:
            while True:
                if steps >= max_steps:
                    detail = f"stopped after {max_steps} steps"
                    break
                steps += 1
                turn = step(transcript, tools, SYSTEM)
                transcript.append(turn)
                if not turn["calls"]:
                    break
                outputs = []
                for call in turn["calls"]:
                    called.append(call["name"])
                    try:
                        result = session.call_tool(call["name"], call["arguments"])
                        outputs.append({"id": call["id"], "name": call["name"], "content": _text(result) or "(empty)",
                                        "error": bool(result.get("isError"))})
                    except Exception as exc:
                        outputs.append({"id": call["id"], "name": call["name"], "content": str(exc), "error": True})
                transcript.append({"role": "tool", "results": outputs})
        except Exception as exc:  # the model failed: the case fails, the run goes on
            detail = f"{type(exc).__name__}: {exc}"
        passed = not detail and any(name in expected for name in called)
        if not passed and not detail:
            detail = f"expected a call to {' or '.join(expected)}; called {', '.join(called) or 'nothing'}"
        results.append(CaseResult(item, task, passed, expected, called, detail, steps))
    return EvalReport(target, "agent", results)

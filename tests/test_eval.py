"""Issue #23: run eval cases against a live server, directly or through an agent."""

import json
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from llm_fakes import FakeModelServer
from mcp_anything import evaluate, llm
from mcp_anything.grade.client import open_session

FIXTURES = Path(__file__).parent / "fixtures" / "grade"
SERVER = f"{shlex.quote(sys.executable)} {shlex.quote(str(FIXTURES / 'eval_server.py'))} {shlex.quote(str(FIXTURES / 'clean_tools.json'))}"

CASES = [
    {"id": "ec-1", "brief_item_id": "uc-1", "tool_name": "search_issues", "input_params": {"query": "crash"},
     "expected_output_pattern": r"Found \d+ issues", "case_type": "happy_path"},
    {"id": "ec-2", "brief_item_id": "uc-2", "tool_name": "manage_issue", "input_params": {"operation": "close", "number": 7},
     "expected_output_pattern": "close done", "case_type": "happy_path"},
    {"id": "ec-3", "brief_item_id": "uc-2", "tool_name": "manage_issue", "input_params": {},
     "expected_error": "missing required", "case_type": "expected_error"},
    {"id": "ec-4", "brief_item_id": "uc-3", "tool_name": "search_issues", "input_params": {"query": "x"},
     "expected_output_pattern": "nothing like this", "case_type": "happy_path"},
]
USE_CASES = {"uc-1": "Find the issues about crashes.", "uc-2": "Close issue 7.", "uc-3": "Search for x."}


def turn(text="", *calls):
    return {"role": "assistant", "content": text, "calls": [
        {"id": f"c{n}", "name": name, "arguments": arguments} for n, (name, arguments) in enumerate(calls)], "raw": None}


def scripted(*turns):
    turns = list(turns)
    seen = []

    def step(transcript, tools, system):
        seen.append((list(transcript), [t["name"] for t in tools]))
        return turns.pop(0)

    step.seen = seen
    return step


def test_eval_direct():
    with open_session(SERVER) as session:
        report = evaluate.run_direct(session, CASES, "fake")
    assert [r.passed for r in report.results] == [True, True, True, False]
    assert "does not match" in report.results[3].detail
    assert report.pass_rate == 0.75


def test_eval_passes_with_scripted_model():
    tasks = evaluate.tasks_from(CASES[:2], USE_CASES)
    assert tasks == [("uc-1", "Find the issues about crashes.", ["search_issues"]), ("uc-2", "Close issue 7.", ["manage_issue"])]
    step = scripted(turn("", ("search_issues", {"query": "crash"})), turn("There are two."),
                    turn("", ("manage_issue", {"operation": "close", "number": 7})), turn("Closed."))
    with open_session(SERVER) as session:
        report = evaluate.run_agent(session, tasks, step, "fake")
    assert report.pass_rate == 1.0
    second_call_transcript, tool_names = step.seen[1]
    assert second_call_transcript[-1]["results"][0]["content"].startswith("Found 2 issues")
    assert tool_names == ["search_issues", "manage_issue", "delete_comment"]


def test_eval_fails_wrong_tool():
    step = scripted(turn("", ("delete_comment", {"comment_id": 1})), turn("Done."))
    with open_session(SERVER) as session:
        report = evaluate.run_agent(session, [("uc-1", "Find crash issues.", ["search_issues"])], step)
    (result,) = report.results
    assert not result.passed and result.detail == "expected a call to search_issues; called delete_comment"


def test_eval_step_limit():
    looping = lambda transcript, tools, system: turn("", ("search_issues", {"query": "again"}))  # noqa: E731
    with open_session(SERVER) as session:
        report = evaluate.run_agent(session, [("uc-1", "Find crash issues.", ["search_issues"])], looping, max_steps=3)
    (result,) = report.results
    assert not result.passed and result.steps == 3 and result.detail == "stopped after 3 steps"


def test_eval_report():
    with open_session(SERVER) as session:
        report = evaluate.run_direct(session, CASES, "fake")
    data = json.loads(report.to_json())
    assert (data["passed"], data["total"], data["pass_rate"]) == (3, 4, 0.75)
    assert "Passed 3 of 4 (75%)" in report.to_text() and "FAIL  ec-4" in report.to_text()


def test_eval_cli_min_pass(tmp_path):
    cases = tmp_path / "cases.json"
    cases.write_text(json.dumps(CASES))
    run = lambda *extra: subprocess.run([sys.executable, "-m", "mcp_anything", "eval", SERVER, "--cases", str(cases), *extra],  # noqa: E731
                                        capture_output=True, text=True)
    assert run("--min-pass", "0.7").returncode == 0
    low = run("--min-pass", "0.9", "--format", "json")
    assert low.returncode == 1 and json.loads(low.stdout.split("\n}\n")[0] + "\n}")["pass_rate"] == 0.75


def test_tool_step_openai_compatible(monkeypatch):
    payload = {"choices": [{"message": {"role": "assistant", "content": None, "tool_calls": [
        {"id": "call_1", "type": "function", "function": {"name": "search_issues", "arguments": '{"query": "crash"}'}}]}}]}
    with FakeModelServer(payloads=[payload]) as server:
        monkeypatch.setenv("MCP_ANYTHING_BASE_URL", server.url)
        transcript = [{"role": "user", "content": "find crashes"},
                      turn("", ("search_issues", {"query": "old"})),
                      {"role": "tool", "results": [{"id": "c0", "name": "search_issues", "content": "none", "error": False}]}]
        tools = json.loads((FIXTURES / "clean_tools.json").read_text())["tools"]
        result = llm.tool_step(transcript, tools, system="sys", model="vllm:x")
    assert result["calls"] == [{"id": "call_1", "name": "search_issues", "arguments": {"query": "crash"}}]
    body = server.requests[0][1]
    assert body["tools"][0]["function"]["parameters"] == tools[0]["inputSchema"]
    assert body["messages"][2]["tool_calls"][0]["function"]["arguments"] == '{"query": "old"}'
    assert body["messages"][3] == {"role": "tool", "tool_call_id": "c0", "content": "none"}


def test_tool_step_ollama(monkeypatch):
    payload = {"message": {"role": "assistant", "content": "", "tool_calls": [
        {"function": {"name": "delete_comment", "arguments": {"comment_id": 3}}}]}, "done": True}
    with FakeModelServer(payloads=[payload]) as server:
        monkeypatch.setenv("MCP_ANYTHING_BASE_URL", server.url)
        result = llm.tool_step([{"role": "user", "content": "delete 3"}], [], model="ollama:qwen3:8b")
    assert result["calls"][0]["name"] == "delete_comment" and result["calls"][0]["arguments"] == {"comment_id": 3}
    assert server.requests[0][0] == "/api/chat"

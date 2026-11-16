"""Issue #20 (grade) and issue #21 (badge, threshold and GitHub Action)."""

import copy
import json
import shlex
import subprocess
import sys
import threading
import xml.etree.ElementTree as ElementTree
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
import yaml

from mcp_anything import cli
from mcp_anything.grade import badge_svg, grade, grade_tools, shields_endpoint, to_markdown, to_text
from mcp_anything.grade.client import TargetError, tools_from_json

ROOT = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "fixtures"
CLEAN = FIXTURES / "grade" / "clean_tools.json"
SERVER = FIXTURES / "grade" / "fake_server.py"


def clean():
    return copy.deepcopy(json.loads(CLEAN.read_text())["tools"])


def tool(_name, description="Does a useful thing for the user and returns the result as text.", **params):
    properties = {key: {"type": "string", "description": f"The {key} to use."} for key in params}
    return {"name": _name, "description": description,
            "inputSchema": {"type": "object", "properties": properties, "required": list(params)}}


def broken(rule):
    tools = clean()
    if rule == "G01":
        tools += [tool(f"tool_number_{n}", f"Tool number {n} does a distinct job number {n} for the user.") for n in range(45)]
    elif rule == "G02":
        long_params = {f"field_{k}": {"type": "string", "description": f"Field {k}: " + "a detailed explanation. " * 6}
                       for k in range(12)}
        tools += [{"name": f"report_{n}", "description": f"Build report {n} for the user from many fields at once.",
                   "inputSchema": {"type": "object", "properties": long_params}, "annotations": {}} for n in range(22)]
    elif rule == "G03":
        tools[0]["description"] = ""
    elif rule == "G04":
        tools[0]["description"] = "Search issues."
    elif rule == "G05":
        tools[0]["description"] = "Search issues by text, state or label. " + "More detail about searching. " * 40
    elif rule == "G06":
        tools[0]["inputSchema"]["properties"]["query"].pop("description")
    elif rule == "G07":
        tools[0]["inputSchema"]["properties"]["query"].pop("type")
    elif rule == "G08":
        tools[1]["inputSchema"]["properties"]["body"] = {"type": "object", "description": "The issue fields."}
    elif rule == "G09":
        tools[0]["name"] = "searchIssues"
    elif rule == "G10":
        tools += [tool(f"{verb}_label", f"{verb.title()} one label on a repository and return it as JSON.", name="x")
                  for verb in ("create", "update", "list")]
    elif rule == "G11":
        tools[2].pop("annotations")
    elif rule == "G12":
        tools[0].pop("annotations")
    elif rule == "G13":
        tools.append(dict(copy.deepcopy(tools[0]), name="find_issues"))
        tools[-1]["annotations"] = {"readOnlyHint": True}
    elif rule == "G14":
        tools[1]["inputSchema"]["properties"]["title"]["description"] = "The kind of title: one of short, long."
    elif rule == "G15":
        tools[0].pop("inputSchema")
    return tools


def rules_found(tools):
    return {item["rule"] for item in grade_tools(tools).findings}


def test_clean_server_scores_high():
    report = grade_tools(clean())
    assert report.findings == [], report.findings
    assert report.score >= 90 and report.grade == "A"


@pytest.mark.parametrize("rule", [f"G{n:02}" for n in range(1, 16)])
def test_each_rule_triggers(rule):
    found = rules_found(broken(rule))
    assert rule in found, found
    if rule not in ("G01", "G02", "G10", "G13", "G15"):  # these change the tool list itself
        assert found == {rule}, found


def test_score_is_deterministic():
    tools = broken("G06") + broken("G11")[2:]
    first, second = grade_tools(tools, "x"), grade_tools(copy.deepcopy(tools), "x")
    assert first == second and to_text(first) == to_text(second)
    assert first.score < 100


def test_findings_cost_more_when_more_tools_are_affected():
    some = clean()
    some[0]["description"] = ""
    every = clean()
    for item in every:
        item["description"] = ""
    assert grade_tools(every).score < grade_tools(some).score < 100


def test_grade_stdio_server():
    report = grade(f"{shlex.quote(sys.executable)} {shlex.quote(str(SERVER))} {shlex.quote(str(CLEAN))}")
    assert report.tools == 3 and report.grade == "A"  # three tools over two pages


def test_grade_http_server():
    tools = clean()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            message = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if "id" not in message:
                self.send_response(202)
                self.end_headers()
                return
            result = {"tools": tools} if message["method"] == "tools/list" else {"protocolVersion": "2025-06-18", "capabilities": {}}
            data = f"data: {json.dumps({'jsonrpc': '2.0', 'id': message['id'], 'result': result})}\n\n".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        report = grade(f"http://127.0.0.1:{server.server_port}/mcp")
    finally:
        server.shutdown()
    assert report.tools == 3 and report.score == 100


def test_grade_generated_server(tmp_path):
    brief = tmp_path / "pet.yaml"
    brief.write_text(
        "server_name: petstore-mcp\ndomain_description: A pet store API for listing, adding and reading pets.\n"
        "use_cases:\n  - List pets\n  - Add a pet\n"
        f"data_source_path: {FIXTURES / 'petstore_openapi.json'}\ndata_source_kind: openapi\nbackend_target: fastmcp\n"
    )
    cli.main(["build", "--brief", str(brief), "-o", str(tmp_path / "pet"), "--no-llm", "--auto-approve"])
    report = grade(str(tmp_path / "pet"))
    assert report.tools >= 5
    # Even without a model, a generated server documents every parameter, uses enums
    # for allowed values and annotates destructive tools.
    assert report.score >= 90, to_text(report)
    assert {item["rule"] for item in report.findings} <= {"G10"}


def test_grade_json_file_shapes(tmp_path):
    tools = clean()
    for shape in ({"tools": tools}, {"jsonrpc": "2.0", "id": 1, "result": {"tools": tools}}, tools):
        assert len(tools_from_json(shape)) == 3
    with pytest.raises(TargetError):
        tools_from_json({"something": "else"})


def test_unreachable_targets_are_explained():
    with pytest.raises(TargetError, match="not installed or not on PATH"):
        grade("definitely-not-a-command --stdio")
    with pytest.raises(TargetError, match="exited before answering"):
        grade(f"{shlex.quote(sys.executable)} -c 'import sys; print(\"boom\", file=sys.stderr)'")


def test_report_formats():
    report = grade_tools(broken("G06") + [tool("delete_everything", name="x")], "server")
    rules = {item["rule"] for item in report.findings}
    as_json = json.loads(report.to_json())
    assert {item["rule"] for item in as_json["findings"]} == rules and as_json["score"] == report.score
    text, markdown = to_text(report), to_markdown(report)
    for rule in rules:
        assert rule in text and rule in markdown
    assert markdown.startswith(f"## MCP grade: {report.grade} ({report.score}/100)")


# --- #21 badge, threshold, action -------------------------------------------------------------


@pytest.mark.parametrize("tools, letter", [(clean(), "A"), ([tool(f"t{n}", "") for n in range(3)], "D"),
                                           ([{"name": f"t{n}"} for n in range(3)], "F")])
def test_badge_svg(tools, letter):
    from mcp_anything.grade import COLORS

    report = grade_tools(tools)
    svg = badge_svg(report)
    ElementTree.fromstring(svg)  # valid XML
    assert report.grade == letter
    assert f"{report.grade} {report.score}" in svg and COLORS[letter] in svg


def test_shields_endpoint():
    data = json.loads(shields_endpoint(grade_tools(clean())))
    assert data == {"schemaVersion": 1, "label": "mcp grade", "message": "A 100", "color": "brightgreen"}


def run_cli(*argv):
    return subprocess.run([sys.executable, "-m", "mcp_anything", "grade", *argv], capture_output=True, text=True)


def test_min_score_exit_code(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps([tool("x", "")]))
    assert run_cli(str(CLEAN), "--min-score", "90").returncode == 0
    failed = run_cli(str(bad), "--min-score", "90")
    assert failed.returncode == 1 and "below the minimum" in failed.stdout + failed.stderr


def test_cli_writes_badges_and_formats(tmp_path):
    done = run_cli(str(CLEAN), "--format", "json", "--badge", str(tmp_path / "b.svg"), "--shields", str(tmp_path / "b.json"))
    assert done.returncode == 0 and json.loads(done.stdout)["grade"] == "A"
    assert (tmp_path / "b.svg").read_text().startswith("<svg") and json.loads((tmp_path / "b.json").read_text())["schemaVersion"] == 1


def test_action_is_valid():
    action = yaml.safe_load((ROOT / "action.yml").read_text())
    assert action["runs"]["using"] == "composite"
    assert {"target", "min-score"} <= set(action["inputs"])
    script = "\n".join(step.get("run", "") for step in action["runs"]["steps"])
    assert "mcp-anything grade" in script and "GITHUB_STEP_SUMMARY" in script

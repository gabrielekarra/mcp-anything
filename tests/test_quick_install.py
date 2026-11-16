"""Issue #18 (one command from a source) and issue #19 (install into clients)."""

import json
import shutil
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
import yaml

from mcp_anything import cli, install
from mcp_anything.quick import draft_brief

FIXTURES = Path(__file__).parent / "fixtures"
PETSTORE = FIXTURES / "petstore_openapi.json"


def built(tmp_path, source, *extra):
    out = tmp_path / "out"
    cli.main([str(source), "-o", str(out), "--no-llm", *extra])
    return out


def test_quick_from_openapi_file(tmp_path):
    out = built(tmp_path, PETSTORE)
    brief = yaml.safe_load((out / "brief.yaml").read_text())
    assert brief["data_source_kind"] == "openapi" and brief["server_name"] == "petstore-api"
    assert any(case.startswith("Pets:") for case in brief["use_cases"])
    assert any(case.startswith("Store:") for case in brief["use_cases"])
    assert (out / "pyproject.toml").exists() and list(out.glob("mcp_*/server.py"))


def test_quick_from_url(tmp_path):
    served = tmp_path / "site"
    served.mkdir()
    shutil.copy(PETSTORE, served / "openapi.json")
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(served)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        out = built(tmp_path, f"http://127.0.0.1:{server.server_port}/openapi.json")
    finally:
        server.shutdown()
    assert yaml.safe_load((out / "brief.yaml").read_text())["data_source_kind"] == "openapi"
    assert list(out.glob("mcp_*/tools/*.py"))


def test_quick_from_code_folder(tmp_path):
    out = built(tmp_path, FIXTURES / "fake_flask_app")
    brief = yaml.safe_load((out / "brief.yaml").read_text())
    assert brief["data_source_kind"] == "codebase"
    assert list(out.glob("mcp_*/server.py")) or list(out.glob("src/*/server.py"))


def test_drafted_brief_rebuilds(tmp_path):
    out = built(tmp_path, PETSTORE)
    again = tmp_path / "again"
    cli.main(["build", "--brief", str(out / "brief.yaml"), "-o", str(again), "--no-llm", "--auto-approve"])
    tools = lambda folder: sorted(p.name for p in folder.glob("mcp_*/tools/*.py"))  # noqa: E731
    assert tools(again) == tools(out)


def test_brief_drafts_for_other_specs(tmp_path):
    graphql = tmp_path / "shop.graphql"
    graphql.write_text("type Query {\n  products(first: Int): [Product]\n  order(id: ID!): Order\n}\n"
                       "type Mutation {\n  placeOrder(items: [ID!]!): Order\n}\n")
    proto = tmp_path / "users.proto"
    proto.write_text("service Users {\n  rpc GetUser (GetUserRequest) returns (User);\n  rpc ListUsers (Empty) returns (Users);\n}\n")
    assert draft_brief(graphql, "graphql", "shop", use_model=False)["use_cases"] == ["Products", "Order", "Place order"]
    assert draft_brief(proto, "grpc", "users", use_model=False)["use_cases"] == ["Get user", "List users"]


def test_existing_subcommands_still_work(capsys, tmp_path):
    cli.main(["grade", str(FIXTURES / "grade" / "clean_tools.json")])
    assert "Grade A" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        cli.main(["--version"])
    with pytest.raises(SystemExit):
        cli.main([str(tmp_path / "does-not-exist.json"), "--no-llm"])


# --- #19 install ------------------------------------------------------------------------------


@pytest.fixture
def server(tmp_path):
    return built(tmp_path, PETSTORE)


@pytest.mark.parametrize("client, relative, key", [
    ("claude-code", ".claude.json", "mcpServers"),
    ("cursor", ".cursor/mcp.json", "mcpServers"),
    ("claude-desktop", ".config/Claude/claude_desktop_config.json", "mcpServers"),
    ("vscode", "project/.vscode/mcp.json", "servers"),
])
def test_install_writes_each_client(client, relative, key, server, tmp_path):
    home = tmp_path / "home"
    path = install.config_path(client, home=home, cwd=home / "project", system="Linux")
    assert path == home / relative
    launch = install.launch(server, pip=False)
    written, entry, changed = install.install(client, "petstore", launch, path=path)
    saved = json.loads(written.read_text())[key]["petstore"]
    assert changed and saved == entry
    assert saved["args"][-1].endswith(".server") and saved["args"][0] == "-m"
    if client in ("claude-code", "vscode"):
        assert saved["type"] == "stdio"


def test_claude_desktop_paths():
    home = Path("/h")
    assert install.config_path("claude-desktop", home=home, system="Darwin") == \
        home / "Library/Application Support/Claude/claude_desktop_config.json"


def test_install_merges_and_backs_up(tmp_path):
    path = tmp_path / "mcp.json"
    path.write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}, "theme": "dark"}))
    install.install("cursor", "petstore", {"command": "python", "args": ["-m", "p.server"]}, path=path)
    saved = json.loads(path.read_text())
    assert saved["mcpServers"]["other"] == {"command": "x"} and saved["theme"] == "dark"
    assert "petstore" in saved["mcpServers"]
    assert json.loads((tmp_path / "mcp.json.bak").read_text())["mcpServers"] == {"other": {"command": "x"}}


def test_install_is_idempotent(tmp_path):
    path = tmp_path / "mcp.json"
    spec = {"command": "python", "args": ["-m", "p.server"]}
    assert install.install("cursor", "p", spec, path=path)[2] is True
    before = path.read_text()
    assert install.install("cursor", "p", spec, path=path)[2] is False
    assert path.read_text() == before


def test_install_print_writes_nothing(tmp_path, monkeypatch, capsys, server):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setattr(install.Path, "home", classmethod(lambda cls: tmp_path / "home"))
    capsys.readouterr()  # drop the build's output
    cli.main(["install", str(server), "--client", "cursor", "--print"])
    printed = json.loads(capsys.readouterr().out)
    assert list(printed["mcpServers"]) == ["petstore-api"]
    assert not (tmp_path / "home" / ".cursor").exists()


def test_install_http_server(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(install.Path, "home", classmethod(lambda cls: tmp_path))
    cli.main(["install", "--url", "http://localhost:8000/mcp", "--name", "remote", "--client", "cursor",
              "--client", "claude-desktop", "--client", "claude-code"])
    assert json.loads((tmp_path / ".cursor/mcp.json").read_text())["mcpServers"]["remote"] == {"url": "http://localhost:8000/mcp"}
    assert json.loads((tmp_path / ".claude.json").read_text())["mcpServers"]["remote"] == \
        {"type": "http", "url": "http://localhost:8000/mcp"}
    desktop = next(tmp_path.rglob("claude_desktop_config.json"))
    assert json.loads(desktop.read_text())["mcpServers"]["remote"]["args"][-1] == "http://localhost:8000/mcp"


def test_quick_install_flag(tmp_path, monkeypatch):
    monkeypatch.setattr(install.Path, "home", classmethod(lambda cls: tmp_path / "home"))
    monkeypatch.setattr(install.subprocess, "run", lambda *a, **k: None)  # no pip install in tests
    built(tmp_path, PETSTORE, "--install", "cursor")
    saved = json.loads((tmp_path / "home/.cursor/mcp.json").read_text())
    assert "petstore-api" in saved["mcpServers"]

"""Tests for the CLI interface."""

import pytest
from rich.console import Console

from mcp_anything.cli import _run_domain_command, build_parser, parse_options


class TestCLIParser:
    def test_help(self, capsys):
        parser = build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])
        assert exc_info.value.code == 0

    def test_version(self, capsys):
        parser = build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        assert exc_info.value.code == 0

    def test_generate_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["generate", "/some/path", "--name", "myapp", "-v"])
        assert args.command == "generate"
        assert str(args.codebase_path) == "/some/path"
        assert args.name == "myapp"
        assert args.verbose is True

    def test_analyze_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["analyze", "/some/path", "--no-llm"])
        assert args.command == "analyze"
        assert args.no_llm is True

    def test_design_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["design", "/some/path"])
        assert args.command == "design"

    def test_status_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["status", "/some/output"])
        assert args.command == "status"

    def test_generate_with_backend(self):
        parser = build_parser()
        args = parser.parse_args(["generate", "/path", "--backend", "socket"])
        assert args.backend == "socket"

    def test_generate_with_phases(self):
        parser = build_parser()
        args = parser.parse_args(["generate", "/path", "--phases", "analyze,design"])
        options = parse_options(args)
        assert options.phases == ["analyze", "design"]

    def test_parse_options_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["generate", "/some/path"])
        options = parse_options(args)
        assert options.codebase_path.parts[-1] == "path"
        assert options.name is None
        assert options.backend is None
        assert options.resume is False
        assert options.no_llm is False

    def test_resolved_name(self):
        parser = build_parser()
        args = parser.parse_args(["generate", "/some/my-app"])
        options = parse_options(args)
        assert options.resolved_name() == "my-app"

    def test_resolved_name_override(self):
        parser = build_parser()
        args = parser.parse_args(["generate", "/some/path", "--name", "custom"])
        options = parse_options(args)
        assert options.resolved_name() == "custom"


class _FakeDomainEngine:
    """Stand-in for PipelineEngine that just records the options it was built with."""

    last_options = None

    def __init__(self, options, console):
        _FakeDomainEngine.last_options = options

    async def run_domain(self):
        return None


class TestBuildCommandServerName:
    """`build`/`model` derive the server name from --name, else the brief's own
    `server_name` field, else the brief file stem — in that order."""

    def _run(self, tmp_path, monkeypatch, brief_text, extra_args=None):
        monkeypatch.setattr(
            "mcp_anything.pipeline.engine.PipelineEngine", _FakeDomainEngine
        )
        brief_path = tmp_path / "brief.yaml"
        brief_path.write_text(brief_text)
        parser = build_parser()
        args = parser.parse_args(
            ["build", "--brief", str(brief_path), "-o", str(tmp_path / "out"), "--no-llm"]
            + (extra_args or [])
        )
        _run_domain_command(args, Console(quiet=True), phases=None)
        return _FakeDomainEngine.last_options

    def test_uses_brief_server_name_when_no_name_flag(self, tmp_path, monkeypatch):
        options = self._run(tmp_path, monkeypatch, "server_name: aracne-sim\nuse_cases: []\n")
        assert options.name == "aracne-sim"
        assert options.resolved_name() == "aracne-sim"

    def test_falls_back_to_file_stem_when_brief_has_no_server_name(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "mcp_anything.pipeline.engine.PipelineEngine", _FakeDomainEngine
        )
        brief_path = tmp_path / "my_brief.yaml"
        brief_path.write_text("use_cases: []\n")
        parser = build_parser()
        args = parser.parse_args(
            ["build", "--brief", str(brief_path), "-o", str(tmp_path / "out"), "--no-llm"]
        )
        _run_domain_command(args, Console(quiet=True), phases=None)
        assert _FakeDomainEngine.last_options.name == "my-brief"

    def test_name_flag_overrides_brief_server_name(self, tmp_path, monkeypatch):
        options = self._run(
            tmp_path,
            monkeypatch,
            "server_name: aracne-sim\nuse_cases: []\n",
            extra_args=["--name", "custom-name"],
        )
        assert options.name == "custom-name"

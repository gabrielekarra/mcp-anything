"""Tests for AST-based analysis."""

from pathlib import Path

import pytest

from mcp_anything.analysis.ast_analyzer import (
    ASTAnalysisResult,
    analyze_python_file,
    ast_results_to_capabilities,
)
from mcp_anything.analysis.scanner import scan_codebase
from mcp_anything.models.analysis import FileInfo, IPCType, Language


class TestAnalyzePythonFile:
    def test_finds_functions_in_fake_app(self, fake_cli_app):
        files = scan_codebase(fake_cli_app)
        main_file = next(f for f in files if f.path == "main.py")
        result = analyze_python_file(fake_cli_app, main_file)

        assert result is not None
        func_names = [f.name for f in result.functions]
        assert "process_file" in func_names
        assert "get_status" in func_names
        assert "list_formats" in func_names
        assert "main" in func_names

    def test_extracts_parameters(self, fake_cli_app):
        files = scan_codebase(fake_cli_app)
        main_file = next(f for f in files if f.path == "main.py")
        result = analyze_python_file(fake_cli_app, main_file)

        process_fn = next(f for f in result.functions if f.name == "process_file")
        param_names = [p.name for p in process_fn.parameters]
        assert "input_path" in param_names
        assert "output_path" in param_names
        assert "format" in param_names

    def test_extracts_types(self, fake_cli_app):
        files = scan_codebase(fake_cli_app)
        main_file = next(f for f in files if f.path == "main.py")
        result = analyze_python_file(fake_cli_app, main_file)

        process_fn = next(f for f in result.functions if f.name == "process_file")
        input_param = next(p for p in process_fn.parameters if p.name == "input_path")
        assert input_param.type == "string"

    def test_extracts_defaults(self, fake_cli_app):
        files = scan_codebase(fake_cli_app)
        main_file = next(f for f in files if f.path == "main.py")
        result = analyze_python_file(fake_cli_app, main_file)

        process_fn = next(f for f in result.functions if f.name == "process_file")
        format_param = next(p for p in process_fn.parameters if p.name == "format")
        assert format_param.required is False
        assert format_param.default == "json"

    def test_extracts_return_type(self, fake_cli_app):
        files = scan_codebase(fake_cli_app)
        main_file = next(f for f in files if f.path == "main.py")
        result = analyze_python_file(fake_cli_app, main_file)

        process_fn = next(f for f in result.functions if f.name == "process_file")
        assert process_fn.return_type == "string"

    def test_extracts_docstrings(self, fake_cli_app):
        files = scan_codebase(fake_cli_app)
        main_file = next(f for f in files if f.path == "main.py")
        result = analyze_python_file(fake_cli_app, main_file)

        process_fn = next(f for f in result.functions if f.name == "process_file")
        assert "Process" in process_fn.docstring

    def test_detects_argparse(self, fake_cli_app):
        files = scan_codebase(fake_cli_app)
        main_file = next(f for f in files if f.path == "main.py")
        result = analyze_python_file(fake_cli_app, main_file)

        assert result.has_argparse is True
        assert result.has_click is False

    def test_detects_subcommands(self, fake_cli_app):
        files = scan_codebase(fake_cli_app)
        main_file = next(f for f in files if f.path == "main.py")
        result = analyze_python_file(fake_cli_app, main_file)

        subcmd_names = [s["name"] for s in result.subcommands]
        assert "process" in subcmd_names
        assert "status" in subcmd_names
        assert "formats" in subcmd_names

    def test_extracts_argparse_arguments(self, fake_cli_app):
        files = scan_codebase(fake_cli_app)
        main_file = next(f for f in files if f.path == "main.py")
        result = analyze_python_file(fake_cli_app, main_file)

        proc_subcmd = next(s for s in result.subcommands if s["name"] == "process")
        args = proc_subcmd["arguments"]
        arg_names = [a["name"] for a in args]
        assert "input" in arg_names
        assert "output" in arg_names
        assert "format" in arg_names

        # "input" is positional → required
        input_arg = next(a for a in args if a["name"] == "input")
        assert input_arg["required"] is True
        assert input_arg["help"] == "Input file path"

        # "--format" has choices and a default
        format_arg = next(a for a in args if a["name"] == "format")
        assert format_arg["required"] is False
        assert format_arg["default"] == "json"
        assert format_arg["choices"] == ["json", "csv", "xml"]

    def test_subcommand_args_become_capability_params(self, fake_cli_app):
        files = scan_codebase(fake_cli_app)
        ast_results = {}
        for fi in files:
            if fi.language == Language.PYTHON:
                r = analyze_python_file(fake_cli_app, fi)
                if r:
                    ast_results[fi.path] = r

        capabilities = ast_results_to_capabilities(ast_results, IPCType.CLI)
        process_cap = next(c for c in capabilities if c.name == "process")

        param_names = [p.name for p in process_cap.parameters]
        assert "input" in param_names
        assert "output" in param_names
        assert "format" in param_names
        # Should NOT have the generic "args" passthrough
        assert "args" not in param_names

        format_param = next(p for p in process_cap.parameters if p.name == "format")
        assert format_param.enum_values == ["json", "csv", "xml"]

    def test_skips_non_python(self, fake_cli_app):
        fi = FileInfo(path="foo.js", language=Language.JAVASCRIPT, size_bytes=100, line_count=10)
        result = analyze_python_file(fake_cli_app, fi)
        assert result is None

    def test_handles_syntax_error(self, tmp_path):
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("def foo(:\n  pass\n")
        fi = FileInfo(path="bad.py", language=Language.PYTHON, size_bytes=20, line_count=2)
        result = analyze_python_file(tmp_path, fi)
        assert result is None


class TestAnalyzeClassMethods:
    def test_finds_class_methods(self, tmp_path):
        code = '''
class FileConverter:
    """Converts files between formats."""

    def convert(self, input_path: str, output_path: str, format: str = "json") -> str:
        """Convert a file to the specified format."""
        pass

    def supported_formats(self) -> list:
        """List supported formats."""
        return []

    def _internal_method(self):
        pass
'''
        (tmp_path / "converter.py").write_text(code)
        fi = FileInfo(path="converter.py", language=Language.PYTHON, size_bytes=200, line_count=15)
        result = analyze_python_file(tmp_path, fi)

        assert len(result.classes) == 1
        cls = result.classes[0]
        assert cls.name == "FileConverter"
        assert "Converts" in cls.docstring

        method_names = [m.name for m in cls.methods]
        assert "convert" in method_names
        assert "supported_formats" in method_names
        assert "_internal_method" in method_names


class TestASTToCapabilities:
    def test_generates_capabilities_from_functions(self, fake_cli_app):
        files = scan_codebase(fake_cli_app)
        ast_results = {}
        for fi in files:
            if fi.language == Language.PYTHON:
                result = analyze_python_file(fake_cli_app, fi)
                if result:
                    ast_results[fi.path] = result

        capabilities = ast_results_to_capabilities(ast_results, IPCType.CLI)
        cap_names = [c.name for c in capabilities]

        # Should find real functions, not just "run_main_py"
        assert "process_file" in cap_names
        assert "get_status" in cap_names
        assert "list_formats" in cap_names

    def test_capabilities_have_parameters(self, fake_cli_app):
        files = scan_codebase(fake_cli_app)
        ast_results = {}
        for fi in files:
            if fi.language == Language.PYTHON:
                result = analyze_python_file(fake_cli_app, fi)
                if result:
                    ast_results[fi.path] = result

        capabilities = ast_results_to_capabilities(ast_results, IPCType.CLI)
        process_cap = next(c for c in capabilities if c.name == "process_file")

        assert len(process_cap.parameters) == 3
        assert process_cap.parameters[0].name == "input_path"
        assert process_cap.parameters[2].name == "format"
        assert process_cap.parameters[2].required is False

    def test_subcommands_become_capabilities(self, fake_cli_app):
        files = scan_codebase(fake_cli_app)
        ast_results = {}
        for fi in files:
            if fi.language == Language.PYTHON:
                result = analyze_python_file(fake_cli_app, fi)
                if result:
                    ast_results[fi.path] = result

        capabilities = ast_results_to_capabilities(ast_results, IPCType.CLI)
        cap_names = [c.name for c in capabilities]

        assert "process" in cap_names
        assert "status" in cap_names
        assert "formats" in cap_names

    def test_skips_private_functions(self, tmp_path):
        code = '''
def public_func() -> str:
    """A public function."""
    return "hello"

def _private_func():
    pass
'''
        (tmp_path / "mod.py").write_text(code)
        fi = FileInfo(path="mod.py", language=Language.PYTHON, size_bytes=100, line_count=8)
        result = analyze_python_file(tmp_path, fi)
        caps = ast_results_to_capabilities({"mod.py": result}, None)

        cap_names = [c.name for c in caps]
        assert "public_func" in cap_names
        assert "_private_func" not in cap_names

    def test_class_methods_become_capabilities(self, tmp_path):
        code = '''
class ImageProcessor:
    def resize(self, width: int, height: int) -> str:
        """Resize an image."""
        pass

    def rotate(self, angle: float) -> str:
        """Rotate an image."""
        pass
'''
        (tmp_path / "proc.py").write_text(code)
        fi = FileInfo(path="proc.py", language=Language.PYTHON, size_bytes=150, line_count=10)
        result = analyze_python_file(tmp_path, fi)
        caps = ast_results_to_capabilities({"proc.py": result}, None)

        cap_names = [c.name for c in caps]
        assert "image_processor_resize" in cap_names
        assert "image_processor_rotate" in cap_names

        resize_cap = next(c for c in caps if c.name == "image_processor_resize")
        assert resize_cap.parameters[0].name == "width"
        assert resize_cap.parameters[0].type == "integer"

    def test_skips_test_functions(self, tmp_path):
        code = '''
def test_something():
    """A test function."""
    pass

def assert_valid(x):
    pass

def real_function(name: str) -> str:
    """A real function."""
    return name
'''
        (tmp_path / "mod.py").write_text(code)
        fi = FileInfo(path="mod.py", language=Language.PYTHON, size_bytes=100, line_count=12)
        result = analyze_python_file(tmp_path, fi)
        caps = ast_results_to_capabilities({"mod.py": result}, None)

        cap_names = [c.name for c in caps]
        assert "real_function" in cap_names
        assert "test_something" not in cap_names
        assert "assert_valid" not in cap_names

    def test_keeps_functions_ending_in_test_suffix(self, tmp_path):
        """A "_test" suffix is not a pytest convention — pytest discovery only
        recognizes a "test_" prefix — so ordinary production functions that
        happen to end in "_test" (e.g. `run_hover_test`) must not be dropped.
        Test files/dirs are already excluded upstream by the scanner.
        """
        code = '''
def run_hover_test(duration_s: float = 3.0) -> dict:
    """Run a hover stability test against the sim."""
    return {"ok": True}

def run_crawl_test(cycles: int = 6) -> dict:
    """Run a crawl gait test against the sim."""
    return {"ok": True}
'''
        (tmp_path / "mod.py").write_text(code)
        fi = FileInfo(path="mod.py", language=Language.PYTHON, size_bytes=200, line_count=10)
        result = analyze_python_file(tmp_path, fi)
        caps = ast_results_to_capabilities({"mod.py": result}, None)

        cap_names = [c.name for c in caps]
        assert "run_hover_test" in cap_names
        assert "run_crawl_test" in cap_names

    def test_skips_no_param_no_docstring_functions(self, tmp_path):
        code = '''
def setup_logging():
    pass

def helper():
    pass

def useful_function(path: str) -> str:
    """Does something useful."""
    return path
'''
        (tmp_path / "mod.py").write_text(code)
        fi = FileInfo(path="mod.py", language=Language.PYTHON, size_bytes=100, line_count=12)
        result = analyze_python_file(tmp_path, fi)
        caps = ast_results_to_capabilities({"mod.py": result}, None)

        cap_names = [c.name for c in caps]
        assert "useful_function" in cap_names
        assert "setup_logging" not in cap_names
        assert "helper" not in cap_names

    def test_categorizes_functions(self, tmp_path):
        code = '''
def get_config() -> dict:
    """Get current configuration."""
    pass

def create_project(name: str) -> str:
    """Create a new project."""
    pass

def delete_file(path: str) -> bool:
    """Delete a file."""
    pass
'''
        (tmp_path / "api.py").write_text(code)
        fi = FileInfo(path="api.py", language=Language.PYTHON, size_bytes=100, line_count=12)
        result = analyze_python_file(tmp_path, fi)
        caps = ast_results_to_capabilities({"api.py": result}, None)

        by_name = {c.name: c for c in caps}
        assert by_name["get_config"].category == "query"
        assert by_name["create_project"].category == "creation"
        assert by_name["delete_file"].category == "management"

    def test_skips_function_factories(self, tmp_path):
        code = '''
def make_color(code):
    """Create a color function."""
    def color_func(s):
        return f"\\033[{code}m{s}\\033[0m"
    return color_func

def make_formatter(style):
    """Create a formatter."""
    def fmt(text):
        return text
    return fmt

def real_tool(name: str) -> str:
    """A real tool that returns data."""
    return name
'''
        (tmp_path / "mod.py").write_text(code)
        fi = FileInfo(path="mod.py", language=Language.PYTHON, size_bytes=200, line_count=16)
        result = analyze_python_file(tmp_path, fi)
        caps = ast_results_to_capabilities({"mod.py": result}, None)

        cap_names = [c.name for c in caps]
        assert "real_tool" in cap_names
        assert "make_color" not in cap_names
        assert "make_formatter" not in cap_names

    def test_keeps_function_with_unrelated_nested_helper(self, tmp_path):
        """A nested helper def plus a `return <local var>` is not a closure
        factory — only a return that actually names the nested def is. Before
        the fix, any function with *any* nested helper that also returned a
        local variable by name (a very common pattern) was misclassified as
        `returns_callable` and silently dropped.
        """
        code = '''
def run_crawl_test(cycles: int = 6) -> dict:
    """Run a crawl test and aggregate per-joint stats."""
    def stats(arr: list) -> dict:
        if not arr:
            return {"peak": 0.0}
        return {"peak": max(arr)}

    result = {"cycles": cycles, "joint": stats([1, 2, 3])}
    return result
'''
        (tmp_path / "mod.py").write_text(code)
        fi = FileInfo(path="mod.py", language=Language.PYTHON, size_bytes=200, line_count=12)
        result = analyze_python_file(tmp_path, fi)
        caps = ast_results_to_capabilities({"mod.py": result}, None)

        assert "run_crawl_test" in [c.name for c in caps]

    def test_skips_sys_exit_functions(self, tmp_path):
        code = '''
import sys

def quit(s, code=0):
    """Quit the application."""
    if s is not None:
        print(s)
    sys.exit(code)

def abort(msg: str):
    """Abort with error."""
    import os
    os._exit(1)

def real_tool(path: str) -> str:
    """Process a file."""
    return path
'''
        (tmp_path / "mod.py").write_text(code)
        fi = FileInfo(path="mod.py", language=Language.PYTHON, size_bytes=200, line_count=16)
        result = analyze_python_file(tmp_path, fi)
        caps = ast_results_to_capabilities({"mod.py": result}, None)

        cap_names = [c.name for c in caps]
        assert "real_tool" in cap_names
        assert "quit" not in cap_names
        assert "abort" not in cap_names


class TestArgparseExtraction:
    def test_extracts_store_true_as_boolean(self, tmp_path):
        code = '''
import argparse

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    build = sub.add_parser("build", help="Build the project")
    build.add_argument("--verbose", action="store_true", help="Enable verbose output")
    build.add_argument("--clean", action="store_true", help="Clean before build")
    build.add_argument("target", help="Build target")
'''
        (tmp_path / "cli.py").write_text(code)
        fi = FileInfo(path="cli.py", language=Language.PYTHON, size_bytes=300, line_count=10)
        result = analyze_python_file(tmp_path, fi)

        assert len(result.subcommands) == 1
        build = result.subcommands[0]
        args = build["arguments"]

        verbose = next(a for a in args if a["name"] == "verbose")
        assert verbose["type"] == "boolean"
        assert verbose["required"] is False

        target = next(a for a in args if a["name"] == "target")
        assert target["required"] is True

    def test_extracts_typed_arguments(self, tmp_path):
        code = '''
import argparse

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    run = sub.add_parser("run", help="Run task")
    run.add_argument("--port", type=int, default=8080, help="Port number")
    run.add_argument("--rate", type=float, help="Rate limit")
'''
        (tmp_path / "cli.py").write_text(code)
        fi = FileInfo(path="cli.py", language=Language.PYTHON, size_bytes=200, line_count=8)
        result = analyze_python_file(tmp_path, fi)

        run = result.subcommands[0]
        args = run["arguments"]

        port = next(a for a in args if a["name"] == "port")
        assert port["type"] == "integer"
        assert port["default"] == "8080"

        rate = next(a for a in args if a["name"] == "rate")
        assert rate["type"] == "float"


class TestClickExtraction:
    def test_extracts_click_options(self, tmp_path):
        code = '''
import click

@click.command()
@click.argument("url")
@click.option("--output", "-o", type=str, default="out.json", help="Output file path")
@click.option("--timeout", type=int, default=30, help="Request timeout")
def fetch(url, output, timeout):
    """Fetch data from a URL."""
    pass
'''
        (tmp_path / "cli.py").write_text(code)
        fi = FileInfo(path="cli.py", language=Language.PYTHON, size_bytes=300, line_count=12)
        result = analyze_python_file(tmp_path, fi)

        assert result.has_click is True
        fetch_fn = next(f for f in result.functions if f.name == "fetch")
        param_names = [p.name for p in fetch_fn.parameters]
        assert "url" in param_names
        assert "output" in param_names
        assert "timeout" in param_names

        # Check url is required (argument)
        url_param = next(p for p in fetch_fn.parameters if p.name == "url")
        assert url_param.required is True

        # Check timeout has correct type
        timeout_param = next(p for p in fetch_fn.parameters if p.name == "timeout")
        assert timeout_param.type == "integer"

    def test_click_boolean_flags(self, tmp_path):
        code = '''
import click

@click.command()
@click.option("--verbose/--no-verbose", default=False, help="Enable verbose")
def run(verbose):
    """Run something."""
    pass
'''
        (tmp_path / "cli.py").write_text(code)
        fi = FileInfo(path="cli.py", language=Language.PYTHON, size_bytes=200, line_count=8)
        result = analyze_python_file(tmp_path, fi)

        run_fn = next(f for f in result.functions if f.name == "run")
        verbose_param = next(p for p in run_fn.parameters if p.name == "verbose")
        assert verbose_param.type == "boolean"

    def test_click_choice_becomes_enum(self, tmp_path):
        code = '''
import click

@click.command()
@click.option("--format", type=click.Choice(["json", "csv", "xml"]), default="json", help="Format")
def convert(format):
    """Convert something."""
    pass
'''
        (tmp_path / "cli.py").write_text(code)
        fi = FileInfo(path="cli.py", language=Language.PYTHON, size_bytes=200, line_count=8)
        result = analyze_python_file(tmp_path, fi)

        convert_fn = next(f for f in result.functions if f.name == "convert")
        fmt_param = next(p for p in convert_fn.parameters if p.name == "format")
        assert fmt_param.enum_values == ["json", "csv", "xml"]

    def test_click_commands_detected(self):
        """Test Click commands in the fixture app are found."""
        fixture_dir = Path(__file__).parent / "fixtures" / "fake_click_app"
        fi = FileInfo(path="cli.py", language=Language.PYTHON, size_bytes=500, line_count=30)
        result = analyze_python_file(fixture_dir, fi)

        assert result is not None
        assert result.has_click is True
        func_names = [f.name for f in result.functions]
        assert "fetch" in func_names
        assert "convert" in func_names

        # fetch should be detected as CLI command
        cli_cmd_names = [f.name for f in result.cli_commands]
        assert "fetch" in cli_cmd_names


class TestTyperExtraction:
    def test_extracts_typer_params(self, tmp_path):
        code = '''
import typer

app = typer.Typer()

@app.command()
def hello(
    name: str = typer.Option(..., help="Your name"),
    count: int = typer.Option(1, help="Number of greetings"),
    filename: str = typer.Argument(..., help="File to process"),
):
    """Say hello."""
    pass
'''
        (tmp_path / "cli.py").write_text(code)
        fi = FileInfo(path="cli.py", language=Language.PYTHON, size_bytes=300, line_count=14)
        result = analyze_python_file(tmp_path, fi)

        assert result.has_typer is True
        hello_fn = next(f for f in result.functions if f.name == "hello")
        param_names = [p.name for p in hello_fn.parameters]
        assert "name" in param_names
        assert "count" in param_names
        assert "filename" in param_names

        # name is required (Ellipsis default)
        name_param = next(p for p in hello_fn.parameters if p.name == "name")
        assert name_param.required is True
        assert name_param.description == "Your name"

        # count has default
        count_param = next(p for p in hello_fn.parameters if p.name == "count")
        assert count_param.required is False
        assert count_param.type == "integer"

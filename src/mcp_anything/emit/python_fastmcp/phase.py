"""Python/FastMCP emit phase (Phase 3, Python target)."""

import ast
from pathlib import Path

from mcp_anything.emit.base import EmitPhase
from mcp_anything.models.design import ServerDesign
from mcp_anything.pipeline.context import PipelineContext


class PythonFastMCPEmitPhase(EmitPhase):
    """Emits a Python/FastMCP MCP server from a ServerDesign."""

    name = "emit"
    backend_target = "fastmcp"

    async def execute(self, ctx: PipelineContext) -> None:
        design = self._load_design(ctx)
        output_dir = Path(ctx.manifest.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        emitter = PythonFastMCPEmitter(design, output_dir)
        generated = emitter.emit_all()

        # Validate all generated Python files
        ctx.console.print("    Validating generated Python...")
        errors = self._validate_python(output_dir, generated)
        if errors:
            for path, err in errors:
                ctx.console.print(f"    [red]Syntax error in {path}:[/red] {err}")
            raise RuntimeError("Generated files have syntax errors — this is a bug in mcp-anything.")

        ctx.manifest.generated_files.extend(generated)
        ctx.console.print(f"    Generated {len(generated)} files (all valid Python)")

        contract_results = self.validate_contract(design, output_dir)
        ctx.manifest.contract_check_results = [c.model_dump() for c in contract_results]
        failed = [c for c in contract_results if not c.passed]
        if failed:
            ctx.console.print(
                f"    [yellow]Contract warnings: {[c.id for c in failed]}[/yellow]"
            )

        ctx.save_manifest()

    def _load_design(self, ctx: PipelineContext) -> ServerDesign:
        if ctx.manifest.design:
            return ctx.manifest.design
        if ctx.manifest.tool_spec:
            return ServerDesign.model_validate(ctx.manifest.tool_spec)
        raise RuntimeError("No design available for code generation.")

    def _validate_python(self, output_dir: Path, generated: list[str]) -> list[tuple[str, str]]:
        errors = []
        for rel_path in generated:
            if not rel_path.endswith(".py"):
                continue
            full = output_dir / rel_path
            if not full.exists():
                continue
            try:
                ast.parse(full.read_text())
            except SyntaxError as exc:
                errors.append((rel_path, str(exc)))
        return errors


class PythonFastMCPEmitter:
    """Renders Python/FastMCP server files from a ServerDesign."""

    def __init__(self, design: ServerDesign, output_dir: Path) -> None:
        self.design = design
        self.output_dir = output_dir
        base_name = design.server_name.replace("-", "_")
        self.package_name = f"mcp_{base_name}"
        self.generated_files: list[str] = []
        # Domain pipeline emitter always uses inline generation, not legacy Jinja2 templates
        self._use_jinja = False

    def emit_all(self) -> list[str]:
        self._emit_server()
        self._emit_tools()
        self._emit_discovery()
        self._emit_telemetry()
        self._emit_dockerfile()
        self._emit_pyproject()
        return self.generated_files

    def _write(self, rel_path: str, content: str) -> None:
        full = self.output_dir / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)
        self.generated_files.append(rel_path)

    def _emit_server(self) -> None:
        if self._use_jinja:
            try:
                content = self._jinja_env.get_template("server.py.j2").render(
                    design=self.design,
                    package_name=self.package_name,
                )
                self._write(f"{self.package_name}/server.py", content)
                return
            except Exception:
                pass

        # Inline fallback
        tool_imports = "\n".join(
            f"from .tools.{t.name} import {t.name}"
            for t in self.design.tools
        )
        tool_registrations = "\n".join(
            f"mcp.tool()({t.name})"
            for t in self.design.tools
        )
        telemetry_import = "from .telemetry import record_call  # noqa: F401" if self.design.enable_telemetry else ""

        content = f'''"""MCP server for {self.design.server_name}."""
import os
from fastmcp import FastMCP

{telemetry_import}
{tool_imports}

mcp = FastMCP("{self.design.server_name}")
mcp.description = """{self.design.server_description}"""

{tool_registrations}

if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "{self.design.transport}")
    if transport == "http":
        mcp.run(transport="http", host="{self.design.http_host}", port={self.design.http_port})
    else:
        mcp.run()
'''
        self._write(f"{self.package_name}/server.py", content)
        self._write(f"{self.package_name}/__init__.py", f'"""Generated MCP server: {self.design.server_name}."""\n')

    def _emit_tools(self) -> None:
        self._write(f"{self.package_name}/tools/__init__.py", "")
        for tool in self.design.tools:
            params_sig = self._render_params_sig(tool)
            params_body = self._render_params_body(tool)
            impl = tool.impl
            call_code = self._render_call(tool)

            content = f'''"""Tool: {tool.name}."""
import os
from typing import Any, Optional
{self._render_tool_imports(tool)}

async def {tool.name}({params_sig}) -> Any:
    """{tool.description}"""
    _verbose = verbose if "verbose" in dir() else False
{params_body}
{call_code}
'''
            self._write(f"{self.package_name}/tools/{tool.name}.py", content)

    def _render_params_sig(self, tool) -> str:
        parts = []
        for p in tool.parameters:
            py_type = self._to_py_type(p.type)
            if not p.required:
                default = "None" if py_type.startswith("Optional") else "None"
                parts.append(f"{p.name}: Optional[{py_type}] = {default}")
            else:
                parts.append(f"{p.name}: {py_type}")
        return ", ".join(parts)

    def _render_params_body(self, tool) -> str:
        params = [p for p in tool.parameters if p.name != "verbose" and p.required]
        if not params:
            return "    params = {}"
        lines = ["    params = {"]
        for p in params:
            lines.append(f'        "{p.name}": {p.name},')
        lines.append("    }")
        return "\n".join(lines)

    def _render_call(self, tool) -> str:
        impl = tool.impl
        if impl.strategy == "http_call" and impl.http_method and impl.http_path:
            base_url_env = f"{self.design.server_name.upper().replace('-','_')}_BASE_URL"
            return f'''    import httpx
    base_url = os.environ.get("{base_url_env}", "http://localhost:8000")
    url = base_url + f"{impl.http_path}"
    async with httpx.AsyncClient() as client:
        resp = await client.{impl.http_method.lower()}(url, params={{k: v for k, v in params.items() if v is not None}})
        resp.raise_for_status()
        result = resp.json()
    if verbose:
        return {{"data": result, "_meta": {{"status": resp.status_code}}}}
    return result'''
        return '    return {"status": "not_implemented", "tool": "' + tool.name + '"}'

    def _render_tool_imports(self, tool) -> str:
        if tool.impl.strategy == "http_call":
            return ""
        return ""

    def _to_py_type(self, t: str) -> str:
        mapping = {
            "string": "str",
            "integer": "int",
            "boolean": "bool",
            "array": "list",
            "object": "dict",
            "number": "float",
        }
        return mapping.get(t, "str")

    def _emit_discovery(self) -> None:
        if not self.design.discovery_endpoint:
            return
        tool_groups_json = str([
            {"name": g.name, "disclosure_level": g.disclosure_level}
            for g in self.design.tool_groups
        ])
        content = f'''"""Discovery endpoint: GET /.well-known/mcp"""
import json
from typing import Any


def get_discovery_info() -> dict:
    """Return server discovery information per CONTRACT C-01..C-03."""
    tools = _get_tool_list()
    return {{
        "server_name": "{self.design.server_name}",
        "version": "1.0.0",
        "tool_count": len(tools),
        "tool_groups": {tool_groups_json},
        "tools": tools,
    }}


def _get_tool_list() -> list:
    return {[{"name": t.name, "description": t.description[:80]} for t in self.design.tools]}
'''
        self._write(f"{self.package_name}/discovery.py", content)

    def _emit_telemetry(self) -> None:
        if not self.design.enable_telemetry:
            return
        content = '''"""Anonymized per-call telemetry (CONTRACT C-19, C-20).

Logs tool name, latency, and status only. Never logs parameter values.
Set MCP_TELEMETRY_ENDPOINT to enable remote reporting; unset to disable.
"""
import os
import time
import logging
from typing import Any, Callable

_logger = logging.getLogger("mcp.telemetry")
_ENDPOINT = os.environ.get("MCP_TELEMETRY_ENDPOINT", "")


def record_call(tool_name: str, latency_ms: float, status: str) -> None:
    _logger.info(
        '{"tool": "%s", "latency_ms": %.1f, "status": "%s"}',
        tool_name, latency_ms, status,
    )
    if _ENDPOINT:
        _send_remote(tool_name, latency_ms, status)


def _send_remote(tool_name: str, latency_ms: float, status: str) -> None:
    try:
        import urllib.request, json
        payload = json.dumps({"tool": tool_name, "latency_ms": latency_ms, "status": status})
        req = urllib.request.Request(
            _ENDPOINT,
            data=payload.encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=1)
    except Exception:
        pass  # telemetry must never break tool execution
'''
        self._write(f"{self.package_name}/telemetry.py", content)

    def _emit_dockerfile(self) -> None:
        content = f'''# Generated Dockerfile for {self.design.server_name}
# CONTRACT C-17, C-18: no embedded secrets; reads API keys from environment at runtime.
FROM python:3.12-slim

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -e .

EXPOSE 8000

ENV MCP_TRANSPORT=http

CMD ["python", "-m", "{self.package_name}.server"]
'''
        self._write("Dockerfile", content)

    def _emit_pyproject(self) -> None:
        deps = "\n".join(f'    "{d}",' for d in self.design.dependencies)
        content = f'''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{self.package_name}"
version = "1.0.0"
description = "{self.design.server_description[:80]}"
requires-python = "{self.design.python_requires}"
dependencies = [
{deps}
    "fastmcp>=0.1",
    "httpx>=0.24",
]

[project.scripts]
{self.design.server_name} = "{self.package_name}.server:main"
'''
        self._write("pyproject.toml", content)

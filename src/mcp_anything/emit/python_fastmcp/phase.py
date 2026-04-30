"""Python/FastMCP emit phase (Phase 3, Python target)."""

import ast
import keyword
import re
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

        # Compile any .proto files referenced by grpc_call tools so the runtime
        # `from {pkg}.proto_stubs import ..._pb2` imports actually resolve.
        if any(t.impl.grpc_proto_module for t in design.tools):
            stubs = self._compile_proto_stubs(ctx, output_dir, emitter.package_name, design)
            if stubs:
                generated.extend(stubs)

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

    def _compile_proto_stubs(
        self, ctx: PipelineContext, output_dir: Path, pkg_name: str, design: ServerDesign
    ) -> list[str]:
        """Compile .proto files into {pkg_name}/proto_stubs/ for grpc_call tools."""
        try:
            from grpc_tools import protoc
        except ImportError:
            raise RuntimeError(
                "grpc_call tools require grpcio-tools at generation time so protobuf "
                "stubs can be emitted. Install with: pip install grpcio-tools"
            )

        proto_modules = {
            t.impl.grpc_proto_module
            for t in design.tools
            if t.impl.grpc_proto_module
        }
        codebase = Path(ctx.manifest.codebase_path)
        # codebase_path may point at the .proto file itself (domain pipeline) — search its parent
        search_root = codebase.parent if codebase.is_file() else codebase
        stubs_dir = output_dir / pkg_name / "proto_stubs"
        stubs_dir.mkdir(parents=True, exist_ok=True)

        generated: list[str] = []
        (stubs_dir / "__init__.py").write_text('"""Compiled gRPC protobuf stubs."""\n')
        generated.append(f"{pkg_name}/proto_stubs/__init__.py")

        for module_stem in proto_modules:
            proto_files = list(search_root.rglob(f"{module_stem}.proto"))
            if not proto_files:
                raise RuntimeError(
                    f"Proto file '{module_stem}.proto' not found in codebase; "
                    "cannot emit executable grpc_call tools."
                )
            proto_file = proto_files[0]
            ret = protoc.main([
                "grpc_tools.protoc",
                f"--proto_path={proto_file.parent}",
                f"--python_out={stubs_dir}",
                f"--grpc_python_out={stubs_dir}",
                str(proto_file),
            ])
            if ret != 0:
                raise RuntimeError(
                    f"Proto compilation failed for {proto_file.name}; "
                    "cannot emit executable grpc_call tools."
                )

            for suffix in ("_pb2.py", "_pb2_grpc.py"):
                rel = f"{pkg_name}/proto_stubs/{module_stem}{suffix}"
                if (output_dir / rel).exists():
                    generated.append(rel)

            grpc_stub = stubs_dir / f"{module_stem}_pb2_grpc.py"
            if grpc_stub.exists():
                content = grpc_stub.read_text()
                patched = re.sub(
                    r"^import (\w+_pb2) as (\w+)$",
                    r"from . import \1 as \2",
                    content,
                    flags=re.MULTILINE,
                )
                if patched != content:
                    grpc_stub.write_text(patched)

            ctx.console.print(f"    Compiled {proto_file.name} → {pkg_name}/proto_stubs/")

        return generated

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


def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "{self.design.transport}")
    if transport == "http":
        mcp.run(transport="http", host="{self.design.http_host}", port={self.design.http_port})
    else:
        mcp.run()


if __name__ == "__main__":
    main()
'''
        self._write(f"{self.package_name}/server.py", content)
        self._write(f"{self.package_name}/__init__.py", f'"""Generated MCP server: {self.design.server_name}."""\n')

    _COMPACT_HELPER = '''
def _compact(data, _depth: int = 0):
    """Return a token-friendly subset of data. Full payload available via verbose=True."""
    if _depth > 3:
        return data
    if isinstance(data, dict):
        return {k: _compact(v, _depth + 1) for k, v in list(data.items())[:20]}
    if isinstance(data, list):
        return [_compact(x, _depth + 1) for x in data[:10]]
    if isinstance(data, str) and len(data) > 300:
        return data[:300] + "…"
    return data
'''

    def _emit_tools(self) -> None:
        self._write(f"{self.package_name}/tools/__init__.py", "")
        for tool in self.design.tools:
            params_sig = self._render_params_sig(tool)
            params_body = self._render_params_body(tool)
            call_code = self._render_call(tool)

            content = f'''"""Tool: {tool.name}."""
import os
from typing import Any, Optional
{self._render_tool_imports(tool)}
{self._COMPACT_HELPER}

async def {tool.name}({params_sig}) -> Any:
    """{tool.description}"""
{params_body}
{call_code}
'''
            self._write(f"{self.package_name}/tools/{tool.name}.py", content)

    def _render_params_sig(self, tool) -> str:
        parts = []
        ordered = sorted(
            tool.parameters,
            key=lambda p: (p.name == "verbose", not p.required, p.name),
        )
        for p in ordered:
            name = self._safe_py_identifier(p.name)
            py_type = self._to_py_type(p.type)
            if p.name == "verbose":
                parts.append("verbose: bool = False")
            elif not p.required:
                parts.append(f"{name}: Optional[{py_type}] = None")
            else:
                parts.append(f"{name}: {py_type}")
        return ", ".join(parts)

    def _render_params_body(self, tool) -> str:
        params = [p for p in tool.parameters if p.name != "verbose"]
        if not params:
            return "    params = {}"
        lines = ["    params = {"]
        for p in params:
            local_name = self._safe_py_identifier(p.name)
            api_name = getattr(p, "api_name", "") or p.name
            lines.append(f'        "{api_name}": {local_name},')
        lines.append("    }")
        return "\n".join(lines)

    def _render_call(self, tool) -> str:
        impl = tool.impl

        if impl.strategy == "http_call" and impl.http_method and impl.http_path:
            base_url_env = f"{self.design.server_name.upper().replace('-','_')}_BASE_URL"
            spec_default = self.design.backend_base_url or "http://localhost:8000"
            constants_repr = repr(dict(impl.http_query_constants))
            param_styles = {}
            for p in tool.parameters:
                if p.name == "verbose":
                    continue
                api_name = getattr(p, "api_name", "") or p.name
                mapping = impl.arg_mapping.get(p.name, {})
                style = mapping.get("style") or getattr(p, "location", "") or "query"
                if style not in {"path", "body", "query"}:
                    style = "query"
                param_styles[api_name] = style
            ua_default = f"{self.design.server_name}-mcp/1.0 (+https://github.com/Type-MCP/mcp-anything)"
            return f'''    import httpx
    from urllib.parse import quote
    base_url = os.environ.get("{base_url_env}", "{spec_default}")
    url = base_url + {impl.http_path!r}
    query = {{}}
    body_fields = {{}}
    param_styles = {param_styles!r}
    for key, val in params.items():
        if val is None:
            continue
        style = param_styles.get(key, "query")
        if style == "path":
            url = url.replace("{{" + key + "}}", quote(str(val), safe=""))
        elif style == "body":
            body_fields[key] = val
        else:
            query[key] = str(val)
    # Constants merged after dynamic params so explicit constants always win.
    query.update({constants_repr})
    headers = {{"User-Agent": "{ua_default}"}}
    async with httpx.AsyncClient(headers=headers) as client:
        resp = await client.request("{impl.http_method.upper()}", url, params=query, json=body_fields or None)
        resp.raise_for_status()
        result = resp.json()
    if verbose:
        return {{"data": result, "_meta": {{"status": resp.status_code}}}}
    return _compact(result)'''

        if impl.strategy == "grpc_call" and impl.grpc_service and impl.grpc_method:
            stub_module = impl.grpc_proto_module or "service"
            request_type = repr(impl.grpc_request_type or "")
            service_name = repr(impl.grpc_service.rsplit(".", 1)[-1])
            method_name = repr(impl.grpc_method)
            return f'''    import grpc
    from {self.package_name}.proto_stubs import {stub_module}_pb2, {stub_module}_pb2_grpc
    target = os.environ.get("{self.design.server_name.upper().replace("-", "_")}_GRPC_TARGET", "localhost:50051")
    request_type_name = {request_type}
    if not request_type_name:
        file_descriptor = getattr({stub_module}_pb2, "DESCRIPTOR", None)
        service_descriptor = (
            file_descriptor.services_by_name.get({service_name})
            if file_descriptor is not None else None
        )
        method_descriptor = (
            service_descriptor.methods_by_name.get({method_name})
            if service_descriptor is not None else None
        )
        request_type_name = method_descriptor.input_type.name if method_descriptor else ""
    if not request_type_name:
        request_type_name = "{impl.grpc_method}Request"
    request_cls = getattr({stub_module}_pb2, request_type_name, None)
    if request_cls is None:
        raise AttributeError(
            "Could not resolve protobuf request message "
            + repr(request_type_name)
            + " for {impl.grpc_service}.{impl.grpc_method}"
        )
    request = request_cls(**{{k: v for k, v in params.items() if v is not None}})
    async with grpc.aio.insecure_channel(target) as channel:
        stub = {stub_module}_pb2_grpc.{impl.grpc_service}Stub(channel)
        response = await stub.{impl.grpc_method}(request)
    from google.protobuf.json_format import MessageToDict
    result = MessageToDict(response, preserving_proto_field_name=True)
    if verbose:
        return {{"data": result, "_meta": {{"service": "{impl.grpc_service}", "method": "{impl.grpc_method}"}}}}
    return _compact(result)'''

        if impl.strategy == "cli_subcommand" and impl.cli_subcommand:
            bin_env = f"{self.design.server_name.upper().replace('-','_')}_BIN"
            default_bin = self.design.server_name
            return f'''    import asyncio
    binary = os.environ.get("{bin_env}", "{default_bin}")
    args = [binary, "{impl.cli_subcommand}"]
    for key, val in params.items():
        if val is None:
            continue
        if isinstance(val, bool):
            if val:
                args.append(f"--{{key.replace('_', '-')}}")
        else:
            args.extend([f"--{{key.replace('_', '-')}}", str(val)])
    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    output = stdout.decode("utf-8", errors="replace") or stderr.decode("utf-8", errors="replace")
    if verbose:
        return {{"stdout": stdout.decode("utf-8", errors="replace"), "stderr": stderr.decode("utf-8", errors="replace"), "returncode": proc.returncode}}
    return _compact({{"output": output, "returncode": proc.returncode}})'''

        if impl.strategy == "python_call" and impl.python_module and impl.python_function:
            if impl.python_class:
                init_param_names = [p.name for p in impl.python_init_params] if impl.python_init_params else []
                init_filter = f"{init_param_names!r}"
                return f'''    import importlib
    mod = importlib.import_module("{impl.python_module}")
    cls = getattr(mod, "{impl.python_class}")
    _init_keys = {init_filter}
    init_args = {{k: v for k, v in params.items() if k in _init_keys and v is not None}}
    method_args = {{k: v for k, v in params.items() if k not in _init_keys and v is not None}}
    instance = cls(**init_args)
    method = getattr(instance, "{impl.python_function}")
    result = method(**method_args)
    import inspect
    if inspect.isawaitable(result):
        result = await result
    if verbose:
        return {{"data": result, "_meta": {{"module": "{impl.python_module}", "class": "{impl.python_class}", "method": "{impl.python_function}"}}}}
    return _compact(result)'''
            return f'''    import importlib
    mod = importlib.import_module("{impl.python_module}")
    fn = getattr(mod, "{impl.python_function}")
    call_args = {{k: v for k, v in params.items() if v is not None}}
    result = fn(**call_args)
    import inspect
    if inspect.isawaitable(result):
        result = await result
    if verbose:
        return {{"data": result, "_meta": {{"module": "{impl.python_module}", "function": "{impl.python_function}"}}}}
    return _compact(result)'''

        # Final fallback — only reached when no strategy fields are populated.
        # Configure your backend by setting the appropriate env vars or override this tool.
        return f'''    raise NotImplementedError(
        "Tool '{tool.name}' has no executable strategy. "
        "Configure the data source (OpenAPI/gRPC) or implement this tool manually."
    )'''

    def _render_tool_imports(self, tool) -> str:
        if tool.impl.strategy == "http_call":
            return ""
        return ""

    def _safe_py_identifier(self, value: str) -> str:
        s = re.sub(r"[^a-zA-Z0-9_]", "_", value)
        s = re.sub(r"_+", "_", s).strip("_")
        if not s:
            s = "param"
        if s[0].isdigit():
            s = f"p_{s}"
        if keyword.iskeyword(s):
            s = f"{s}_"
        return s

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
        # Merge design deps with required base deps; drop duplicates by package name
        base_deps = {"fastmcp": "fastmcp>=0.1", "httpx": "httpx>=0.27.0", "mcp": "mcp>=1.0"}
        # Conditionally pull in grpc/protobuf if any tool needs them
        if any(t.impl.strategy == "grpc_call" for t in self.design.tools):
            base_deps["grpcio"] = "grpcio>=1.60.0"
            base_deps["protobuf"] = "protobuf>=4.24.0"
        merged: dict[str, str] = {}
        for d in self.design.dependencies:
            key = d.split(">=")[0].split("==")[0].split("<")[0].strip()
            merged[key] = d
        for pkg, pin in base_deps.items():
            if pkg not in merged:
                merged[pkg] = pin
        deps = "\n".join(f'    "{v}",' for v in merged.values())
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
]

[project.scripts]
{self.design.server_name} = "{self.package_name}.server:main"
'''
        self._write("pyproject.toml", content)

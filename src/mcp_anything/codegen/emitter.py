"""Orchestrates file generation from a ServerDesign."""

from pathlib import Path

from mcp_anything.codegen.renderer import create_jinja_env
from mcp_anything.models.design import ServerDesign
from mcp_anything.pipeline.design import _assign_generation_status


class Emitter:
    """Renders Jinja2 templates into a generated MCP server package."""

    def __init__(self, design: ServerDesign, output_dir: Path) -> None:
        self.design = design
        self.output_dir = output_dir
        self.env = create_jinja_env()
        # Prefix with mcp_ to avoid collisions with the target library
        base_name = design.server_name.replace("-", "_")
        self.package_name = f"mcp_{base_name}"
        self.generated_files: list[str] = []
        for tool in self.design.tools:
            if tool.generation_notes or tool.manual_steps or tool.generation_status != "ready":
                continue
            _assign_generation_status(tool, self.design.backend)

    def _write(self, rel_path: str, content: str) -> None:
        """Write content to a file relative to output_dir."""
        full_path = self.output_dir / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        self.generated_files.append(rel_path)

    def _render(self, template_name: str, **kwargs) -> str:
        """Render a template with the design context."""
        template = self.env.get_template(template_name)
        return template.render(design=self.design, package_name=self.package_name, **kwargs)

    def emit_all(self) -> list[str]:
        """Generate all files for the MCP server package."""
        self._emit_package_init()
        self._emit_server()
        self._emit_models()
        self._emit_state()
        self._emit_backend()
        self._emit_bridge_component()
        self._emit_tool_modules()
        self._emit_resource_modules()
        self._emit_prompt_modules()
        return self.generated_files

    def emit_docs(self) -> list[str]:
        """Generate documentation."""
        start = len(self.generated_files)
        self._emit_readme()
        self._emit_agents_md()
        return self.generated_files[start:]

    def emit_agents_only(self) -> list[str]:
        """Generate only AGENTS.md, without README (used by mcp-use target)."""
        start = len(self.generated_files)
        self._emit_agents_md()
        return self.generated_files[start:]

    def emit_packaging(self) -> list[str]:
        """Generate packaging files."""
        start = len(self.generated_files)
        self._emit_pyproject()
        self._emit_mcp_json()
        return self.generated_files[start:]

    def _emit_package_init(self) -> None:
        src_dir = f"src/{self.package_name}"
        self._write(f"{src_dir}/__init__.py", f'"""MCP server for {self.design.server_name}."""\n')

    def _emit_server(self) -> None:
        content = self._render("server.py.j2")
        self._write(f"src/{self.package_name}/server.py", content)

    def _emit_models(self) -> None:
        content = self._render("models.py.j2")
        self._write(f"src/{self.package_name}/models.py", content)

    def _emit_state(self) -> None:
        content = self._render("state.py.j2")
        self._write(f"src/{self.package_name}/state.py", content)

    def _emit_backend(self) -> None:
        if not self.design.backend:
            return
        backend_type = self.design.backend.backend_type.value
        protocol = self.design.backend.env_vars.get("PROTOCOL", "")

        # Zustand bridge: runs a WebSocket SERVER, not a client
        if protocol == "zustand":
            content = self._render("backend_zustand.py.j2")
            self._write(f"src/{self.package_name}/backend.py", content)
            return

        # Use tool strategies (not env_vars) to determine backend template.
        # env_vars.get("PROTOCOL") == "http" is unreliable — HTTP detectors set it
        # for all web frameworks including FastAPI WebSocket apps, which use
        # protocol_call tools and need the protocol backend, not the HTTP one.
        has_http_tools = any(t.impl.strategy == "http_call" for t in self.design.tools)
        has_protocol_tools = any(t.impl.strategy == "protocol_call" for t in self.design.tools)
        is_http = has_http_tools and not has_protocol_tools

        template_map = {
            "socket": "backend_socket.py.j2",
            "cli": "backend_cli.py.j2",
            "file": "backend_file.py.j2",
            "python-api": "backend_api.py.j2",
            "protocol": "backend_http.py.j2" if is_http else "backend_protocol.py.j2",
        }
        template_name = template_map.get(backend_type)
        if template_name:
            content = self._render(template_name)
            self._write(f"src/{self.package_name}/backend.py", content)

    def _emit_bridge_component(self) -> None:
        """Emit the McpBridge React component for Zustand-based apps."""
        import json as _json

        protocol = self.design.backend.env_vars.get("PROTOCOL", "") if self.design.backend else ""
        if protocol != "zustand":
            return

        # Load store metadata detected during analysis (hook names + import paths)
        meta_str = self.design.backend.env_vars.get("ZUSTAND_STORE_META", "[]") if self.design.backend else "[]"
        try:
            store_imports = _json.loads(meta_str)
        except Exception:
            store_imports = []

        # Fallback: derive store names from tool names if metadata is missing
        if not store_imports:
            seen: set[str] = set()
            for t in self.design.tools:
                if t.impl.strategy == "protocol_call":
                    store_name = t.name.split("_")[0]
                    if store_name not in seen:
                        seen.add(store_name)
                        store_imports.append({
                            "name": store_name,
                            "hook_name": f"use{store_name.capitalize()}",
                            "import_path": f"../../store/use-{store_name}",
                        })

        content = self._render("bridge_zustand.tsx.j2", zustand_store_imports=store_imports)
        self._write("bridge/McpBridge.tsx", content)

    def _emit_tool_modules(self) -> None:
        for module_name, tool_names in self.design.tool_modules.items():
            tools = [t for t in self.design.tools if t.name in tool_names]
            content = self._render("tool_module.py.j2", module_name=module_name, tools=tools)
            self._write(f"src/{self.package_name}/tools/{module_name}.py", content)
        # Tools __init__
        modules = list(self.design.tool_modules.keys())
        init_content = '"""Tool modules."""\n'
        self._write(f"src/{self.package_name}/tools/__init__.py", init_content)

    def _emit_resource_modules(self) -> None:
        if not self.design.resources:
            return
        content = self._render("resource_module.py.j2")
        self._write(f"src/{self.package_name}/resources.py", content)

    def _emit_prompt_modules(self) -> None:
        if not self.design.prompts:
            return
        content = self._render("prompts_module.py.j2")
        self._write(f"src/{self.package_name}/prompts.py", content)

    def _emit_readme(self) -> None:
        content = self._render("readme.md.j2")
        self._write("README.md", content)

    def _emit_agents_md(self) -> None:
        if not self.design.generate_agents_md:
            return
        content = self._render("agents_md.j2")
        self._write("AGENTS.md", content)

    def _emit_mcp_json(self) -> None:
        import json as _json
        server_slug = self.design.server_name.replace("_", "-")
        if self.design.transport == "http":
            server_entry: dict = {"url": f"http://localhost:{self.design.http_port}/mcp"}
        else:
            env: dict[str, str] = {}
            env_prefix = self.design.server_name.upper().replace("-", "_")
            backend = self.design.backend
            if backend:
                is_http_proxy = any(t.impl.strategy == "http_call" for t in self.design.tools)
                if is_http_proxy:
                    detected = f"http://{backend.host}:{backend.port}" if backend.port else ""
                    env[f"{env_prefix}_BASE_URL"] = detected or "http://localhost:PORT"

                auth = backend.auth
                if auth.auth_type in {"api_key", "bearer"} and auth.env_var_token:
                    env[auth.env_var_token] = "<set-me>"
                elif auth.auth_type == "basic":
                    if auth.env_var_username:
                        env[auth.env_var_username] = "<username>"
                    if auth.env_var_password:
                        env[auth.env_var_password] = "<password>"

            server_entry = {
                "command": f"mcp-{server_slug}",
                "args": [],
            }
            if env:
                server_entry["env"] = env
        mcp_config = {"mcpServers": {server_slug: server_entry}}
        self._write("mcp.json", _json.dumps(mcp_config, indent=2) + "\n")

    def _emit_pyproject(self) -> None:
        content = self._render("pyproject.toml.j2")
        self._write("pyproject.toml", content)


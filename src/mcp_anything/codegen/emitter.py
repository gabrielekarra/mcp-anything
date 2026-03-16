"""Orchestrates file generation from a ServerDesign."""

from pathlib import Path

from mcp_anything.codegen.renderer import create_jinja_env
from mcp_anything.models.design import ServerDesign


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
        self._emit_tool_modules()
        self._emit_resource_modules()
        self._emit_prompt_modules()
        return self.generated_files

    def emit_tests(self) -> list[str]:
        """Generate test files."""
        start = len(self.generated_files)
        self._emit_test_conftest()
        self._emit_test_tools()
        self._emit_test_protocol()
        return self.generated_files[start:]

    def emit_docs(self) -> list[str]:
        """Generate documentation."""
        start = len(self.generated_files)
        self._emit_readme()
        self._emit_agents_md()
        return self.generated_files[start:]

    def emit_packaging(self) -> list[str]:
        """Generate packaging files."""
        start = len(self.generated_files)
        self._emit_pyproject()
        if self.design.generate_docker or self.design.transport == "http":
            self._emit_dockerfile()
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
        # Check if this is an HTTP/REST backend (Spring Boot, etc.)
        is_http = False
        if self.design.backend.env_vars.get("PROTOCOL") == "http":
            is_http = True
        # Also check if any tools use http_call strategy
        if any(t.impl.strategy == "http_call" for t in self.design.tools):
            is_http = True

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

    def _emit_test_conftest(self) -> None:
        content = self._render("conftest.py.j2")
        self._write("tests/conftest.py", content)

    def _emit_test_tools(self) -> None:
        content = self._render("test_tools.py.j2")
        self._write("tests/test_tools.py", content)

    def _emit_test_protocol(self) -> None:
        content = self._render("test_protocol.py.j2")
        self._write("tests/test_protocol.py", content)

    def _emit_readme(self) -> None:
        content = self._render("readme.md.j2")
        self._write("README.md", content)

    def _emit_agents_md(self) -> None:
        if not self.design.generate_agents_md:
            return
        content = self._render("agents_md.j2")
        self._write("AGENTS.md", content)

    def _emit_pyproject(self) -> None:
        content = self._render("pyproject.toml.j2")
        self._write("pyproject.toml", content)

    def _emit_dockerfile(self) -> None:
        content = self._render("Dockerfile.j2")
        self._write("Dockerfile", content)

"""Phase 3 (mcp-use target): IMPLEMENT — generate TypeScript MCP server using mcp-use SDK."""

from pathlib import Path

from mcp_anything.codegen.renderer import create_mcp_use_jinja_env
from mcp_anything.pipeline.context import PipelineContext
from mcp_anything.pipeline.phase import Phase


class ImplementMcpUsePhase(Phase):
    @property
    def name(self) -> str:
        return "implement"

    def validate_preconditions(self, ctx: PipelineContext) -> list[str]:
        if not ctx.manifest.design:
            return ["Design phase must complete before implement"]
        return []

    async def execute(self, ctx: PipelineContext) -> None:
        design = ctx.manifest.design
        assert design is not None

        output_dir = Path(ctx.manifest.output_dir)
        env = create_mcp_use_jinja_env()

        ctx.console.print("    Generating TypeScript server (mcp-use)...")

        has_cli_tools = any(
            t.impl.strategy in ("cli_subcommand", "cli_function") for t in design.tools
        )
        has_http_tools = any(t.impl.strategy == "http_call" for t in design.tools)

        binary_default = design.server_name
        if design.backend and design.backend.command:
            binary_default = design.backend.command

        http_base_url = "http://localhost:8080"
        if design.backend and design.backend.port:
            host = design.backend.host or "localhost"
            http_base_url = f"http://{host}:{design.backend.port}"

        auth = design.backend.auth if design.backend else None

        template = env.get_template("server.ts.j2")
        content = template.render(
            design=design,
            has_cli_tools=has_cli_tools,
            has_http_tools=has_http_tools,
            binary_default=binary_default,
            http_base_url=http_base_url,
            auth=auth,
        )

        src_dir = output_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "server.ts").write_text(content)

        generated = ["src/server.ts"]
        ctx.manifest.generated_files.extend(generated)
        ctx.console.print(f"    Generated {len(generated)} TypeScript file(s)")

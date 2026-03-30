"""Phase 5 (mcp-use target): PACKAGE — generate package.json, tsconfig.json, mcp.json."""

import json
from pathlib import Path

from mcp_anything.pipeline.context import PipelineContext
from mcp_anything.pipeline.phase import Phase


class PackageMcpUsePhase(Phase):
    @property
    def name(self) -> str:
        return "package"

    def validate_preconditions(self, ctx: PipelineContext) -> list[str]:
        if not ctx.manifest.design:
            return ["Design phase must complete before packaging"]
        return []

    async def execute(self, ctx: PipelineContext) -> None:
        design = ctx.manifest.design
        assert design is not None

        output_dir = Path(ctx.manifest.output_dir)
        server_slug = design.server_name.replace("_", "-")
        env_prefix = design.server_name.upper().replace("-", "_")

        has_cli_tools = any(
            t.impl.strategy in ("cli_subcommand", "cli_function") for t in design.tools
        )
        has_http_tools = any(t.impl.strategy == "http_call" for t in design.tools)

        ctx.console.print("    Generating TypeScript packaging files...")
        generated: list[str] = []

        # package.json
        package_json = {
            "name": f"mcp-{server_slug}-server",
            "version": "1.0.0",
            "type": "module",
            "scripts": {
                "build": "tsc",
                "dev": "npx @mcp-use/cli dev",
                "start": "node dist/server.js",
                "inspector": "npx @mcp-use/inspector --url http://localhost:3000/mcp",
            },
            "dependencies": {
                "mcp-use": "latest",
                "zod": "^4.0.0",
            },
            "devDependencies": {
                "@mcp-use/cli": "latest",
                "@mcp-use/inspector": "latest",
                "typescript": "^5.0.0",
                "@types/node": "^20.0.0",
            },
        }
        self._write(output_dir, "package.json", json.dumps(package_json, indent=2) + "\n")
        generated.append("package.json")

        # tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "ES2022",
                "module": "ESNext",
                "moduleResolution": "bundler",
                "outDir": "./dist",
                "rootDir": "./src",
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True,
            },
            "include": ["src/**/*"],
        }
        self._write(output_dir, "tsconfig.json", json.dumps(tsconfig, indent=2) + "\n")
        generated.append("tsconfig.json")

        # mcp.json
        mcp_config: dict = {
            "mcpServers": {
                server_slug: {
                    "type": "http",
                    "url": "http://localhost:3000/mcp"
                }
            }
        }
        self._write(output_dir, "mcp.json", json.dumps(mcp_config, indent=2) + "\n")
        generated.append("mcp.json")

        # .env.example
        env_lines: list[str] = []
        if has_cli_tools:
            cmd = (design.backend.command if design.backend and design.backend.command else design.server_name)
            env_lines.append(f"# Path to the {design.server_name} binary (overrides PATH lookup)")
            env_lines.append(f"# {env_prefix}_BINARY={cmd}")
            env_lines.append("")
        if has_http_tools:
            host = (design.backend.host or "localhost") if design.backend else "localhost"
            port = (design.backend.port or 8080) if design.backend else 8080
            env_lines.append(f"# Upstream service base URL")
            env_lines.append(f"{env_prefix}_BASE_URL=http://{host}:{port}")
            env_lines.append("")
        if (
            design.backend
            and design.backend.auth.auth_type in ("api_key", "bearer")
            and design.backend.auth.env_var_token
        ):
            env_lines.append(f"# API token for upstream authentication")
            env_lines.append(f"{design.backend.auth.env_var_token}=<set-me>")
            env_lines.append("")

        if env_lines:
            self._write(output_dir, ".env.example", "\n".join(env_lines))
            generated.append(".env.example")

        # README.md
        readme = self._render_readme(design, server_slug, has_cli_tools, has_http_tools, env_prefix)
        self._write(output_dir, "README.md", readme)
        generated.append("README.md")

        # Only extend manifest with untracked files
        tracked = set(ctx.manifest.generated_files)
        ctx.manifest.generated_files.extend(f for f in generated if f not in tracked)

        ctx.console.print(f"    Generated {len(generated)} packaging files")
        self._print_guidance(ctx, mcp_config)

    def _write(self, output_dir: Path, rel_path: str, content: str) -> None:
        full = output_dir / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)

    def _render_readme(
        self,
        design,
        server_slug: str,
        has_cli_tools: bool,
        has_http_tools: bool,
        env_prefix: str,
    ) -> str:
        lines: list[str] = [
            f"# MCP Server for {design.server_name} (TypeScript / mcp-use)",
            "",
            design.server_description or "",
            "",
            "Generated by [mcp-anything](https://github.com/Type-MCP/mcp-anything).",
            "",
            "## Installation",
            "",
            "```bash",
            "npm install",
            "```",
            "",
            "## Usage",
            "",
            "### Development (with auto-reload and inspector)",
            "",
            "```bash",
            "npm run dev",
            "```",
            "",
            "Inspector: http://localhost:3000/inspector",
            "",
            "### Production",
            "",
            "```bash",
            "npm run build && npm start",
            "```",
            "",
        ]

        config_section: list[str] = []
        if has_cli_tools:
            cmd = (
                design.backend.command
                if design.backend and design.backend.command
                else design.server_name
            )
            config_section += [
                f"### Binary path",
                "",
                f"If `{cmd}` is not on your PATH, set:",
                "",
                "```bash",
                f"export {env_prefix}_BINARY=/usr/local/bin/{cmd}",
                "```",
                "",
            ]
        if has_http_tools:
            host = (design.backend.host or "localhost") if design.backend else "localhost"
            port = (design.backend.port or 8080) if design.backend else 8080
            config_section += [
                f"### Upstream service",
                "",
                "Set the upstream API base URL before starting:",
                "",
                "```bash",
                f"export {env_prefix}_BASE_URL=http://{host}:{port}",
                "```",
                "",
            ]
        if config_section:
            lines += ["## Configuration", ""] + config_section

        lines += [
            "## MCP Client Config",
            "",
            "```json",
            json.dumps(
                {"mcpServers": {server_slug: {"type": "http", "url": "http://localhost:3000/mcp"}}},
                indent=2,
            ),
            "```",
            "",
            "## Available Tools",
            "",
        ]
        for tool in design.tools:
            lines.append(f"### `{tool.name}`")
            lines.append("")
            lines.append(tool.description)
            lines.append("")
            if tool.parameters:
                lines.append("**Parameters:**")
                for param in tool.parameters:
                    opt = "" if param.required else " — optional"
                    lines.append(
                        f"- `{param.name}` ({param.type}){opt}: {param.description}"
                    )
                lines.append("")
        return "\n".join(lines) + "\n"

    def _print_guidance(self, ctx, mcp_config: dict) -> None:
        ctx.console.print("    Generated mcp.json config")
        ctx.console.print()
        ctx.console.print("    [bold]Start the server:[/bold]")
        ctx.console.print("    [cyan]npm install && npm run dev[/cyan]")
        ctx.console.print()
        ctx.console.print(
            "    Built-in inspector: [cyan]http://localhost:3000/inspector[/cyan]"
        )
        ctx.console.print()
        ctx.console.print("    [bold]Add to your MCP client config:[/bold]")
        snippet = json.dumps(mcp_config["mcpServers"], indent=6)
        ctx.console.print(f"    {snippet}")

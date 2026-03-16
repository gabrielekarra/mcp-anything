"""Phase 6: PACKAGE — generate pyproject.toml, verify structure, install, and emit MCP config."""

import json
import subprocess
import sys
from pathlib import Path

from mcp_anything.codegen.emitter import Emitter
from mcp_anything.pipeline.context import PipelineContext
from mcp_anything.pipeline.phase import Phase


class PackagePhase(Phase):
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
        emitter = Emitter(design, output_dir)

        ctx.console.print("    Generating packaging files...")
        generated = emitter.emit_packaging()

        ctx.manifest.generated_files.extend(generated)

        # Verify structure
        errors = self._verify_structure(output_dir, design.server_name.replace("-", "_"))
        if errors:
            for err in errors:
                ctx.console.print(f"    [yellow]Warning:[/yellow] {err}")
        else:
            ctx.console.print("    Package structure verified")

        ctx.console.print(f"    Generated {len(generated)} packaging files")

        # Auto-install now that pyproject.toml exists
        if not ctx.options.no_install:
            install_errors = self._install_dependencies(ctx, output_dir)
            if install_errors:
                for err in install_errors:
                    ctx.console.print(f"    [yellow]Install warning:[/yellow] {err}")

        # Generate MCP config snippet
        self._emit_mcp_config(ctx, output_dir)

    def _verify_structure(self, output_dir: Path, package_name: str) -> list[str]:
        """Verify the generated package has the expected structure."""
        errors: list[str] = []

        expected = [
            "pyproject.toml",
            f"src/{package_name}/__init__.py",
            f"src/{package_name}/server.py",
        ]

        for rel in expected:
            if not (output_dir / rel).exists():
                errors.append(f"Missing expected file: {rel}")

        return errors

    def _install_dependencies(
        self, ctx: PipelineContext, output_dir: Path
    ) -> list[str]:
        """Install target project and generated server dependencies."""
        errors: list[str] = []

        # Install the target project if we have an install hint
        design = ctx.manifest.design
        if design and design.target_install_hint:
            hint = design.target_install_hint
            ctx.console.print(f"    Installing target: {hint}")
            try:
                if "install " in hint:
                    pip_args = hint.split("install ", 1)[1].split()
                else:
                    pip_args = [hint]
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-q"] + pip_args,
                    capture_output=True, text=True, timeout=120,
                )
                if result.returncode != 0:
                    errors.append(f"Target install failed: {result.stderr.strip()[:200]}")
            except subprocess.TimeoutExpired:
                errors.append("Target install timed out")
            except Exception as e:
                errors.append(f"Target install error: {e}")

        # Install the generated server package
        ctx.console.print("    Installing generated server...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "-e", str(output_dir)],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                errors.append(f"Server install failed: {result.stderr.strip()[:200]}")
        except subprocess.TimeoutExpired:
            errors.append("Server install timed out")
        except Exception as e:
            errors.append(f"Server install error: {e}")

        if not errors:
            ctx.console.print("    Dependencies installed successfully")

        return errors

    def _emit_mcp_config(self, ctx: PipelineContext, output_dir: Path) -> None:
        """Generate a .mcp.json snippet for Claude Code integration."""
        design = ctx.manifest.design
        assert design is not None

        server_slug = design.server_name.replace("_", "-")
        package_name = design.server_name.replace("-", "_")

        # Generate MCP config based on transport mode
        if design.transport == "http":
            mcp_config = {
                "mcpServers": {
                    server_slug: {
                        "url": f"http://localhost:{design.http_port}/sse",
                    }
                }
            }
        else:
            mcp_config = {
                "mcpServers": {
                    server_slug: {
                        "command": f"mcp-{server_slug}",
                        "args": [],
                    }
                }
            }

        config_path = output_dir / "mcp.json"
        config_path.write_text(json.dumps(mcp_config, indent=2) + "\n")
        ctx.manifest.generated_files.append("mcp.json")

        ctx.console.print("    Generated mcp.json config")
        ctx.console.print()
        ctx.console.print("    [bold]Add to your Claude Code config (.mcp.json):[/bold]")
        snippet = json.dumps(mcp_config["mcpServers"], indent=6)
        ctx.console.print(f"    {snippet}")

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
        # emit_packaging() regenerates pyproject.toml + mcp.json (already written in implement
        # phase so tests could find them — safe to overwrite with identical content)
        generated = emitter.emit_packaging()

        # Only extend manifest with files not already tracked
        tracked = set(ctx.manifest.generated_files)
        ctx.manifest.generated_files.extend(f for f in generated if f not in tracked)

        # Verify structure
        errors = self._verify_structure(output_dir, f"mcp_{design.server_name.replace('-', '_')}")
        if errors:
            for err in errors:
                ctx.console.print(f"    [yellow]Warning:[/yellow] {err}")
        else:
            ctx.console.print("    Package structure verified")

        ctx.console.print(f"    Generated {len(generated)} packaging files")

        # Auto-install now that pyproject.toml exists
        install_ok = True
        if not ctx.options.no_install:
            install_errors = self._install_dependencies(ctx, output_dir)
            if install_errors:
                install_ok = False
                for err in install_errors:
                    ctx.console.print(f"    [red]Install error:[/red] {err}")
                ctx.console.print(
                    f"    [yellow]pip install failed — the generated server is not installed.[/yellow]\n"
                    f"    [yellow]Use [bold]mcp-anything serve {output_dir}[/bold] to run it without installing,[/yellow]\n"
                    f"    [yellow]or fix the error above and re-run with --resume.[/yellow]"
                )
                # Rewrite stdio mcp.json to use `mcp-anything serve` so the config still works
                if design.transport != "http":
                    self._rewrite_mcp_json_for_serve(ctx, output_dir)

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

    def _rewrite_mcp_json_for_serve(self, ctx: PipelineContext, output_dir: Path) -> None:
        """Overwrite stdio mcp.json to use `mcp-anything serve` when pip install failed."""
        design = ctx.manifest.design
        assert design is not None
        server_slug = design.server_name.replace("_", "-")
        config_path = output_dir / "mcp.json"
        existing = json.loads(config_path.read_text()) if config_path.exists() else {"mcpServers": {}}
        server_entry = dict(existing.get("mcpServers", {}).get(server_slug, {}))
        server_entry["command"] = "mcp-anything"
        server_entry["args"] = ["serve", str(output_dir)]
        server_entry.pop("url", None)
        mcp_config = {
            "mcpServers": {
                server_slug: server_entry,
            }
        }
        config_path.write_text(json.dumps(mcp_config, indent=2) + "\n")

    def _emit_mcp_config(self, ctx: PipelineContext, output_dir: Path) -> None:
        """Print MCP config guidance for local clients and remote connector setups."""
        design = ctx.manifest.design
        assert design is not None

        server_slug = design.server_name.replace("_", "-")

        # File was already written by the emitter in emit_packaging(); just load it for display
        mcp_config = json.loads((output_dir / "mcp.json").read_text())

        ctx.console.print("    Generated mcp.json config")
        if design.enable_server_auth:
            ctx.console.print(
                f"    [yellow]Before starting: export {design.server_auth_env_var}=<secret-token>[/yellow]"
            )
            ctx.console.print(
                "    [yellow]Users enter this token in the browser login form when connecting via Claude.[/yellow]"
            )
        ctx.console.print()
        if design.transport == "http":
            ctx.console.print("    [bold]Use with remote MCP clients:[/bold]")
            ctx.console.print(
                "    Start the server, then expose it with the provider you prefer."
            )
            ctx.console.print(
                "    We recommend [cyan]mcp-use[/cyan] for easy setup, but it is optional:"
            )
            ctx.console.print("    [cyan]https://github.com/mcp-use/mcp-use[/cyan]")
            ctx.console.print(
                "    Add the public connector URL from your hosting or tunneling provider in your MCP client."
            )
            ctx.console.print(f"    Example: [cyan]npx @mcp-use/tunnel {design.http_port}[/cyan]")
            ctx.console.print()
            ctx.console.print("    [bold]Local MCP client config:[/bold]")
        else:
            ctx.console.print("    [bold]Add to your Claude Code config (.mcp.json):[/bold]")
        snippet = json.dumps(mcp_config["mcpServers"], indent=6)
        ctx.console.print(f"    {snippet}")

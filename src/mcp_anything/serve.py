"""Run a generated MCP server directly without installing."""

import json
import subprocess
import sys
from pathlib import Path

from rich.console import Console


def run_server(
    output_dir: Path,
    transport: str | None,
    host: str,
    port: int,
    console: Console,
) -> None:
    """Run a generated MCP server from its output directory."""
    output_dir = output_dir.resolve()

    if not output_dir.exists():
        console.print(f"[red]Error:[/red] Directory not found: {output_dir}")
        sys.exit(1)

    # Find the package name from the src/ directory
    src_dir = output_dir / "src"
    if not src_dir.exists():
        console.print(f"[red]Error:[/red] No src/ directory in {output_dir}")
        sys.exit(1)

    packages = [d.name for d in src_dir.iterdir() if d.is_dir() and (d / "server.py").exists()]
    if not packages:
        console.print("[red]Error:[/red] No server.py found in src/*/")
        sys.exit(1)

    package_name = packages[0]

    # Determine transport from manifest if not overridden
    if transport is None:
        manifest_path = output_dir / "mcp-anything-manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            design = manifest.get("design", {})
            transport = design.get("transport", "stdio")
        else:
            transport = "stdio"

    console.print(f"    Starting [bold]{package_name}[/bold] server ({transport} transport)")

    # Build the command to run
    env_vars = {
        "PYTHONPATH": str(src_dir),
        "MCP_TRANSPORT": transport,
    }
    if transport == "http":
        env_vars["MCP_HOST"] = host
        env_vars["MCP_PORT"] = str(port)
        console.print(f"    Listening on http://{host}:{port}")

    import os

    # If proto_stubs exist, add that directory to PYTHONPATH so any residual
    # bare imports (e.g. from manually-compiled or cached stubs) still resolve.
    proto_stubs_dir = src_dir / package_name / "proto_stubs"
    if proto_stubs_dir.exists():
        env_vars["PYTHONPATH"] = os.pathsep.join([
            str(src_dir),
            str(proto_stubs_dir),
        ])

    run_env = {**os.environ, **env_vars}

    try:
        result = subprocess.run(
            [sys.executable, "-m", f"{package_name}.server"],
            cwd=str(output_dir),
            env=run_env,
        )
        if result.returncode not in (0, -2):  # -2 = SIGINT (Ctrl-C)
            console.print(f"[red]Server exited with code {result.returncode}[/red]")
    except KeyboardInterrupt:
        console.print("\n    Server stopped.")

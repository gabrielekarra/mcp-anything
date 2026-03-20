"""CLI entry point for mcp-anything."""

import argparse
import asyncio
import re
import shutil
import sys
import tempfile
from pathlib import Path

from rich.console import Console

from mcp_anything import __version__
from mcp_anything.config import CLIOptions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mcp-anything",
        description="Auto-generate MCP servers from any scriptable application's source code.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # generate
    gen = subparsers.add_parser("generate", help="Run full 6-phase generation pipeline")
    gen.add_argument("codebase_path", help="Path to source code or URL to an API spec")
    gen.add_argument("-o", "--output-dir", type=Path, help="Output directory")
    gen.add_argument("--name", help="Override server name")
    gen.add_argument(
        "--backend",
        choices=["socket", "cli", "file", "python-api", "protocol"],
        help="Force backend type (default: auto-detect)",
    )
    gen.add_argument("--phases", help="Comma-separated phases to run (e.g. analyze,design)")
    gen.add_argument("--resume", action="store_true", help="Resume from saved manifest")
    gen.add_argument("--no-llm", action="store_true", help="Disable Claude API analysis")
    gen.add_argument("--no-install", action="store_true", help="Skip auto-installing dependencies")
    gen.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="MCP transport mode (default: stdio, use http for remote/enterprise)",
    )
    gen.add_argument(
        "--server-auth",
        action="store_true",
        default=False,
        help="Protect the HTTP server with bearer token auth (reads MCP_SERVER_TOKEN env var)",
    )
    gen.add_argument(
        "--include",
        action="append",
        default=None,
        help="Glob pattern to include capabilities (repeatable, e.g. --include '/api/v2/*')",
    )
    gen.add_argument(
        "--exclude",
        action="append",
        default=None,
        help="Glob pattern to exclude capabilities (repeatable, e.g. --exclude '/internal/*')",
    )
    gen.add_argument(
        "--scope-file",
        type=Path,
        default=None,
        help="Path to a scope.yaml file for capability curation",
    )
    gen.add_argument(
        "--review",
        action="store_true",
        default=False,
        help="Pause after analysis to write scope.yaml for manual editing, then --resume to continue",
    )
    gen.add_argument("-v", "--verbose", action="store_true")

    # analyze
    ana = subparsers.add_parser("analyze", help="Run analysis phase only")
    ana.add_argument("codebase_path", help="Path to source code or URL to an API spec")
    ana.add_argument("--no-llm", action="store_true")
    ana.add_argument("-v", "--verbose", action="store_true")

    # design
    des = subparsers.add_parser("design", help="Run analysis + design phases")
    des.add_argument("codebase_path", help="Path to source code or URL to an API spec")
    des.add_argument("--no-llm", action="store_true")
    des.add_argument("-v", "--verbose", action="store_true")

    # status
    sta = subparsers.add_parser("status", help="Show manifest state for an output directory")
    sta.add_argument("output_dir", type=Path)

    # serve
    srv = subparsers.add_parser("serve", help="Run a generated MCP server directly without installing")
    srv.add_argument("output_dir", type=Path, help="Path to generated server directory")
    srv.add_argument("--transport", choices=["stdio", "http"], default=None, help="Override transport mode")
    srv.add_argument("--host", default="0.0.0.0", help="HTTP host (default: 0.0.0.0)")
    srv.add_argument("--port", type=int, default=8000, help="HTTP port (default: 8000)")

    return parser


def parse_options(args: argparse.Namespace) -> CLIOptions:
    """Convert parsed args to CLIOptions."""
    codebase_path = args.codebase_path
    if isinstance(codebase_path, str):
        codebase_path = Path(codebase_path)
    return CLIOptions(
        codebase_path=codebase_path,
        output_dir=getattr(args, "output_dir", None),
        name=getattr(args, "name", None),
        backend=getattr(args, "backend", None),
        phases=args.phases.split(",") if getattr(args, "phases", None) else None,
        resume=getattr(args, "resume", False),
        no_llm=getattr(args, "no_llm", False),
        no_install=getattr(args, "no_install", False),
        verbose=getattr(args, "verbose", False),
        transport=getattr(args, "transport", "stdio") or "stdio",
        server_auth=getattr(args, "server_auth", False),
        include=getattr(args, "include", None),
        exclude=getattr(args, "exclude", None),
        scope_file=getattr(args, "scope_file", None),
        review=getattr(args, "review", False),
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    console = Console()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "status":
        from mcp_anything.pipeline.engine import show_status

        show_status(args.output_dir, console)
        return

    if args.command == "serve":
        from mcp_anything.serve import run_server

        run_server(args.output_dir, args.transport, args.host, args.port, console)
        return

    # Handle URL-based generation and local spec files
    source_url = None
    if hasattr(args, "codebase_path") and isinstance(args.codebase_path, str):
        from mcp_anything.url_fetcher import is_url

        if is_url(args.codebase_path):
            source_url = args.codebase_path
            from mcp_anything.url_fetcher import fetch_url

            try:
                temp_dir, derived_name = fetch_url(source_url, console)
            except RuntimeError as exc:
                console.print(f"[red]Error:[/red] {exc}")
                sys.exit(1)
            args.codebase_path = temp_dir
            if not getattr(args, "name", None):
                args.name = derived_name
        else:
            spec_path = Path(args.codebase_path)
            if spec_path.is_file():
                # Single spec file — wrap in a temp dir so the pipeline sees a directory
                _spec_exts = {".json", ".yaml", ".yml", ".proto", ".graphql", ".gql"}
                if spec_path.suffix.lower() not in _spec_exts:
                    console.print(
                        f"[red]Error:[/red] {spec_path} is a file but not a recognised spec "
                        f"({', '.join(sorted(_spec_exts))}). Pass a directory instead."
                    )
                    sys.exit(1)
                temp_dir = Path(tempfile.mkdtemp(prefix="mcp_spec_"))
                shutil.copy(spec_path, temp_dir / spec_path.name)
                args.codebase_path = temp_dir
                if not getattr(args, "name", None):
                    stem = re.sub(r"[^a-zA-Z0-9]+", "_", spec_path.stem).strip("_").lower()
                    args.name = stem or "api"
            else:
                args.codebase_path = Path(args.codebase_path)

    options = parse_options(args)
    if source_url:
        options.source_url = source_url

    if not options.codebase_path.exists():
        console.print(f"[red]Error:[/red] Codebase path does not exist: {options.codebase_path}")
        sys.exit(1)

    # Determine which phases to run
    if args.command == "analyze":
        options.phases = ["analyze"]
    elif args.command == "design":
        options.phases = ["analyze", "design"]

    from mcp_anything.pipeline.engine import PipelineEngine

    engine = PipelineEngine(options, console)
    asyncio.run(engine.run())

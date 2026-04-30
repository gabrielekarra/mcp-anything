"""CLI entry point for mcp-anything."""

import argparse
import asyncio
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional

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
    gen.add_argument("codebase_path", nargs="?", default=None, help="Path to source code or URL to an API spec")
    gen.add_argument("-o", "--output-dir", type=Path, help="Output directory")
    gen.add_argument("--name", help="Override server name")
    gen.add_argument(
        "--backend",
        choices=["socket", "cli", "file", "python-api", "protocol"],
        help="Force backend type (default: auto-detect)",
    )
    gen.add_argument("--phases", help="Comma-separated phases to run (e.g. analyze,design)")
    gen.add_argument("--resume", action="store_true", help="Resume from saved manifest")
    gen.add_argument(
        "--description",
        action="store_true",
        default=False,
        help="Apply description overrides from descriptions.yaml and regenerate",
    )
    gen.add_argument("--no-llm", action="store_true", help="Disable Claude API analysis")
    gen.add_argument("--no-install", action="store_true", help="Skip auto-installing dependencies")
    gen.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="MCP transport mode (default: stdio, use http for remote/enterprise)",
    )
    gen.add_argument(
        "--target",
        choices=["fastmcp", "mcp-use"],
        default="fastmcp",
        help="Target MCP SDK. 'fastmcp' (default) generates Python/FastMCP. 'mcp-use' generates TypeScript using the mcp-use SDK.",
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

    # model — Phase 1 only: domain brief → domain_model.json
    mod = subparsers.add_parser(
        "model",
        help="[domain] Phase 1: collect domain brief + data source → domain_model.json",
    )
    mod.add_argument("--brief", dest="brief_file", type=Path, help="Path to domain brief YAML/JSON")
    mod.add_argument("--data-source", dest="data_source", type=Path, help="Path to OpenAPI spec, .proto, DDL, or SDK")
    mod.add_argument("--name", help="Server name")
    mod.add_argument("-o", "--output-dir", type=Path)
    mod.add_argument("--review", action="store_true", help="Pause for domain model sign-off")
    mod.add_argument("--resume", action="store_true", help="Continue from saved domain_model.json")
    mod.add_argument("--auto-approve", dest="auto_approve", action="store_true", help="Skip sign-off gate")
    mod.add_argument("--no-llm", action="store_true")
    mod.add_argument("-v", "--verbose", action="store_true")

    # build — full domain pipeline: Phases 1-5
    bld = subparsers.add_parser(
        "build",
        help="[domain] Full 5-phase domain pipeline: brief → domain model → tool design → server",
    )
    bld.add_argument("--brief", dest="brief_file", type=Path, required=True, help="Path to domain brief YAML/JSON")
    bld.add_argument("--data-source", dest="data_source", type=Path, help="Path to API spec, .proto, DDL, or SDK")
    bld.add_argument("--name", help="Server name (default: from brief)")
    bld.add_argument("-o", "--output-dir", type=Path)
    bld.add_argument(
        "--target",
        choices=["fastmcp", "mcp-use"],
        default="fastmcp",
        help="Output backend: fastmcp (Python) or mcp-use (TypeScript)",
    )
    bld.add_argument("--resume", action="store_true")
    bld.add_argument("--auto-approve", dest="auto_approve", action="store_true")
    bld.add_argument("--run-eval", dest="run_eval", action="store_true", help="Run live eval after generation")
    bld.add_argument("--eval-threshold", dest="eval_threshold", type=float, default=0.80)
    bld.add_argument("--ci", action="store_true", help="Hard-fail on coverage below threshold or parity divergence")
    bld.add_argument("--no-llm", action="store_true")
    bld.add_argument("-v", "--verbose", action="store_true")

    # validate — run conformance checks on an existing generated server
    val = subparsers.add_parser(
        "validate",
        help="[domain] Run CONTRACT.md conformance checks on an existing generated server",
    )
    val.add_argument("output_dir", type=Path, help="Path to generated server directory")
    val.add_argument("--run-eval", dest="run_eval", action="store_true", help="Run live eval (requires running server)")
    val.add_argument("--eval-threshold", dest="eval_threshold", type=float, default=0.80)
    val.add_argument("--ci", action="store_true")
    val.add_argument("-v", "--verbose", action="store_true")

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
        description=getattr(args, "description", False),
        no_llm=getattr(args, "no_llm", False),
        no_install=getattr(args, "no_install", False),
        verbose=getattr(args, "verbose", False),
        transport=getattr(args, "transport", "stdio") or "stdio",
        target=getattr(args, "target", "fastmcp"),
        include=getattr(args, "include", None),
        exclude=getattr(args, "exclude", None),
        scope_file=getattr(args, "scope_file", None),
        review=getattr(args, "review", False),
    )


def _run_domain_command(
    args: argparse.Namespace,
    console: Console,
    phases: Optional[list[str]],
) -> None:
    """Handle 'model' and 'build' subcommands (domain pipeline)."""
    brief_file = getattr(args, "brief_file", None)
    data_source = getattr(args, "data_source", None)
    name = getattr(args, "name", None)

    # Derive server name from brief file stem if not provided
    if not name and brief_file:
        name = Path(brief_file).stem.replace("_", "-").replace(" ", "-")
    if not name:
        name = "mcp-server"

    # Use a synthetic codebase_path (domain pipeline doesn't need a real codebase)
    codebase_path = data_source or Path(".")

    output_dir = getattr(args, "output_dir", None) or Path(f"./mcp-{name}-server")

    options = CLIOptions(
        codebase_path=Path(codebase_path),
        output_dir=Path(output_dir),
        name=name,
        phases=phases,
        resume=getattr(args, "resume", False),
        no_llm=getattr(args, "no_llm", False),
        verbose=getattr(args, "verbose", False),
        target=getattr(args, "target", "fastmcp"),
        review=getattr(args, "review", False),
        brief_file=Path(brief_file) if brief_file else None,
        auto_approve=getattr(args, "auto_approve", False),
        run_eval=getattr(args, "run_eval", False),
        eval_threshold=getattr(args, "eval_threshold", 0.80),
        ci=getattr(args, "ci", False),
    )

    from mcp_anything.pipeline.engine import PipelineEngine

    engine = PipelineEngine(options, console)
    asyncio.run(engine.run_domain())


def _run_validate_command(args: argparse.Namespace, console: Console) -> None:
    """Handle 'validate' subcommand — run CONTRACT checks on an existing server."""
    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        console.print(f"[red]Error:[/red] Output directory not found: {output_dir}")
        sys.exit(1)

    manifest_path = output_dir / "mcp-anything-manifest.json"
    if not manifest_path.exists():
        console.print(f"[red]Error:[/red] No manifest found in {output_dir}")
        sys.exit(1)

    from mcp_anything.models.manifest import GenerationManifest
    from mcp_anything.models.design import ServerDesign
    from mcp_anything.emit.base import EmitPhase
    from mcp_anything.conformance.reporter import ConformanceReporter
    from mcp_anything.models.validation import ConformanceReport

    manifest = GenerationManifest.load(manifest_path)
    design = (
        ServerDesign.model_validate(manifest.tool_spec)
        if manifest.tool_spec
        else manifest.design
    )

    if not design:
        console.print("[red]Error:[/red] No tool spec or design found in manifest.")
        sys.exit(1)

    # Structural contract checks (no running server needed)
    from mcp_anything.emit.base import EmitPhase as _EmitPhase

    class _TmpPhase(_EmitPhase):
        name = "_validate"
        backend_target = "fastmcp"
        def execute(self, ctx): pass

    phase = _TmpPhase()
    checks = phase.validate_contract(design, output_dir)

    contracts_ok = all(c.passed for c in checks)
    run_eval = getattr(args, "run_eval", False)
    report = ConformanceReport(
        server_name=design.server_name,
        backend_target=manifest.extra_data.get("backend_target", "fastmcp") if manifest.extra_data else "fastmcp",
        contract_checks=checks,
        threshold=getattr(args, "eval_threshold", 0.80),
        eval_run=run_eval,
        passed=contracts_ok if not run_eval else False,  # live eval pass/fail set below
    )

    output = ConformanceReporter.to_ci_output(report)
    console.print(output)

    if getattr(args, "ci", False):
        failed = [c for c in checks if not c.passed]
        if failed:
            sys.exit(1)


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

    if args.command == "model":
        _run_domain_command(args, console, phases=["domain_modeling"])
        return

    if args.command == "build":
        _run_domain_command(args, console, phases=None)  # all DOMAIN_PHASES
        return

    if args.command == "validate":
        _run_validate_command(args, console)
        return

    if args.command == "serve":
        from mcp_anything.serve import run_server

        run_server(args.output_dir, args.transport, args.host, args.port, console)
        return

    # --description without codebase_path: infer from current directory manifest
    if getattr(args, "description", False) and args.codebase_path is None:
        output_dir = getattr(args, "output_dir", None) or Path(".")
        manifest_path = output_dir / "mcp-anything-manifest.json"
        if not manifest_path.exists():
            console.print(
                "[red]Error:[/red] No manifest found in current directory. "
                "Run from the generated server directory or pass --output-dir."
            )
            sys.exit(1)
        from mcp_anything.models.manifest import GenerationManifest

        manifest = GenerationManifest.load(manifest_path)
        args.codebase_path = Path(manifest.codebase_path)
        if not getattr(args, "output_dir", None):
            args.output_dir = output_dir.resolve()
        if not getattr(args, "name", None):
            args.name = manifest.server_name

    # Require codebase_path for non-description commands
    if getattr(args, "codebase_path", None) is None:
        console.print("[red]Error:[/red] codebase_path is required")
        sys.exit(1)

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

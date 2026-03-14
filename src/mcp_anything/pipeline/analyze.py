"""Phase 1: ANALYZE — scan codebase and detect IPC mechanisms."""

from mcp_anything.analysis.ast_analyzer import (
    analyze_python_file,
    ast_results_to_capabilities,
)
from mcp_anything.analysis.detectors import ALL_DETECTORS
from mcp_anything.analysis.flask_fastapi_analyzer import (
    analyze_flask_fastapi_file,
    flask_fastapi_results_to_capabilities,
)
from mcp_anything.analysis.java_analyzer import (
    analyze_java_file,
    java_results_to_capabilities,
)
from mcp_anything.analysis.llm_analyzer import llm_analyze
from mcp_anything.analysis.scanner import scan_codebase
from mcp_anything.models.analysis import (
    AnalysisResult,
    Capability,
    IPCType,
    Language,
    ParameterSpec,
)
from mcp_anything.pipeline.context import PipelineContext
from mcp_anything.pipeline.phase import Phase


class AnalyzePhase(Phase):
    @property
    def name(self) -> str:
        return "analyze"

    async def execute(self, ctx: PipelineContext) -> None:
        root = ctx.codebase_path
        console = ctx.console

        # 1. Scan filesystem
        console.print("    Scanning codebase...")
        files = scan_codebase(root)
        console.print(f"    Found {len(files)} source files")

        if not files:
            raise RuntimeError(f"No source files found in {root}")

        # 2. Run detectors
        console.print("    Running IPC detectors...")
        all_mechanisms = []
        for detector_cls in ALL_DETECTORS:
            detector = detector_cls()
            mechanisms = detector.detect(root, files)
            if mechanisms:
                for m in mechanisms:
                    console.print(
                        f"      {detector.name}: {m.ipc_type.value} "
                        f"(confidence: {m.confidence:.2f}, {len(m.evidence)} signals)"
                    )
                all_mechanisms.extend(mechanisms)

        # 3. AST analysis (always runs for Python files)
        console.print("    Running AST analysis...")
        ast_results = {}
        for fi in files:
            if fi.language == Language.PYTHON:
                result = analyze_python_file(root, fi)
                if result:
                    ast_results[fi.path] = result
                    # Mark files with public API surfaces
                    if result.functions or result.classes:
                        fi.is_api_surface = True

        func_count = sum(len(r.functions) for r in ast_results.values())
        class_count = sum(len(r.classes) for r in ast_results.values())
        cli_count = sum(len(r.cli_commands) for r in ast_results.values())
        subcmd_count = sum(len(r.subcommands) for r in ast_results.values())
        console.print(
            f"    AST: {func_count} functions, {class_count} classes, "
            f"{cli_count} CLI commands, {subcmd_count} subcommands"
        )

        # 3a. Java/Spring Boot analysis
        java_results = {}
        for fi in files:
            if fi.language == Language.JAVA:
                jresult = analyze_java_file(root, fi)
                if jresult and (jresult.endpoints or jresult.has_spring_boot):
                    java_results[fi.path] = jresult
                    if jresult.endpoints:
                        fi.is_api_surface = True

        if java_results:
            endpoint_count = sum(len(r.endpoints) for r in java_results.values())
            controller_count = sum(len(r.controllers) for r in java_results.values())
            console.print(
                f"    Java: {endpoint_count} REST endpoints, "
                f"{controller_count} controllers"
            )

        # 3b. Flask/FastAPI analysis
        flask_fastapi_results = {}
        for fi in files:
            if fi.language == Language.PYTHON:
                ff_result = analyze_flask_fastapi_file(root, fi)
                if ff_result and ff_result.routes:
                    flask_fastapi_results[fi.path] = ff_result
                    fi.is_api_surface = True

        if flask_fastapi_results:
            route_count = sum(len(r.routes) for r in flask_fastapi_results.values())
            frameworks = {r.framework for r in flask_fastapi_results.values()}
            console.print(
                f"    {'/'.join(frameworks).title()}: {route_count} HTTP routes"
            )

        # 3c. For non-Python or thin codebases, try --help parsing
        ast_cap_count = sum(
            len(r.functions) + len(r.cli_commands) for r in ast_results.values()
        )
        if ast_cap_count < 3:
            from mcp_anything.analysis.help_parser import run_help_command, parse_help_text
            help_text = run_help_command(root)
            if help_text:
                console.print("    Parsing --help output...")
                help_caps = parse_help_text(help_text, ctx.manifest.server_name)
                if help_caps:
                    console.print(f"    Found {len(help_caps)} commands from --help")
                    # Store for later merging in _ast_fallback
                    ctx.manifest.extra_data = ctx.manifest.extra_data or {}
                    ctx.manifest.extra_data["help_capabilities"] = [
                        {"name": c.name, "description": c.description, "category": c.category}
                        for c in help_caps
                    ]

        # 4. LLM analysis (if enabled)
        llm_result = None
        if not ctx.options.no_llm:
            console.print("    Running LLM analysis...")
            llm_result = await llm_analyze(
                ctx.manifest.server_name, root, files, all_mechanisms
            )
            if llm_result:
                console.print(f"    LLM found {len(llm_result.capabilities)} capabilities")
            else:
                console.print("    [dim]LLM analysis unavailable, using static fallback[/dim]")

        # 5. Build result
        if llm_result:
            result = llm_result
        else:
            result = self._ast_fallback(
                ctx.manifest.server_name, files, all_mechanisms, ast_results,
                java_results, flask_fastapi_results,
            )

        # Override backend if forced
        if ctx.options.backend:
            backend_map = {
                "socket": IPCType.SOCKET,
                "cli": IPCType.CLI,
                "file": IPCType.FILE,
                "python-api": IPCType.PYTHON_API,
                "protocol": IPCType.PROTOCOL,
            }
            result.primary_ipc = backend_map.get(ctx.options.backend, result.primary_ipc)

        ctx.manifest.analysis = result

    def _ast_fallback(
        self, app_name: str, files: list, ipc_mechanisms: list, ast_results: dict,
        java_results: dict | None = None,
        flask_fastapi_results: dict | None = None,
    ) -> AnalysisResult:
        """Generate AnalysisResult from AST/Java/Flask/FastAPI analysis without LLM."""
        primary_ipc = None
        if ipc_mechanisms:
            primary_ipc = max(ipc_mechanisms, key=lambda m: m.confidence).ipc_type

        languages = list({f.language for f in files if f.language != Language.OTHER})

        # When Flask/FastAPI routes are found, exclude those files from AST
        # to avoid duplicate generic function tools alongside HTTP route tools
        if flask_fastapi_results:
            filtered_ast = {k: v for k, v in ast_results.items() if k not in flask_fastapi_results}
        else:
            filtered_ast = ast_results

        # Generate capabilities from AST results
        capabilities = ast_results_to_capabilities(filtered_ast, primary_ipc)

        # Add Java/Spring Boot capabilities
        if java_results:
            java_caps = java_results_to_capabilities(java_results)
            capabilities.extend(java_caps)

        # Add Flask/FastAPI capabilities
        if flask_fastapi_results:
            ff_caps = flask_fastapi_results_to_capabilities(flask_fastapi_results)
            capabilities.extend(ff_caps)

        # If AST found nothing, fall back to generic capability
        if not capabilities:
            capabilities.append(
                Capability(
                    name=f"execute_{app_name.replace('-', '_')}",
                    description=f"Execute {app_name} command",
                    category="execution",
                    parameters=[
                        ParameterSpec(name="command", type="string", description="Command to execute"),
                        ParameterSpec(
                            name="args",
                            type="string",
                            description="Command arguments",
                            required=False,
                        ),
                    ],
                    ipc_type=primary_ipc,
                )
            )

        # Build description from what we found
        parts = []
        if any(r.has_argparse or r.has_click or r.has_typer for r in ast_results.values()):
            parts.append("CLI application")
        if len(capabilities) > 1:
            parts.append(f"with {len(capabilities)} capabilities")
        description = f"MCP server for {app_name}" + (f" ({', '.join(parts)})" if parts else "")

        return AnalysisResult(
            app_name=app_name,
            app_description=description,
            languages=languages,
            files=files,
            ipc_mechanisms=ipc_mechanisms,
            capabilities=capabilities,
            primary_ipc=primary_ipc,
            entry_points=[f.path for f in files if f.is_entry_point],
        )

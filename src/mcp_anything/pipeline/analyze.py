"""Phase 1: ANALYZE — scan codebase and detect IPC mechanisms."""

from mcp_anything.analysis.ast_analyzer import (
    analyze_python_file,
    ast_results_to_capabilities,
)
from mcp_anything.analysis.detectors import ALL_DETECTORS
from mcp_anything.analysis.django_analyzer import (
    analyze_django_file,
    django_results_to_capabilities,
)
from mcp_anything.analysis.express_analyzer import (
    analyze_express_file,
    build_router_mount_map,
    express_results_to_capabilities,
)
from mcp_anything.analysis.flask_fastapi_analyzer import (
    analyze_flask_fastapi_file,
    flask_fastapi_results_to_capabilities,
)
from mcp_anything.analysis.go_analyzer import (
    analyze_go_file,
    go_results_to_capabilities,
)
from mcp_anything.analysis.graphql_analyzer import (
    analyze_graphql_file,
    graphql_results_to_capabilities,
)
from mcp_anything.analysis.grpc_analyzer import (
    analyze_proto_file,
    grpc_results_to_capabilities,
)
from mcp_anything.analysis.java_analyzer import (
    analyze_java_file,
    java_results_to_capabilities,
)
from mcp_anything.analysis.openapi_analyzer import (
    find_openapi_specs,
    openapi_to_capabilities,
    parse_openapi_spec,
)
from mcp_anything.analysis.rails_analyzer import (
    analyze_rails_file,
    analyze_rails_routes,
    rails_results_to_capabilities,
)
from mcp_anything.analysis.rust_web_analyzer import (
    analyze_rust_web_file,
    rust_web_results_to_capabilities,
)
from mcp_anything.analysis.websocket_analyzer import (
    analyze_websocket_file,
    websocket_results_to_capabilities,
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

        # Check for OpenAPI specs even if no source files
        spec_files = find_openapi_specs(root)

        # Check for help text files (e.g. ffmpeg help output captured to .txt)
        from mcp_anything.analysis.help_parser import find_help_files, parse_help_text as _parse_help
        help_text_files = find_help_files(root) if not files else []

        if not files and not spec_files and not help_text_files:
            raise RuntimeError(f"No source files or API specs found in {root}")

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

        # 3a. Java/Kotlin/Spring analysis
        java_results = {}
        for fi in files:
            if fi.language in (Language.JAVA, Language.KOTLIN):
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

        # 3c. OpenAPI/Swagger spec analysis
        openapi_capabilities = []
        for spec_path in spec_files:
            spec = parse_openapi_spec(spec_path)
            if spec:
                rel_path = str(spec_path.relative_to(root.resolve()))
                caps = openapi_to_capabilities(spec, rel_path)
                openapi_capabilities.extend(caps)
                console.print(
                    f"    OpenAPI: {len(caps)} endpoints from {rel_path}"
                )

        # 3d. For non-Python or thin codebases, try --help parsing
        help_capabilities: list[Capability] = []
        ast_cap_count = sum(
            len(r.functions) + len(r.cli_commands) for r in ast_results.values()
        )

        # First: parse any .txt help files found in the directory
        if help_text_files:
            for htf in help_text_files:
                console.print(f"    Parsing help file: {htf.name}")
                content = htf.read_text(errors="replace")
                help_caps = _parse_help(content, ctx.manifest.server_name)
                if help_caps:
                    console.print(f"    Found {len(help_caps)} capabilities from {htf.name}")
                    help_capabilities.extend(help_caps)

        # Then: try running --help for non-Python/thin codebases
        if ast_cap_count < 3 and not help_capabilities:
            from mcp_anything.analysis.help_parser import run_help_command, parse_help_text
            help_text = run_help_command(root)
            if help_text:
                console.print("    Parsing --help output...")
                help_caps = parse_help_text(help_text, ctx.manifest.server_name)
                if help_caps:
                    console.print(f"    Found {len(help_caps)} commands from --help")
                    help_capabilities.extend(help_caps)

        if help_capabilities:
            ctx.manifest.extra_data = ctx.manifest.extra_data or {}
            ctx.manifest.extra_data["help_capabilities"] = [
                {"name": c.name, "description": c.description, "category": c.category,
                 "parameters": [{"name": p.name, "type": p.type, "description": p.description,
                                 "required": p.required} for p in (c.parameters or [])]}
                for c in help_capabilities
            ]

        # 3e. Express.js analysis
        # Build cross-file router mount map first
        js_ts_files = [fi for fi in files if fi.language in (Language.JAVASCRIPT, Language.TYPESCRIPT)]
        express_mount_map = build_router_mount_map(root, js_ts_files) if js_ts_files else {}

        express_results = {}
        for fi in js_ts_files:
            expr_result = analyze_express_file(root, fi, mount_map=express_mount_map)
            if expr_result and expr_result.routes:
                express_results[fi.path] = expr_result
                fi.is_api_surface = True

        if express_results:
            route_count = sum(len(r.routes) for r in express_results.values())
            console.print(f"    Express.js: {route_count} HTTP routes")

        # 3f. Django REST Framework analysis
        django_results = {}
        for fi in files:
            if fi.language == Language.PYTHON:
                dj_result = analyze_django_file(root, fi)
                if dj_result and dj_result.endpoints:
                    django_results[fi.path] = dj_result
                    fi.is_api_surface = True

        if django_results:
            endpoint_count = sum(len(r.endpoints) for r in django_results.values())
            viewset_count = sum(len(r.viewsets) for r in django_results.values())
            console.print(
                f"    Django REST Framework: {endpoint_count} endpoints, "
                f"{viewset_count} ViewSets"
            )

        # 3g. Go web framework analysis
        go_results = {}
        for fi in files:
            if fi.language == Language.GO:
                go_result = analyze_go_file(root, fi)
                if go_result and go_result.routes:
                    go_results[fi.path] = go_result
                    fi.is_api_surface = True

        if go_results:
            route_count = sum(len(r.routes) for r in go_results.values())
            frameworks = {r.framework for r in go_results.values() if r.framework}
            fw_label = "/".join(frameworks).title() if frameworks else "Go"
            console.print(f"    {fw_label}: {route_count} HTTP routes")

        # 3h. Ruby on Rails analysis
        rails_results = {}
        # First try routes.rb for the full picture
        rails_route_result = analyze_rails_routes(root)
        if rails_route_result:
            rails_results["config/routes.rb"] = rails_route_result
        # Also scan individual controller files
        for fi in files:
            if fi.language == Language.RUBY:
                rails_result = analyze_rails_file(root, fi)
                if rails_result and rails_result.routes:
                    rails_results[fi.path] = rails_result
                    fi.is_api_surface = True

        if rails_results:
            route_count = sum(len(r.routes) for r in rails_results.values())
            controller_count = sum(len(r.controllers) for r in rails_results.values())
            console.print(
                f"    Rails: {route_count} routes, {controller_count} controllers"
            )

        # 3i. Rust web framework analysis
        rust_web_results = {}
        for fi in files:
            if fi.language == Language.RUST:
                rust_result = analyze_rust_web_file(root, fi)
                if rust_result and rust_result.routes:
                    rust_web_results[fi.path] = rust_result
                    fi.is_api_surface = True

        if rust_web_results:
            route_count = sum(len(r.routes) for r in rust_web_results.values())
            frameworks = {r.framework for r in rust_web_results.values() if r.framework}
            fw_label = "/".join(frameworks).title() if frameworks else "Rust"
            console.print(f"    {fw_label}: {route_count} HTTP routes")

        # 3j. GraphQL analysis
        graphql_results = {}
        for fi in files:
            if fi.language == Language.GRAPHQL:
                gql_result = analyze_graphql_file(root, fi)
                if gql_result and (gql_result.queries or gql_result.mutations):
                    graphql_results[fi.path] = gql_result
                    fi.is_api_surface = True

        if graphql_results:
            query_count = sum(len(r.queries) for r in graphql_results.values())
            mutation_count = sum(len(r.mutations) for r in graphql_results.values())
            console.print(
                f"    GraphQL: {query_count} queries, {mutation_count} mutations"
            )

        # 3k. gRPC/Protobuf analysis
        grpc_results = {}
        for fi in files:
            if fi.language == Language.PROTOBUF:
                proto_result = analyze_proto_file(root, fi)
                if proto_result and proto_result.services:
                    grpc_results[fi.path] = proto_result
                    fi.is_api_surface = True

        if grpc_results:
            service_count = sum(len(r.services) for r in grpc_results.values())
            method_count = sum(
                len(m) for r in grpc_results.values()
                for s in r.services for m in [s.methods]
            )
            console.print(
                f"    gRPC: {service_count} services, {method_count} RPC methods"
            )

        # 3l. WebSocket analysis
        websocket_results = {}
        for fi in files:
            if fi.language in (
                Language.PYTHON, Language.JAVASCRIPT, Language.TYPESCRIPT,
            ):
                ws_result = analyze_websocket_file(root, fi)
                if ws_result and ws_result.endpoints:
                    websocket_results[fi.path] = ws_result
                    fi.is_api_surface = True

        if websocket_results:
            ws_count = sum(len(r.endpoints) for r in websocket_results.values())
            console.print(f"    WebSocket: {ws_count} endpoints")

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
                java_results, flask_fastapi_results, openapi_capabilities,
                express_results, django_results, go_results,
                rails_results, rust_web_results,
                graphql_results, grpc_results, websocket_results,
                help_capabilities,
                root=root,
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
        openapi_capabilities: list | None = None,
        express_results: dict | None = None,
        django_results: dict | None = None,
        go_results: dict | None = None,
        rails_results: dict | None = None,
        rust_web_results: dict | None = None,
        graphql_results: dict | None = None,
        grpc_results: dict | None = None,
        websocket_results: dict | None = None,
        help_capabilities: list | None = None,
        root: Path | None = None,
    ) -> AnalysisResult:
        """Generate AnalysisResult from all analyzers without LLM."""
        primary_ipc = None
        if ipc_mechanisms:
            primary_ipc = max(ipc_mechanisms, key=lambda m: m.confidence).ipc_type
        elif help_capabilities:
            primary_ipc = IPCType.CLI

        languages = list({f.language for f in files if f.language != Language.OTHER})

        # When framework routes are found, exclude those files from generic AST
        # to avoid duplicate generic function tools alongside HTTP route tools
        framework_files: set[str] = set()
        if flask_fastapi_results:
            framework_files.update(flask_fastapi_results.keys())
        if django_results:
            framework_files.update(django_results.keys())

        if framework_files:
            filtered_ast = {k: v for k, v in ast_results.items() if k not in framework_files}
        else:
            filtered_ast = ast_results

        # Generate capabilities from AST results
        capabilities = ast_results_to_capabilities(filtered_ast, primary_ipc)

        # Add Java/Spring Boot capabilities
        if java_results:
            java_caps = java_results_to_capabilities(java_results, root=root)
            capabilities.extend(java_caps)

        # Add Flask/FastAPI capabilities
        if flask_fastapi_results:
            ff_caps = flask_fastapi_results_to_capabilities(flask_fastapi_results)
            capabilities.extend(ff_caps)

        # Add Express.js capabilities
        if express_results:
            expr_caps = express_results_to_capabilities(express_results)
            capabilities.extend(expr_caps)

        # Add Django REST Framework capabilities
        if django_results:
            dj_caps = django_results_to_capabilities(django_results)
            capabilities.extend(dj_caps)

        # Add Go web framework capabilities
        if go_results:
            go_caps = go_results_to_capabilities(go_results)
            capabilities.extend(go_caps)

        # Add Rails capabilities
        if rails_results:
            rails_caps = rails_results_to_capabilities(rails_results)
            capabilities.extend(rails_caps)

        # Add Rust web framework capabilities
        if rust_web_results:
            rust_caps = rust_web_results_to_capabilities(rust_web_results)
            capabilities.extend(rust_caps)

        # Add GraphQL capabilities
        if graphql_results:
            gql_caps = graphql_results_to_capabilities(graphql_results)
            capabilities.extend(gql_caps)

        # Add gRPC capabilities
        if grpc_results:
            grpc_caps = grpc_results_to_capabilities(grpc_results)
            capabilities.extend(grpc_caps)

        # Add WebSocket capabilities
        if websocket_results:
            ws_caps = websocket_results_to_capabilities(websocket_results)
            capabilities.extend(ws_caps)

        # Add OpenAPI capabilities
        if openapi_capabilities:
            # Deduplicate: skip OpenAPI endpoints already found by source analysis
            existing_names = {c.name for c in capabilities}
            for cap in openapi_capabilities:
                if cap.name not in existing_names:
                    capabilities.append(cap)
                    existing_names.add(cap.name)

        # Add help-parsed capabilities
        if help_capabilities:
            capabilities.extend(help_capabilities)

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

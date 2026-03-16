"""Phase 2: DESIGN — transform AnalysisResult into ServerDesign."""

import json
import re
from typing import Optional

from mcp_anything.models.analysis import AnalysisResult, Capability, IPCType, ParameterSpec
from mcp_anything.models.design import AuthConfig, BackendConfig, PromptSpec, ResourceSpec, ServerDesign, ToolImpl, ToolSpec
from mcp_anything.pipeline.context import PipelineContext
from mcp_anything.pipeline.phase import Phase


def _to_snake_case(name: str) -> str:
    """Convert a string to snake_case."""
    s = re.sub(r"[^a-zA-Z0-9]", "_", name)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return re.sub(r"_+", "_", s).strip("_").lower()


def _capability_to_tool(cap: Capability, primary_ipc: Optional[IPCType] = None) -> ToolSpec:
    """Convert an analysis Capability to a design ToolSpec."""
    impl = _build_tool_impl(cap, primary_ipc or cap.ipc_type)
    return ToolSpec(
        name=_to_snake_case(cap.name),
        description=cap.description,
        parameters=cap.parameters,
        return_type=cap.return_type,
        module=cap.category,
        ipc_type=cap.ipc_type,
        implementation_hint=f"Source: {cap.source_file}::{cap.source_function}"
        if cap.source_function
        else f"Source: {cap.source_file}",
        impl=impl,
    )


def _build_tool_impl(cap: Capability, ipc_type: Optional[IPCType]) -> ToolImpl:
    """Determine the best implementation strategy for a capability."""
    # HTTP endpoint: capability came from Spring Boot / REST analysis
    if cap.category == "api" and cap.ipc_type == IPCType.PROTOCOL:
        # Parse HTTP method and path from description: "GET /api/users - ..."
        http_method = "GET"
        http_path = "/"
        if cap.description and " " in cap.description:
            parts = cap.description.split(" ", 2)
            if parts[0] in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                http_method = parts[0]
                http_path = parts[1].rstrip(" -")

        arg_mapping = {}
        for p in cap.parameters:
            if "{" + p.name + "}" in http_path:
                arg_mapping[p.name] = {"style": "path"}
            elif p.type == "object":
                arg_mapping[p.name] = {"style": "body"}
            else:
                arg_mapping[p.name] = {"style": "query"}

        return ToolImpl(
            strategy="http_call",
            http_method=http_method,
            http_path=http_path,
            arg_mapping=arg_mapping,
        )

    # CLI options group: capability came from help-text parsing (e.g. ffmpeg sections)
    if cap.category == "cli_options" and ipc_type == IPCType.CLI:
        arg_mapping = {}
        for p in cap.parameters:
            arg_mapping[p.name] = {"style": "flag", "flag": f"-{p.name}"}
        return ToolImpl(
            strategy="cli_subcommand",
            cli_subcommand="",  # no subcommand — pass flags directly to the binary
            arg_mapping=arg_mapping,
        )

    # CLI subcommand: capability came from argparse add_parser detection
    if cap.category == "cli_command" and ipc_type == IPCType.CLI:
        arg_mapping = {}
        for p in cap.parameters:
            # The generic "args" param from subcommand detection is positional
            if p.name == "args":
                arg_mapping[p.name] = {"style": "passthrough"}
            elif p.required and not p.default:
                # Positional arguments (required, no default)
                arg_mapping[p.name] = {"style": "positional", "position": len(
                    [v for v in arg_mapping.values() if v.get("style") == "positional"]
                )}
            else:
                arg_mapping[p.name] = {"style": "flag", "flag": f"--{p.name.replace('_', '-')}"}
        return ToolImpl(
            strategy="cli_subcommand",
            cli_subcommand=cap.name,
            arg_mapping=arg_mapping,
        )

    # Python callable: we know the source file and function
    if cap.source_file and cap.source_function:
        # Build arg mapping — for CLI backends, map params to flags
        arg_mapping = {}
        for i, p in enumerate(cap.parameters):
            if p.required and not p.default:
                arg_mapping[p.name] = {"style": "positional", "position": i}
            else:
                arg_mapping[p.name] = {"style": "flag", "flag": f"--{p.name.replace('_', '-')}"}

        # Class methods ALWAYS use python_call — they need direct import
        if cap.source_class or ipc_type == IPCType.PYTHON_API or ipc_type is None:
            module_path = cap.source_file.replace("/", ".").removesuffix(".py")
            return ToolImpl(
                strategy="python_call",
                python_module=module_path,
                python_function=cap.source_function,
                python_import_path=cap.source_file,
                python_class=cap.source_class,
                python_init_params=cap.init_params,
                arg_mapping=arg_mapping,
            )
        elif ipc_type == IPCType.CLI:
            # Wrap as CLI call — invoke the entry point with subcommand-style args
            return ToolImpl(
                strategy="cli_function",
                cli_entry=cap.source_file,
                python_function=cap.source_function,
                arg_mapping=arg_mapping,
            )

    return ToolImpl(strategy="stub")


def _group_tools(tools: list[ToolSpec]) -> dict[str, list[str]]:
    """Group tool names by module/category."""
    modules: dict[str, list[str]] = {}
    for tool in tools:
        module = tool.module or "general"
        modules.setdefault(module, []).append(tool.name)
    return modules


def _build_auth_config(analysis: AnalysisResult, codebase_path: str = "") -> AuthConfig:
    """Build auth configuration from OpenAPI security schemes or IPC mechanism details."""
    from pathlib import Path
    from mcp_anything.analysis.openapi_analyzer import extract_security_schemes, parse_openapi_spec

    app_name = _to_snake_case(analysis.app_name).upper()

    # Try to re-parse the OpenAPI spec to extract security schemes
    spec_file = None
    for mech in analysis.ipc_mechanisms:
        if mech.details.get("spec_file"):
            spec_file = mech.details["spec_file"]
            break

    if spec_file and codebase_path:
        spec_path = Path(codebase_path) / spec_file
        if spec_path.is_file():
            spec = parse_openapi_spec(spec_path)
            if spec:
                schemes = extract_security_schemes(spec)
                if schemes:
                    scheme = schemes[0]  # Use first security scheme
                    auth_type = scheme.get("type", "")

                    if auth_type == "api_key":
                        location = scheme.get("location", "header")
                        header_name = scheme.get("header", "")
                        return AuthConfig(
                            auth_type="api_key",
                            api_key_header=header_name if location == "header" else "",
                            api_key_query=header_name if location == "query" else "",
                            env_var_token=f"{app_name}_API_KEY",
                        )
                    elif auth_type == "bearer":
                        return AuthConfig(
                            auth_type="bearer",
                            env_var_token=f"{app_name}_TOKEN",
                        )
                    elif auth_type == "basic":
                        return AuthConfig(
                            auth_type="basic",
                            env_var_username=f"{app_name}_USERNAME",
                            env_var_password=f"{app_name}_PASSWORD",
                        )

    # Check IPC mechanism details for auth hints
    for mech in analysis.ipc_mechanisms:
        if mech.details.get("auth_type"):
            auth_type = mech.details["auth_type"]
            if auth_type == "api_key":
                return AuthConfig(
                    auth_type="api_key",
                    api_key_header=mech.details.get("auth_header", "X-API-Key"),
                    env_var_token=f"{app_name}_API_KEY",
                )
            elif auth_type == "bearer":
                return AuthConfig(
                    auth_type="bearer",
                    env_var_token=f"{app_name}_TOKEN",
                )

    return AuthConfig()


def _build_backend_config(analysis: AnalysisResult, codebase_path: str = "") -> Optional[BackendConfig]:
    """Create backend configuration from analysis results."""
    ipc_type = analysis.primary_ipc
    if not ipc_type:
        # Still need a backend config if we have class methods (python_call needs codebase_path)
        has_class_methods = any(cap.source_class for cap in analysis.capabilities)
        if has_class_methods:
            return BackendConfig(backend_type=IPCType.PYTHON_API, codebase_path=codebase_path)
        return None

    config = BackendConfig(backend_type=ipc_type, codebase_path=codebase_path)

    # For CLI apps, try to find the entry point command
    if ipc_type == IPCType.CLI:
        if analysis.entry_points:
            config.command = f"python {analysis.entry_points[0]}"
        else:
            # Fallback: find a Python file that likely has a main script
            found_py = False
            for cap in analysis.capabilities:
                if cap.source_file and cap.source_file.endswith(".py"):
                    config.command = f"python {cap.source_file}"
                    found_py = True
                    break
            # For non-Python CLI tools (ffmpeg, sox, etc.), use the app name
            if not found_py:
                config.command = analysis.app_name

    # Extract details from IPC mechanisms
    for mech in analysis.ipc_mechanisms:
        if mech.ipc_type == ipc_type:
            if "port" in mech.details:
                config.port = int(mech.details["port"])
            if "protocol" in mech.details:
                config.env_vars["PROTOCOL"] = mech.details["protocol"]
            if "framework" in mech.details:
                config.env_vars["FRAMEWORK"] = mech.details["framework"]
            break

    # Build auth config for HTTP backends
    auth = _build_auth_config(analysis, codebase_path)
    if auth.auth_type:
        config.auth = auth

    return config


def _generate_resources(analysis: AnalysisResult) -> list[ResourceSpec]:
    """Generate standard resource specs based on the application type."""
    app = analysis.app_name
    resources = [
        ResourceSpec(
            uri=f"app://{app}/status",
            name=f"{_to_snake_case(app)}_status",
            description=f"Current status and version of {app}",
            resource_type="status",
        ),
        ResourceSpec(
            uri=f"app://{app}/commands",
            name=f"{_to_snake_case(app)}_commands",
            description=f"Available commands and tools in {app}",
            resource_type="commands",
        ),
    ]

    # Add a config resource if we detect config-related capabilities
    has_config = any(
        cap.category in ("config", "query") or "config" in cap.name.lower()
        for cap in analysis.capabilities
    )
    if has_config:
        resources.append(
            ResourceSpec(
                uri=f"app://{app}/config",
                name=f"{_to_snake_case(app)}_config",
                description=f"Current configuration of {app}",
                resource_type="config",
            )
        )

    return resources


async def _llm_design(analysis: AnalysisResult) -> Optional[ServerDesign]:
    """Use Claude API for design decisions."""
    try:
        import anthropic
    except ImportError:
        return None

    caps_summary = json.dumps(
        [{"name": c.name, "description": c.description, "category": c.category} for c in analysis.capabilities],
        indent=2,
    )

    prompt = f"""Given these capabilities for "{analysis.app_name}":

{caps_summary}

Suggest:
1. How to group these into tool modules (JSON object: module_name -> [tool_names])
2. What MCP resources to expose (JSON array: [{{"uri", "name", "description"}}])

Return JSON with "tool_modules" and "resources" keys only."""

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)
    except Exception:
        return None


def _detect_target_install(codebase_path) -> str:
    """Detect how to install the target project's dependencies."""
    from pathlib import Path

    root = Path(codebase_path)

    # Check for pyproject.toml
    if (root / "pyproject.toml").exists():
        return f"pip install -e {root}"
    # Check for setup.py
    if (root / "setup.py").exists():
        return f"pip install -e {root}"
    # Check for setup.cfg
    if (root / "setup.cfg").exists():
        return f"pip install -e {root}"
    # Check for requirements.txt
    if (root / "requirements.txt").exists():
        return f"pip install -r {root / 'requirements.txt'}"
    return ""


def _make_run_cli_tool(analysis: AnalysisResult) -> Optional[ToolSpec]:
    """Create a 'run' tool for single-purpose CLI apps.

    When a CLI app has no subcommands and few detected tools, the most useful
    tool is often just "run the CLI with arguments" (e.g., `httpstat <URL>`).
    """
    if analysis.primary_ipc != IPCType.CLI:
        return None

    app_name = _to_snake_case(analysis.app_name)
    entry = analysis.entry_points[0] if analysis.entry_points else None
    # Fallback: find the first Python file that looks like a main script
    if not entry:
        for cap in analysis.capabilities:
            if cap.source_file and cap.source_file.endswith(".py"):
                entry = cap.source_file
                break
    # For non-Python CLI tools (ffmpeg, sox, etc.), use the app name as the command
    if not entry:
        entry = analysis.app_name

    description = f"Run {analysis.app_name} with the given command-line arguments"

    return ToolSpec(
        name=f"run_{app_name}",
        description=description,
        parameters=[
            ParameterSpec(
                name="args",
                type="string",
                description=f"Command-line arguments to pass to {analysis.app_name} (e.g. a URL or flags)",
                required=True,
            ),
        ],
        return_type="string",
        module="general",
        ipc_type=IPCType.CLI,
        implementation_hint=f"Run: python {entry} <args>",
        impl=ToolImpl(
            strategy="cli_subcommand",
            cli_subcommand="",  # empty = no subcommand, just pass args
            arg_mapping={"args": {"style": "passthrough"}},
        ),
    )


async def _enhance_descriptions_with_llm(
    tools: list[ToolSpec], app_name: str
) -> list[ToolSpec]:
    """Use Claude to rewrite tool descriptions to be more useful for AI agents."""
    try:
        import anthropic
    except ImportError:
        return tools

    tool_summaries = []
    for t in tools:
        params = ", ".join(f"{p.name}: {p.type}" for p in t.parameters)
        tool_summaries.append(f"- {t.name}({params}): {t.description}")

    prompt = f"""You are improving tool descriptions for an MCP server wrapping "{app_name}".
These descriptions will be read by an AI assistant to decide which tool to call.

Current tools:
{chr(10).join(tool_summaries)}

For each tool, write a concise, action-oriented description (1 sentence, max 100 chars) that clearly explains what the tool does.

Return a JSON object mapping tool name to new description. Only include tools whose descriptions you improved.
Example: {{"tool_name": "Better description here"}}"""

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        improvements = json.loads(text)

        for tool in tools:
            if tool.name in improvements and isinstance(improvements[tool.name], str):
                tool.description = improvements[tool.name]
    except Exception:
        pass  # Silently fall back to original descriptions

    return tools


def _generate_prompts(analysis: AnalysisResult) -> list[PromptSpec]:
    """Generate MCP prompts (server-delivered skills) from analysis results."""
    app = analysis.app_name
    app_snake = _to_snake_case(app)
    prompts: list[PromptSpec] = []

    # General usage prompt
    tool_list = "\n".join(f"- {c.name}: {c.description}" for c in analysis.capabilities[:20])
    prompts.append(PromptSpec(
        name=f"use_{app_snake}",
        description=f"Guide for using {app} tools effectively",
        template=f"You have access to the {app} MCP server with these tools:\n\n{tool_list}\n\n"
        f"Use the appropriate tool based on the user's request. "
        f"Always check required parameters before calling a tool.",
    ))

    # Debug prompt
    prompts.append(PromptSpec(
        name=f"debug_{app_snake}",
        description=f"Diagnose issues with {app} operations",
        arguments=[
            ParameterSpec(name="error_message", type="string", description="The error to diagnose"),
        ],
        template=f"The user encountered an error while using {app}.\n\n"
        "Error: {{error_message}}\n\n"
        f"Available tools: {', '.join(c.name for c in analysis.capabilities[:15])}\n\n"
        "Diagnose the issue and suggest which tool to use to resolve it.",
    ))

    return prompts


def _generate_doc_resources(analysis: AnalysisResult) -> list[ResourceSpec]:
    """Generate dynamic documentation resources from analysis."""
    app = analysis.app_name
    app_snake = _to_snake_case(app)

    resources: list[ResourceSpec] = []

    # Tool index resource — dynamic list of all tools with params
    resources.append(ResourceSpec(
        uri=f"docs://{app}/tool-index",
        name=f"{app_snake}_tool_index",
        description=f"Complete index of all {app} tools with parameters and usage",
        resource_type="docs",
    ))

    # Group capabilities by category for category-specific docs
    categories = {c.category for c in analysis.capabilities if c.category != "general"}
    for cat in sorted(categories)[:5]:
        cat_snake = _to_snake_case(cat)
        resources.append(ResourceSpec(
            uri=f"docs://{app}/{cat_snake}",
            name=f"{app_snake}_{cat_snake}_docs",
            description=f"Documentation for {app} {cat} capabilities",
            resource_type="docs",
        ))

    return resources


class DesignPhase(Phase):
    @property
    def name(self) -> str:
        return "design"

    def validate_preconditions(self, ctx: PipelineContext) -> list[str]:
        if not ctx.manifest.analysis:
            return ["Analysis phase must complete before design"]
        return []

    async def execute(self, ctx: PipelineContext) -> None:
        analysis = ctx.manifest.analysis
        assert analysis is not None
        console = ctx.console

        # Convert capabilities to tool specs, deduplicating by name
        tools: list[ToolSpec] = []
        seen_names: set[str] = set()
        for cap in analysis.capabilities:
            tool = _capability_to_tool(cap, analysis.primary_ipc)
            if tool.name not in seen_names:
                tools.append(tool)
                seen_names.add(tool.name)

        # Add a generic "run" tool for all CLI apps — always the most useful tool
        if analysis.primary_ipc == IPCType.CLI:
            run_tool = _make_run_cli_tool(analysis)
            if run_tool and run_tool.name not in seen_names:
                tools.insert(0, run_tool)

        console.print(f"    Designed {len(tools)} tools")

        # Enhance descriptions with LLM
        if not ctx.options.no_llm:
            tools = await _enhance_descriptions_with_llm(tools, analysis.app_name)

        # Group tools into modules
        tool_modules = _group_tools(tools)

        # Generate resources
        resources = _generate_resources(analysis)
        console.print(f"    Designed {len(resources)} resources")

        # Try LLM-assisted grouping
        if not ctx.options.no_llm:
            llm_result = await _llm_design(analysis)
            if llm_result and isinstance(llm_result, dict):
                if "tool_modules" in llm_result:
                    tool_modules = llm_result["tool_modules"]
                if "resources" in llm_result:
                    resources = [
                        ResourceSpec(**r) for r in llm_result["resources"]
                        if isinstance(r, dict) and "uri" in r and "name" in r
                    ]

        # Build backend config
        backend = _build_backend_config(analysis, ctx.manifest.codebase_path)

        # Detect target project install hint
        target_install_hint = _detect_target_install(ctx.codebase_path)
        if target_install_hint:
            console.print(f"    Target install: {target_install_hint}")

        # Generate MCP prompts (server-delivered skills)
        prompts = _generate_prompts(analysis)
        console.print(f"    Designed {len(prompts)} prompts")

        # Generate dynamic doc resources
        doc_resources = _generate_doc_resources(analysis)
        resources.extend(doc_resources)
        if doc_resources:
            console.print(f"    Designed {len(doc_resources)} doc resources")

        # Transport and enterprise features
        transport = ctx.options.transport
        is_http = transport == "http"
        enable_telemetry = is_http  # Enable telemetry for HTTP servers

        # Add httpx dependency if any tool uses HTTP calls
        dependencies = ["mcp>=1.0"]
        if any(t.impl.strategy == "http_call" for t in tools):
            dependencies.append("httpx>=0.27")
        if enable_telemetry:
            dependencies.append("opentelemetry-api>=1.20")
            dependencies.append("opentelemetry-sdk>=1.20")
            dependencies.append("opentelemetry-exporter-otlp>=1.20")

        if is_http:
            console.print("    Transport: HTTP (streamable)")
            console.print("    Telemetry: OpenTelemetry enabled")
            console.print("    Docker: Dockerfile will be generated")

        design = ServerDesign(
            server_name=analysis.app_name,
            server_description=analysis.app_description,
            tools=tools,
            resources=resources,
            prompts=prompts,
            tool_modules=tool_modules,
            backend=backend,
            dependencies=dependencies,
            target_install_hint=target_install_hint,
            transport=transport,
            enable_telemetry=enable_telemetry,
            generate_docker=is_http,
        )

        ctx.manifest.design = design

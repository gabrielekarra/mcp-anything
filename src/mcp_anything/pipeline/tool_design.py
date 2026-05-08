"""Phase 2: Tool Design.

LLM shapes tools from the DomainModel using 2026 rules:
  - Group CRUD: ≥3 operations on the same resource → single grouped tool with operation discriminator
  - Composable atomic tools with rich parameters
  - Progressive-disclosure groupings
  - Programmatic-call promotion for recurring multi-step workflows
  - Compact-default response shapes

A second LLM pass rewrites every tool description in agent-consumer voice.
Output: tool_spec.yaml + updated manifest.
"""

import json
from pathlib import Path
from typing import Optional

import yaml

from mcp_anything.models.design import (
    AuthConfig,
    BackendConfig,
    ComposedTool,
    ParameterSpec,
    PromptSpec,
    ResourceSpec,
    ServerDesign,
    ToolGroup,
    ToolImpl,
    ToolSpec,
)
from mcp_anything.models.domain import DomainModel
from mcp_anything.pipeline.context import PipelineContext
from mcp_anything.pipeline.phase import Phase

try:
    from mcp_anything.models.analysis import IPCType
except ImportError:
    IPCType = None  # type: ignore[assignment]


_TOOL_DESIGN_RULES_V1 = """\
You are a senior MCP server architect. Design tools using these 2026 rules:

1. GROUP CRUD: If the data source has ≥3 CRUD operations (create/read/update/delete/list)
   on the same resource, collapse them into ONE tool with an `operation` parameter.
   Example: list_tasks + create_task + update_task + delete_task → manage_task(operation: "list"|"create"|"update"|"delete")

2. ATOMIC TOOLS: Each tool does exactly one thing. No multi-step tools unless promoted as ComposedTool.

3. PROGRESSIVE DISCLOSURE:
   - Most tools: disclosure_level="default" (shown in standard listing)
   - Power/admin tools: disclosure_level="verbose" (hidden unless requested)
   - Group tools by category (e.g. "tasks", "projects", "members")

4. COMPOSED TOOLS: If the domain brief contains a use-case that requires ≥3 sequential
   tool calls, promote it to a ComposedTool. Include all steps explicitly.

5. COMPACT RESPONSES: Every tool has a compact_fields list (3-7 most useful fields).
   Full response available via verbose=true parameter.

6. DESCRIPTION VOICE: Write descriptions from the agent's perspective.
   Good: "Returns all tasks assigned to a user across projects, filtered by status."
   Bad: "Wraps the GET /tasks endpoint." or "Calls the task service."

7. PARAMETER NAMES: Use domain vocabulary from the glossary. No generic names like "id",
   prefer "task_id", "project_id", etc.

8. ARG_MAPPING (REQUIRED for http_call): Every http_call tool MUST include an arg_mapping object
   where each parameter (except verbose) has a "style" of "path", "query", or "body":
   - "path": parameter appears as {param} in http_path — substituted into the URL
   - "query": appended as a URL query string parameter
   - "body": sent in the JSON request body (POST/PUT/PATCH only)
   If http_path contains {param_name}, that param MUST have style="path".
   Parameters for GET/DELETE are typically "query" unless in the path.
   Parameters for POST/PUT/PATCH body fields are "body".
   The "api_name" field is the actual API parameter name if different from the tool param name.

9. NON-REST HTTP APIs: Some HTTP backends use RPC-style or action-discriminated endpoints
   instead of REST resources (MediaWiki /api.php, JSON-RPC over HTTP, SOAP, generic /rpc
   endpoints). For these:
   - `http_path` is the SAME for every operation (e.g. "/api.php").
   - The operation is selected by FIXED query params. Put those in `http_query_constants`
     (e.g. {"action": "query", "format": "json", "prop": "info"} for MediaWiki).
   - Tool parameter names MUST match the actual API parameter names exactly
     (e.g. MediaWiki expects `titles`, not `page_title`; `srsearch`, not `query`).
   - The runtime merges the tool's params with `http_query_constants` into one query string.
   For REST APIs this field stays empty.

Return ONLY valid JSON, no markdown.
"""


def _build_tool_design_prompt(domain_model: DomainModel, data_source_summary: Optional[str]) -> str:
    use_cases_text = "\n".join(
        f"  {uc.id}: {uc.description} (outcome: {uc.expected_outcome})"
        for uc in domain_model.use_cases
    )
    entities_text = ", ".join(domain_model.domain_entities) or "(none detected)"
    glossary_text = "\n".join(
        f"  - {g.term}: {g.definition}"
        for g in domain_model.glossary
    )
    access_patterns_text = "\n".join(
        f"  - {p}" for p in domain_model.access_patterns
    )

    data_section = ""
    if data_source_summary:
        data_section = f"\n## Data Source\n{data_source_summary[:6000]}\n"
    elif domain_model.data_sources:
        ds_lines = "\n".join(
            f"  - kind={ds.kind}, path={ds.path}"
            for ds in domain_model.data_sources
        )
        data_section = (
            "\n## Data Source\n"
            f"{ds_lines}\n"
            "(No spec body available — use your knowledge of this API's contract "
            "to set http_path, http_query_constants, and parameter names correctly.)\n"
        )

    return f"""## Domain Model

Server: {domain_model.server_name}
Description: {domain_model.domain_description}

### Use Cases
{use_cases_text}

### Entities
{entities_text}

### Glossary
{glossary_text}

### Access Patterns
{access_patterns_text}
{data_section}
## Output Format

Return a JSON object with:
{{
  "server_name": "<string>",
  "server_description": "<one paragraph, agent-consumer perspective>",
  "tool_groups": [
    {{
      "name": "<group_name>",
      "description": "<what this group does>",
      "operations": ["create", "read", "update", "delete"],
      "disclosure_level": "default"
    }}
  ],
  "tools": [
    {{
      "name": "<snake_case_name>",
      "description": "<agent-consumer voice, ≥20 chars>",
      "group": "<group_name or null>",
      "disclosure_level": "default",
      "compact_fields": ["field1", "field2"],
      "parameters": [
        {{
          "name": "<param_name>",
          "type": "string|integer|boolean|array|object",
          "description": "<what this parameter controls>",
          "required": true
        }}
      ],
      "return_type": "dict",
      "impl": {{
        "strategy": "http_call | python_call | cli_subcommand | grpc_call",
        "http_method": "GET",
        "http_path": "/path/{{param}}",
        "http_query_constants": {{}},
        "arg_mapping": {{
          "param_name": {{"style": "path|query|body", "api_name": "actual_api_name_if_different"}}
        }},
        "python_module": "package.module (for python_call, e.g. 'scrapegraphai.graphs')",
        "python_function": "function_or_method_name (for python_call)",
        "python_class": "ClassName (for python_call when calling an instance method; leave empty for module-level functions)",
        "python_init_params": [
          {{"name": "prompt", "type": "string", "description": "passed to __init__", "required": true}}
        ],
        "grpc_service": "ServiceName",
        "grpc_method": "RpcMethodName",
        "grpc_proto_module": "proto_file_stem",
        "grpc_request_type": "RequestMessageName",
        "grpc_response_type": "ResponseMessageName"
      }}
    }}
  ],
  "composed_tools": [
    {{
      "name": "<snake_case_name>",
      "description": "<agent-consumer voice>",
      "steps": ["tool_name_1", "tool_name_2", "tool_name_3"],
      "trigger_pattern": "<when an agent should prefer this over individual tools>"
    }}
  ],
  "dependencies": ["mcp>=1.0"],
  "transport": "stdio"
}}
"""


_TOOL_RESHAPE_RULES = """\
You are reshaping an existing set of MCP tools to match a domain brief. You have authority to:

1. DROP tools that are not justified by any use case in the domain brief.
2. GROUP tools: if ≥3 tools perform CRUD operations on the same resource, collapse them into ONE
   tool named manage_<resource>(operation: "list"|"create"|"update"|"delete"|...). Use the name
   of the most common seed tool as the grouped tool's seed_name.
3. RENAME tools: use domain vocabulary from the glossary. Snake_case only.
4. SET disclosure_level: "default" for everyday tools, "verbose" for admin/power tools.
5. REWRITE descriptions: agent-consumer voice, ≥20 chars, action-oriented, max 2 sentences.
6. SET compact_fields: 3-7 most useful response fields.
7. ADD composed_tools: multi-step workflows from use cases that require ≥3 sequential calls.

You MUST NOT:
- Invent tools that do not correspond to a seed tool by name.
- Alter impl details (strategies, paths, methods, modules, RPC names) — they are authoritative.
- Reference implementation internals in descriptions ("calls GET /foo").
- Output a seed_name that was not in the input seed tool list.

If a use case requires a tool not in the seed list, omit it — do not invent it.
Return ONLY valid JSON, no markdown.
"""


def _build_reshape_prompt(domain_model: DomainModel, seed_tools: list) -> str:
    """Build the LLM prompt for reshape mode."""
    use_cases_text = "\n".join(
        f"  {uc.id}: {uc.description}"
        for uc in domain_model.use_cases
    )
    glossary_text = "\n".join(
        f"  - {g.term}: {g.definition}"
        for g in domain_model.glossary
    )

    seed_lines = []
    for t in seed_tools:
        param_names = ", ".join(
            f"{p.name}:{p.type}" for p in t.parameters if p.name != "verbose"
        )
        seed_lines.append(
            f'  - name="{t.name}" strategy={t.impl.strategy} '
            f'params=[{param_names}] desc="{t.description[:80]}"'
        )
    seed_text = "\n".join(seed_lines)

    return f"""## Domain Brief

Server: {domain_model.server_name}
{domain_model.domain_description}

### Use Cases
{use_cases_text}

### Glossary
{glossary_text}

## Seed Tools ({len(seed_tools)} tools from legacy analyzer)
{seed_text}

## Output Format

Return a JSON object:
{{
  "kept_tools": [
    {{
      "seed_name": "<exact name from seed list>",
      "new_name": "<snake_case — same as seed_name if no rename needed>",
      "group": "<group name or null>",
      "disclosure_level": "default",
      "description": "<agent-consumer voice, ≥20 chars>",
      "compact_fields": ["field1", "field2", "field3"]
    }}
  ],
  "tool_groups": [
    {{
      "name": "<group_name>",
      "description": "<what this group covers>",
      "operations": ["list", "create"],
      "disclosure_level": "default"
    }}
  ],
  "composed_tools": [
    {{
      "name": "<snake_case_name>",
      "description": "<agent-consumer voice>",
      "steps": ["tool_name_1", "tool_name_2"],
      "trigger_pattern": "<when an agent should prefer this>"
    }}
  ],
  "dropped_tools": ["seed_name_1", "seed_name_2"],
  "drop_reasons": {{"seed_name_1": "not covered by any use case"}}
}}
"""


_DOCSTRING_REWRITE_SYSTEM = """\
You are rewriting MCP tool descriptions for agent consumers. Rules:

- Present tense, action-oriented. Start with what it returns or does.
- Include: what the agent gets back, key parameters that change behavior, when NOT to use it.
- Never say "Wraps", "Calls", "Proxies", "Sends a request to".
- Maximum 2 sentences. No bullet points.
- Return ONLY a JSON object mapping tool_name → new_description.
"""


def _build_docstring_rewrite_prompt(tools: list[ToolSpec]) -> str:
    entries = "\n".join(
        f'  "{t.name}": "{t.description}"'
        for t in tools
    )
    return (
        f"Rewrite these tool descriptions in agent-consumer voice:\n{{\n{entries}\n}}\n\n"
        "Return ONLY: {\"tool_name\": \"new description\", ...}"
    )


def _parse_tool_spec(data: dict) -> ServerDesign:
    """Parse the LLM-returned tool design dict into a ServerDesign."""
    tools = []
    for t in data.get("tools", []):
        impl_data = t.get("impl", {})
        init_params_raw = impl_data.get("python_init_params", []) or []
        init_params = [
            ParameterSpec(
                name=p["name"],
                type=p.get("type", "string"),
                description=p.get("description", ""),
                required=p.get("required", True),
                default=p.get("default"),
                location=p.get("location", ""),
                api_name=p.get("api_name", ""),
            )
            for p in init_params_raw
            if isinstance(p, dict) and "name" in p
        ]
        raw_constants = impl_data.get("http_query_constants") or {}
        if isinstance(raw_constants, dict):
            http_query_constants = {str(k): str(v) for k, v in raw_constants.items()}
        else:
            http_query_constants = {}
        # Parse arg_mapping from LLM output — validates style values.
        raw_arg_mapping = impl_data.get("arg_mapping") or {}
        arg_mapping: dict[str, dict] = {}
        if isinstance(raw_arg_mapping, dict):
            for pname, meta in raw_arg_mapping.items():
                if isinstance(meta, dict) and meta.get("style") in {"path", "query", "body"}:
                    arg_mapping[str(pname)] = {
                        "style": meta["style"],
                        "api_name": str(meta.get("api_name") or pname),
                    }
        impl = ToolImpl(
            strategy=impl_data.get("strategy", "http_call"),
            http_method=impl_data.get("http_method", ""),
            http_path=impl_data.get("http_path", ""),
            http_query_constants=http_query_constants,
            arg_mapping=arg_mapping,
            python_module=impl_data.get("python_module", ""),
            python_function=impl_data.get("python_function", ""),
            python_class=impl_data.get("python_class", ""),
            python_init_params=init_params,
            cli_subcommand=impl_data.get("cli_subcommand", ""),
            grpc_service=impl_data.get("grpc_service", ""),
            grpc_method=impl_data.get("grpc_method", ""),
            grpc_proto_module=impl_data.get("grpc_proto_module", ""),
            grpc_request_type=impl_data.get("grpc_request_type", ""),
            grpc_response_type=impl_data.get("grpc_response_type", ""),
        )
        params = [
            ParameterSpec(
                name=p["name"],
                type=p.get("type", "string"),
                description=p.get("description", ""),
                required=p.get("required", True),
                default=p.get("default"),
                enum_values=p.get("enum_values"),
                location=p.get("location", ""),
                api_name=p.get("api_name", ""),
            )
            for p in t.get("parameters", [])
        ]
        # Append verbose flag to every tool (if LLM didn't already include it)
        if not any(p.name == "verbose" for p in params):
            params.append(ParameterSpec(
                name="verbose",
                type="boolean",
                description="Return full response payload with metadata when true.",
                required=False,
                default="false",
            ))
        tools.append(ToolSpec(
            name=t["name"],
            description=t.get("description", ""),
            parameters=params,
            return_type=t.get("return_type", "dict"),
            impl=impl,
        ))

    tool_groups = [
        ToolGroup(
            name=g["name"],
            description=g.get("description", ""),
            operations=g.get("operations", []),
            disclosure_level=g.get("disclosure_level", "default"),
        )
        for g in data.get("tool_groups", [])
    ]

    composed_tools = [
        ComposedTool(
            name=c["name"],
            description=c.get("description", ""),
            steps=c.get("steps", []),
            trigger_pattern=c.get("trigger_pattern", ""),
        )
        for c in data.get("composed_tools", [])
    ]

    return ServerDesign(
        server_name=data.get("server_name", "mcp-server"),
        server_description=data.get("server_description", ""),
        tools=tools,
        tool_groups=tool_groups,
        composed_tools=composed_tools,
        dependencies=data.get("dependencies", ["mcp>=1.0"]),
        transport=data.get("transport", "stdio"),
        enable_telemetry=True,
        discovery_endpoint=True,
    )


class ToolDesignPhase(Phase):
    """Phase 2: LLM designs tools from DomainModel using 2026 rules."""

    name = "tool_design"

    def validate_preconditions(self, ctx: PipelineContext) -> list[str]:
        if not ctx.manifest.domain_model:
            return ["Domain model not found. Run Phase 1 (domain_modeling) first."]
        return []

    async def execute(self, ctx: PipelineContext) -> None:
        domain_model = DomainModel.model_validate(ctx.manifest.domain_model)

        if ctx.options.resume and ctx.manifest.tool_spec:
            design = ServerDesign.model_validate(ctx.manifest.tool_spec)
            ctx.console.print("[green]Loaded existing tool spec.[/green]")
        elif ctx.manifest.design and ctx.manifest.design.tools:
            # Codebase mode: reshape the legacy seed design using the domain brief
            design = self._reshape_tools(domain_model, ctx.manifest.design, ctx)
        else:
            design = self._design_tools(domain_model, ctx)

        # Write tool_spec.yaml for customer review / descriptions editing
        tool_spec_path = ctx.output_dir / "tool_spec.yaml"
        ctx.output_dir.mkdir(parents=True, exist_ok=True)
        tool_spec_path.write_text(
            yaml.dump(design.model_dump(mode="json"), allow_unicode=True, sort_keys=False)
        )
        ctx.console.print(f"[green]Tool spec written to {tool_spec_path}[/green]")

        # Write descriptions.yaml for compatibility with --description flag
        descriptions_path = ctx.output_dir / "descriptions.yaml"
        descriptions_data = {t.name: t.description for t in design.tools}
        descriptions_path.write_text(
            yaml.dump(descriptions_data, allow_unicode=True, sort_keys=False)
        )

        ctx.manifest.tool_spec = design.model_dump(mode="json")
        ctx.manifest.design = design  # keep legacy field populated for emitter compatibility
        ctx.save_manifest()

    @staticmethod
    def _is_actionable_seed_tool(tool: "ToolSpec") -> bool:
        """Return True only for tools with a concrete, callable implementation."""
        impl = tool.impl
        if impl.strategy == "http_call":
            return bool(impl.http_method and impl.http_path)
        if impl.strategy in ("python_call", "cli_function"):
            return bool(impl.python_module and impl.python_function)
        if impl.strategy == "cli_subcommand":
            return True
        if impl.strategy == "protocol_call":
            # Only gRPC stubs are meaningful protocol_call tools
            return bool(impl.grpc_service)
        return False

    def _reshape_tools(
        self, domain_model: DomainModel, seed_design: ServerDesign, ctx: PipelineContext
    ) -> ServerDesign:
        """Reshape a legacy seed ServerDesign using the domain brief (codebase mode)."""
        all_seed_tools = seed_design.tools
        # Drop internal helper stubs that can't be called as MCP tools
        seed_tools = [t for t in all_seed_tools if self._is_actionable_seed_tool(t)]
        dropped_stubs = len(all_seed_tools) - len(seed_tools)
        if dropped_stubs:
            ctx.console.print(
                f"  [dim]Pre-filtered {dropped_stubs} non-actionable stub(s) from seed.[/dim]"
            )
        seed_by_name = {t.name: t for t in seed_tools}

        if ctx.options.no_llm:
            ctx.console.print("[dim]--no-llm: skipping reshape, using seed design directly.[/dim]")
            return seed_design.model_copy(update={"tools": seed_tools})

        try:
            from mcp_anything.pipeline.llm_client import call_llm_for_json
        except ImportError:
            ctx.console.print("[yellow]anthropic not installed; using seed design directly.[/yellow]")
            return seed_design.model_copy(update={"tools": seed_tools})

        ctx.console.print(
            f"[dim]Reshaping {len(seed_tools)} seed tools using domain brief...[/dim]"
        )
        prompt = _build_reshape_prompt(domain_model, seed_tools)

        try:
            data = call_llm_for_json(prompt, system=_TOOL_RESHAPE_RULES)
        except Exception as exc:
            ctx.console.print(f"[yellow]Reshape LLM call failed ({exc}); using seed design.[/yellow]")
            return seed_design.model_copy(update={"tools": seed_tools})

        kept_entries = data.get("kept_tools", [])
        if not kept_entries:
            ctx.console.print("[yellow]Reshape returned no kept tools; using seed design.[/yellow]")
            return seed_design.model_copy(update={"tools": seed_tools})

        kept_tools: list[ToolSpec] = []
        invalid = 0
        for entry in kept_entries:
            sname = entry.get("seed_name", "")
            seed_tool = seed_by_name.get(sname)
            if seed_tool is None:
                invalid += 1
                continue  # LLM hallucinated a seed name — reject silently

            new_name = entry.get("new_name") or sname
            description = entry.get("description") or seed_tool.description
            if len(description) < 20:
                description = seed_tool.description

            kept_tools.append(seed_tool.model_copy(update={
                "name": new_name,
                "description": description,
                # impl and parameters preserved from seed — do NOT take from LLM output
            }))

        if invalid:
            ctx.console.print(
                f"[yellow]Reshape:[/yellow] {invalid} LLM tool reference(s) not in seed — ignored."
            )

        if not kept_tools:
            ctx.console.print("[yellow]All reshape entries invalid; using seed design.[/yellow]")
            return seed_design.model_copy(update={"tools": seed_tools})

        dropped = data.get("dropped_tools", [])
        if dropped:
            ctx.console.print(
                f"  [dim]Dropped {len(dropped)} tool(s) not justified by brief: "
                f"{', '.join(str(d) for d in dropped[:5])}"
                f"{'...' if len(dropped) > 5 else ''}[/dim]"
            )
        ctx.console.print(f"  [green]Kept {len(kept_tools)} tool(s) after reshape.[/green]")

        tool_groups = [
            ToolGroup(
                name=g["name"],
                description=g.get("description", ""),
                operations=g.get("operations", []),
                disclosure_level=g.get("disclosure_level", "default"),
            )
            for g in data.get("tool_groups", [])
            if isinstance(g, dict) and "name" in g
        ]
        composed_tools = [
            ComposedTool(
                name=c["name"],
                description=c.get("description", ""),
                steps=c.get("steps", []),
                trigger_pattern=c.get("trigger_pattern", ""),
            )
            for c in data.get("composed_tools", [])
            if isinstance(c, dict) and "name" in c
        ]

        return seed_design.model_copy(update={
            "tools": kept_tools,
            "tool_groups": tool_groups,
            "composed_tools": composed_tools,
            "server_name": domain_model.server_name,
            "server_description": domain_model.domain_description,
        })

    def _design_tools(self, domain_model: DomainModel, ctx: PipelineContext) -> ServerDesign:
        if ctx.options.no_llm:
            ctx.console.print("[dim]--no-llm: generating minimal tool spec from domain model.[/dim]")
            return self._fallback_design(domain_model)

        # When a parseable data source is provided (OpenAPI spec, .proto), extract
        # authoritative tool impls from it first — routes, methods, and param styles
        # are ground truth. Then let the LLM reshape names/descriptions/grouping only,
        # exactly like codebase mode does with seed tools. This guarantees the generated
        # server will call the real backend paths without any manual patches.
        seed_tools = self._derive_tools_from_data_source(domain_model)
        if seed_tools:
            ctx.console.print(
                f"[dim]Parsed {len(seed_tools)} tools from data source spec; "
                "reshaping with domain brief...[/dim]"
            )
            seed_design = ServerDesign(
                server_name=domain_model.server_name,
                server_description=domain_model.domain_description,
                tools=seed_tools,
                enable_telemetry=True,
                discovery_endpoint=True,
                backend_base_url=self._get_backend_base_url(domain_model),
            )
            return self._reshape_tools(domain_model, seed_design, ctx)

        try:
            from mcp_anything.pipeline.llm_client import call_llm_for_json
        except ImportError:
            ctx.console.print("[yellow]anthropic not installed; using fallback tool design.[/yellow]")
            return self._fallback_design(domain_model)

        ctx.console.print("[dim]Calling LLM for tool design...[/dim]")
        data_summary = self._get_data_source_summary(domain_model)
        prompt = _build_tool_design_prompt(domain_model, data_summary)

        try:
            data = call_llm_for_json(prompt, system=_TOOL_DESIGN_RULES_V1)
        except Exception as exc:
            ctx.console.print(f"[yellow]Tool design LLM call failed ({exc}); using fallback.[/yellow]")
            return self._fallback_design(domain_model)

        design = _parse_tool_spec(data)

        # Second pass: rewrite all docstrings in agent-consumer voice
        if design.tools:
            design = self._rewrite_docstrings(design, ctx)

        # Carry through the backend base URL from the data source spec
        base_url = self._get_backend_base_url(domain_model)
        if base_url:
            design = design.model_copy(update={"backend_base_url": base_url})

        return design

    def _rewrite_docstrings(self, design: ServerDesign, ctx: PipelineContext) -> ServerDesign:
        try:
            from mcp_anything.pipeline.llm_client import call_llm_for_json
        except ImportError:
            return design

        ctx.console.print("[dim]Rewriting tool descriptions in agent-consumer voice...[/dim]")
        prompt = _build_docstring_rewrite_prompt(design.tools)

        try:
            rewrites: dict = call_llm_for_json(prompt, system=_DOCSTRING_REWRITE_SYSTEM)
        except Exception:
            return design

        updated_tools = []
        for tool in design.tools:
            new_desc = rewrites.get(tool.name)
            if new_desc and isinstance(new_desc, str) and len(new_desc) >= 20:
                tool = tool.model_copy(update={"description": new_desc})
            updated_tools.append(tool)

        return design.model_copy(update={"tools": updated_tools})

    def _get_data_source_summary(self, domain_model: DomainModel) -> Optional[str]:
        for ds in domain_model.data_sources:
            path = Path(ds.path)
            if not path.exists():
                continue
            try:
                text = path.read_text(errors="replace")
                if ds.kind == "openapi":
                    try:
                        import json as _json
                        import yaml as _yaml
                        spec = _yaml.safe_load(text) if path.suffix in (".yaml", ".yml") else _json.loads(text)
                        from mcp_anything.pipeline.domain_modeling import _summarize_openapi
                        return _summarize_openapi(spec)
                    except Exception:
                        pass
                return text[:4000]
            except OSError:
                pass
        return None

    def _get_backend_base_url(self, domain_model: DomainModel) -> str:
        """Extract servers[0].url from an OpenAPI spec in the domain model's data sources."""
        for ds in domain_model.data_sources:
            if ds.kind != "openapi":
                continue
            # Try parsed_raw first (populated during domain modeling)
            raw = ds.parsed_raw
            if not raw:
                path = Path(ds.path)
                if not path.exists():
                    continue
                try:
                    import json as _json
                    import yaml as _yaml
                    text = path.read_text(errors="replace")
                    raw = _yaml.safe_load(text) if path.suffix in (".yaml", ".yml") else _json.loads(text)
                except Exception:
                    continue
            servers = raw.get("servers", []) if raw else []
            if servers:
                url = servers[0].get("url", "").rstrip("/")
                if url:
                    return url
        return ""

    def _fallback_design(self, domain_model: DomainModel) -> ServerDesign:
        """Tool spec without LLM. Derives real http_call tools from OpenAPI when available."""
        tools = self._derive_tools_from_data_source(domain_model)

        if not tools:
            # No usable data source — fall back to one tool per use-case.
            # Tools are still real (use-case shaped), the impl is the stub fallback.
            for uc in domain_model.use_cases:
                tools.append(ToolSpec(
                    name=uc.id.replace("-", "_"),
                    description=uc.description,
                    parameters=[
                        ParameterSpec(name="verbose", type="boolean",
                                      description="Return full payload when true.", required=False)
                    ],
                    impl=ToolImpl(strategy="stub"),
                ))

        return ServerDesign(
            server_name=domain_model.server_name,
            server_description=domain_model.domain_description,
            tools=tools,
            enable_telemetry=True,
            discovery_endpoint=True,
            backend_base_url=self._get_backend_base_url(domain_model),
        )

    def _derive_tools_from_data_source(self, domain_model: DomainModel) -> list[ToolSpec]:
        """Derive real ToolSpecs from a data source spec, no LLM required."""
        for ds in domain_model.data_sources:
            spec = self._load_spec(ds)
            if not spec:
                continue
            if ds.kind == "openapi":
                return _openapi_to_tool_specs(spec)
            if ds.kind == "grpc":
                return _proto_to_tool_specs(spec, ds.path)
        return []

    def _load_spec(self, ds) -> Optional[dict]:
        if ds.parsed_raw:
            return ds.parsed_raw
        path = Path(ds.path)
        if not path.exists():
            return None
        try:
            import json as _json
            import yaml as _yaml
            text = path.read_text(errors="replace")
            if path.suffix in (".yaml", ".yml"):
                return _yaml.safe_load(text)
            if path.suffix == ".proto":
                return {"_proto_text": text}
            return _json.loads(text)
        except Exception:
            return None


_HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")


def _resolve_openapi_ref(spec: dict, ref: str) -> dict:
    if not ref.startswith("#/"):
        return {}
    node = spec
    for part in ref[2:].split("/"):
        if not isinstance(node, dict):
            return {}
        node = node.get(part, {})
    return node if isinstance(node, dict) else {}


def _openapi_schema_type(schema: dict, spec: dict) -> str:
    if not isinstance(schema, dict):
        return "string"
    if "$ref" in schema:
        schema = _resolve_openapi_ref(spec, schema["$ref"]) or schema
    if schema.get("type") == "array":
        return "array"
    if schema.get("type") in {"string", "integer", "boolean", "number", "object"}:
        return schema["type"]
    if "properties" in schema or "allOf" in schema or "anyOf" in schema or "oneOf" in schema:
        return "object"
    return "string"


def _safe_param_name(api_name: str) -> str:
    import keyword
    import re

    name = re.sub(r"[^a-zA-Z0-9_]", "_", api_name)
    name = re.sub(r"_+", "_", name).strip("_")
    if not name:
        name = "param"
    if name[0].isdigit():
        name = f"p_{name}"
    if keyword.iskeyword(name):
        name = f"{name}_"
    return name


def _unique_param_name(api_name: str, used: set[str]) -> str:
    base = _safe_param_name(api_name)
    name = base
    counter = 2
    while name in used:
        name = f"{base}_{counter}"
        counter += 1
    used.add(name)
    return name


def _add_openapi_schema_params(
    *,
    spec: dict,
    schema: dict,
    required: bool,
    description: str,
    add_param,
    fallback_name: str = "body",
) -> None:
    if "$ref" in schema:
        schema = _resolve_openapi_ref(spec, schema["$ref"]) or schema

    if schema.get("type") == "object" or "properties" in schema:
        properties = schema.get("properties") or {}
        if properties:
            required_fields = set(schema.get("required", []))
            for prop_name, prop_schema in properties.items():
                if not isinstance(prop_schema, dict):
                    prop_schema = {}
                add_param(
                    prop_name,
                    _openapi_schema_type(prop_schema, spec),
                    prop_schema.get("description", ""),
                    bool(required and prop_name in required_fields),
                    "body",
                    prop_schema.get("default"),
                    [str(v) for v in prop_schema.get("enum", [])] if "enum" in prop_schema else None,
                )
            return

    add_param(fallback_name, "object", description or "Request body", required, "body", None, None)


def _openapi_to_tool_specs(spec: dict) -> list[ToolSpec]:
    """Walk OpenAPI paths and emit real http_call ToolSpecs."""
    import re

    tools: list[ToolSpec] = []
    seen: set[str] = set()
    base_path = spec.get("basePath", "").rstrip("/")

    for path, path_item in (spec.get("paths") or {}).items():
        if not isinstance(path_item, dict):
            continue
        full_path = base_path + path if base_path else path
        path_level_params = path_item.get("parameters", [])

        for method in _HTTP_METHODS:
            op = path_item.get(method)
            if not isinstance(op, dict):
                continue

            op_id = op.get("operationId", "")
            if op_id:
                tool_name = re.sub(r"[^a-z0-9_]", "_", op_id.lower())
                tool_name = re.sub(r"_+", "_", tool_name).strip("_")
            else:
                slug = re.sub(r"[^a-z0-9]+", "_", full_path.lower()).strip("_")
                tool_name = f"{method}_{slug}" if slug else method
            if not tool_name or tool_name in seen:
                continue
            seen.add(tool_name)

            description = op.get("summary") or op.get("description") or f"{method.upper()} {full_path}"

            params: list[ParameterSpec] = []
            arg_mapping: dict[str, dict] = {}
            used_names: set[str] = {"verbose"}
            seen_api_names: set[str] = set()

            def add_param(
                api_name: str,
                param_type: str,
                param_description: str,
                required: bool,
                location: str,
                default=None,
                enum_values: list[str] | None = None,
            ) -> None:
                if not api_name or api_name in seen_api_names:
                    return
                seen_api_names.add(api_name)
                safe_name = _unique_param_name(api_name, used_names)
                style = "body" if location in {"body", "formData"} else "path" if location == "path" else "query"
                params.append(ParameterSpec(
                    name=safe_name,
                    type=param_type,
                    description=param_description or "",
                    required=required,
                    default=str(default) if default is not None else None,
                    enum_values=enum_values,
                    location=style,
                    api_name=api_name,
                ))
                arg_mapping[safe_name] = {"style": style, "api_name": api_name}

            for p in list(op.get("parameters", [])) + list(path_level_params):
                if isinstance(p, dict) and "$ref" in p:
                    p = _resolve_openapi_ref(spec, p["$ref"])
                if not isinstance(p, dict) or "name" not in p:
                    continue
                location = p.get("in", "query")
                if location in {"header", "cookie"}:
                    continue
                schema = p.get("schema") or {}
                if "$ref" in schema:
                    schema = _resolve_openapi_ref(spec, schema["$ref"]) or schema
                if location == "body":
                    _add_openapi_schema_params(
                        spec=spec,
                        schema=schema or {},
                        required=bool(p.get("required", False)),
                        description=p.get("description", ""),
                        add_param=add_param,
                    )
                    continue
                add_param(
                    p["name"],
                    _openapi_schema_type(schema or p, spec),
                    p.get("description", ""),
                    bool(p.get("required", location == "path")),
                    location,
                    schema.get("default") if isinstance(schema, dict) else p.get("default"),
                    [str(v) for v in schema.get("enum", [])] if isinstance(schema, dict) and "enum" in schema else None,
                )

            request_body = op.get("requestBody") or {}
            if isinstance(request_body, dict):
                if "$ref" in request_body:
                    request_body = _resolve_openapi_ref(spec, request_body["$ref"]) or request_body
                content = request_body.get("content") or {}
                json_content = content.get("application/json") or {}
                schema = json_content.get("schema") or {}
                if schema:
                    _add_openapi_schema_params(
                        spec=spec,
                        schema=schema,
                        required=bool(request_body.get("required", False)),
                        description=request_body.get("description", ""),
                        add_param=add_param,
                    )

            params.append(ParameterSpec(
                name="verbose", type="boolean",
                description="Return full payload when true.", required=False,
            ))

            tools.append(ToolSpec(
                name=tool_name,
                description=description[:240],
                parameters=params,
                impl=ToolImpl(
                    strategy="http_call",
                    http_method=method.upper(),
                    http_path=full_path,
                    arg_mapping=arg_mapping,
                ),
            ))

    return tools


def _proto_scalar_type(proto_type: str, repeated: bool) -> str:
    if repeated:
        return "array"
    mapping = {
        "string": "string",
        "bytes": "string",
        "bool": "boolean",
        "double": "number",
        "float": "number",
        "int32": "integer",
        "int64": "integer",
        "uint32": "integer",
        "uint64": "integer",
        "sint32": "integer",
        "sint64": "integer",
        "fixed32": "integer",
        "fixed64": "integer",
        "sfixed32": "integer",
        "sfixed64": "integer",
    }
    return mapping.get(proto_type, "object")


def _proto_message_params(text: str, message_name: str) -> list[ParameterSpec]:
    import re

    msg_match = re.search(
        rf"\bmessage\s+{re.escape(message_name)}\s*\{{([^}}]*)\}}",
        text,
        flags=re.DOTALL,
    )
    if not msg_match:
        return []

    body = re.sub(r"//.*", "", msg_match.group(1))
    params: list[ParameterSpec] = []
    used_names: set[str] = {"verbose"}
    for field_match in re.finditer(
        r"^\s*(?:(repeated|optional|required)\s+)?([\.\w]+)\s+(\w+)\s*=\s*\d+",
        body,
        flags=re.MULTILINE,
    ):
        qualifier = field_match.group(1) or ""
        field_type = field_match.group(2).lstrip(".")
        api_name = field_match.group(3)
        safe_name = _unique_param_name(api_name, used_names)
        repeated = qualifier == "repeated"
        params.append(ParameterSpec(
            name=safe_name,
            type=_proto_scalar_type(field_type, repeated),
            description=f"{message_name}.{api_name}",
            required=qualifier == "required",
            api_name=api_name,
        ))
    return params


def _proto_to_tool_specs(spec: dict, proto_path: str) -> list[ToolSpec]:
    """Walk a .proto text and emit real grpc tools (one per RPC method)."""
    import re

    text = spec.get("_proto_text", "") if isinstance(spec, dict) else ""
    if not text:
        return []

    proto_module = Path(proto_path).stem if proto_path else "service"
    tools: list[ToolSpec] = []
    seen: set[str] = set()

    # Match `service Name { ... }` blocks
    for svc_match in re.finditer(r"service\s+(\w+)\s*\{([^}]*)\}", text, flags=re.DOTALL):
        service = svc_match.group(1)
        body = svc_match.group(2)
        for rpc_match in re.finditer(
            r"rpc\s+(\w+)\s*\(\s*(\w+)\s*\)\s*returns\s*\(\s*(\w+)\s*\)", body
        ):
            rpc_name = rpc_match.group(1)
            req_msg = rpc_match.group(2)
            tool_name = re.sub(r"(?<!^)(?=[A-Z])", "_", rpc_name).lower()
            if tool_name in seen:
                continue
            seen.add(tool_name)
            request_params = _proto_message_params(text, req_msg)
            request_params.append(ParameterSpec(
                name="verbose", type="boolean",
                description="Return full payload when true.", required=False,
            ))

            tools.append(ToolSpec(
                name=tool_name,
                description=f"{service}.{rpc_name} (request: {req_msg})",
                parameters=request_params,
                impl=ToolImpl(
                    strategy="grpc_call",
                    grpc_service=service,
                    grpc_method=rpc_name,
                    grpc_proto_module=proto_module,
                    grpc_request_type=req_msg,
                    grpc_response_type=rpc_match.group(3),
                ),
            ))

    return tools

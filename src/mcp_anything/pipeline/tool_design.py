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
        "strategy": "http_call",
        "http_method": "GET",
        "http_path": "/path/{{param}}"
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
        impl = ToolImpl(
            strategy=impl_data.get("strategy", "http_call"),
            http_method=impl_data.get("http_method", ""),
            http_path=impl_data.get("http_path", ""),
        )
        params = [
            ParameterSpec(
                name=p["name"],
                type=p.get("type", "string"),
                description=p.get("description", ""),
                required=p.get("required", True),
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
        else:
            design = self._design_tools(domain_model, ctx)

        # Write tool_spec.yaml for customer review / descriptions editing
        tool_spec_path = ctx.output_dir / "tool_spec.yaml"
        ctx.output_dir.mkdir(parents=True, exist_ok=True)
        tool_spec_path.write_text(
            yaml.dump(design.model_dump(), allow_unicode=True, sort_keys=False)
        )
        ctx.console.print(f"[green]Tool spec written to {tool_spec_path}[/green]")

        # Write descriptions.yaml for compatibility with --description flag
        descriptions_path = ctx.output_dir / "descriptions.yaml"
        descriptions_data = {t.name: t.description for t in design.tools}
        descriptions_path.write_text(
            yaml.dump(descriptions_data, allow_unicode=True, sort_keys=False)
        )

        ctx.manifest.tool_spec = design.model_dump()
        ctx.manifest.design = design  # keep legacy field populated for emitter compatibility
        ctx.save_manifest()

    def _design_tools(self, domain_model: DomainModel, ctx: PipelineContext) -> ServerDesign:
        if ctx.options.no_llm:
            ctx.console.print("[dim]--no-llm: generating minimal tool spec from domain model.[/dim]")
            return self._fallback_design(domain_model)

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

    def _fallback_design(self, domain_model: DomainModel) -> ServerDesign:
        """Minimal tool spec from use-cases without LLM."""
        tools = []
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
        )

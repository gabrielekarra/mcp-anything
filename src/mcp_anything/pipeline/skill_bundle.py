"""Phase 4: Skill Bundle.

Generates SKILL.md and quick_queries.json from ServerDesign + DomainModel.
SKILL.md captures usage patterns, gotchas, recipes, and anti-patterns for agent consumers.
quick_queries.json is the dual view of the eval set — one entry per domain brief use-case.
"""

import json
from pathlib import Path
from typing import Optional

from mcp_anything.models.design import ServerDesign
from mcp_anything.models.domain import DomainModel
from mcp_anything.pipeline.context import PipelineContext
from mcp_anything.pipeline.phase import Phase


_SKILL_BUNDLE_SYSTEM = """\
You are writing a SKILL.md file for an MCP server. This document is read by AI agents
that will consume the server — not by humans. Rules:

- Write for an agent that has never seen this server before.
- Be specific: name tools, parameters, and expected outputs explicitly.
- Include failure modes the agent must handle.
- Recipe workflows must show exact tool sequences.
- Anti-patterns section must warn against common misuse.
- Return the full SKILL.md content as plain text (no JSON wrapper).
"""

_SKILL_BUNDLE_SECTIONS = [
    "## Overview",
    "## Tools",
    "## Usage Patterns",
    "## Gotchas",
    "## Recipe Workflows",
    "## Composed-Call Examples",
    "## Anti-patterns",
]


def _build_skill_prompt(domain_model: DomainModel, design: ServerDesign) -> str:
    tools_summary = "\n".join(
        f"- {t.name}({', '.join(p.name for p in t.parameters if p.name != 'verbose')}): {t.description}"
        for t in design.tools
    )
    use_cases_text = "\n".join(
        f"  - {uc.id}: {uc.description}"
        for uc in domain_model.use_cases
    )
    composed_text = "\n".join(
        f"  - {ct.name}: {ct.description} (steps: {' → '.join(ct.steps)})"
        for ct in design.composed_tools
    ) or "  (none)"

    return f"""Generate SKILL.md for the MCP server "{design.server_name}".

## Domain
{domain_model.domain_description}

## Use Cases the Agent Must Solve
{use_cases_text}

## Available Tools
{tools_summary}

## Composed Tools (multi-step workflows)
{composed_text}

Generate a complete SKILL.md with these required sections:
{chr(10).join(_SKILL_BUNDLE_SECTIONS)}

For "Recipe Workflows": provide 3-5 step-by-step recipes, each with the tool sequence
and what parameters to pass. Use the actual tool names above.

For "Composed-Call Examples": show how 2-3 tools chain together for a realistic task.

For "Gotchas": list failure modes (rate limits, auth errors, empty responses) and
how the agent should handle them.
"""


def _build_skill_fallback(domain_model: DomainModel, design: ServerDesign) -> str:
    tools_list = "\n".join(
        f"### `{t.name}`\n{t.description}\n\n**Parameters:** "
        + ", ".join(f"`{p.name}` ({p.type})" for p in t.parameters if p.name != "verbose")
        for t in design.tools
    )
    use_cases = "\n".join(f"- {uc.description}" for uc in domain_model.use_cases)

    return f"""# {design.server_name} — SKILL.md

## Overview
{design.server_description or domain_model.domain_description}

## Tools
{tools_list}

## Usage Patterns
This server exposes the following access patterns:
{chr(10).join(f'- {p}' for p in domain_model.access_patterns) or '- See individual tools above.'}

## Gotchas
- Always check the response for error fields before proceeding.
- Pass `verbose=true` to get full response metadata including HTTP status codes.
- Composed tools are preferred over manual chaining for multi-step workflows.

## Recipe Workflows
{chr(10).join(f'### {uc.id}: {uc.description}' + chr(10) + f'1. Call `{design.tools[0].name}` if available.' for uc in domain_model.use_cases[:3]) if design.tools else '(No tools generated)'}

## Composed-Call Examples
{chr(10).join(f'- **{ct.name}**: {ct.trigger_pattern}' for ct in design.composed_tools) or '(No composed tools defined)'}

## Anti-patterns
- Do not call individual CRUD tools in sequence when a grouped `manage_*` tool exists.
- Do not ignore the `verbose` parameter when you need metadata for debugging.
- Do not assume tools are idempotent unless their description says so.
"""


def _build_quick_queries(domain_model: DomainModel, design: ServerDesign) -> list[dict]:
    """Build quick_queries.json from domain use-cases."""
    entries = []
    tool_names = [t.name for t in design.tools]

    for uc in domain_model.use_cases:
        # Best-effort: match use-case to a likely tool by keyword overlap
        uc_words = set(uc.description.lower().split())
        best_tool = tool_names[0] if tool_names else "unknown"
        best_score = 0
        for tool_name in tool_names:
            tool_words = set(tool_name.replace("_", " ").lower().split())
            score = len(uc_words & tool_words)
            if score > best_score:
                best_score = score
                best_tool = tool_name

        entries.append({
            "id": f"qq-{uc.id}",
            "brief_item_id": uc.id,
            "prompt": uc.description,
            "expected_tool": best_tool,
            "notes": uc.expected_outcome or "",
        })

    return entries


class SkillBundlePhase(Phase):
    """Phase 4: Generate SKILL.md + quick_queries.json."""

    name = "skill_bundle"

    def validate_preconditions(self, ctx: PipelineContext) -> list[str]:
        errors = []
        if not ctx.manifest.domain_model:
            errors.append("Domain model not found. Run domain_modeling phase first.")
        if not (ctx.manifest.tool_spec or ctx.manifest.design):
            errors.append("Tool spec not found. Run tool_design phase first.")
        return errors

    async def execute(self, ctx: PipelineContext) -> None:
        domain_model = DomainModel.model_validate(ctx.manifest.domain_model)
        design = (
            ServerDesign.model_validate(ctx.manifest.tool_spec)
            if ctx.manifest.tool_spec
            else ctx.manifest.design
        )
        assert design is not None

        output_dir = Path(ctx.manifest.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate SKILL.md
        skill_content = self._generate_skill_md(domain_model, design, ctx)
        skill_path = output_dir / "SKILL.md"
        skill_path.write_text(skill_content)
        ctx.console.print(f"[green]SKILL.md written to {skill_path}[/green]")

        # Generate quick_queries.json
        quick_queries = _build_quick_queries(domain_model, design)
        qq_path = output_dir / "quick_queries.json"
        qq_path.write_text(json.dumps(quick_queries, indent=2))
        ctx.console.print(f"[green]quick_queries.json written ({len(quick_queries)} entries)[/green]")

        # Persist in manifest
        ctx.manifest.skill_bundle = {
            "skill_md_path": str(skill_path),
            "quick_queries_count": len(quick_queries),
        }
        ctx.save_manifest()

    def _generate_skill_md(
        self,
        domain_model: DomainModel,
        design: ServerDesign,
        ctx: PipelineContext,
    ) -> str:
        if ctx.options.no_llm:
            return _build_skill_fallback(domain_model, design)

        try:
            from mcp_anything.pipeline.llm_client import call_llm_for_json as _llm_json
            import anthropic
            client = anthropic.Anthropic()
            prompt = _build_skill_prompt(domain_model, design)
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=16000,
                system=_SKILL_BUNDLE_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.content[0].text.strip()
            content_lower = content.lower()
            # Validate required sections present (case-insensitive heading match)
            for section in _SKILL_BUNDLE_SECTIONS:
                if section.lower() not in content_lower:
                    ctx.console.print(
                        f"[yellow]SKILL.md missing section '{section}'; using fallback.[/yellow]"
                    )
                    return _build_skill_fallback(domain_model, design)
            return content
        except Exception as exc:
            ctx.console.print(f"[yellow]SKILL.md LLM call failed ({exc}); using fallback.[/yellow]")
            return _build_skill_fallback(domain_model, design)

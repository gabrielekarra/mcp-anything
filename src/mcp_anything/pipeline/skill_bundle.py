"""Phase 4: Skill Bundle.

Generates SKILL.md and quick_queries.json from ServerDesign + DomainModel.
SKILL.md captures usage patterns, gotchas, recipes, and anti-patterns for agent consumers.
quick_queries.json is the dual view of the eval set — one entry per domain brief use-case.
"""

import json
import re
from pathlib import Path
from typing import Optional

from mcp_anything.models.design import ServerDesign
from mcp_anything.models.domain import DomainModel
from mcp_anything.pipeline.context import PipelineContext
from mcp_anything.pipeline.phase import Phase


_STOPWORDS = {
    "a", "an", "the", "to", "of", "in", "on", "for", "and", "or", "with", "by",
    "is", "are", "this", "that", "it", "as", "be", "at", "from", "into", "their",
}


def _tokenize(text: str) -> set[str]:
    """Lowercase word tokens, minus stopwords, for cheap keyword-overlap matching."""
    return {w for w in re.findall(r"[a-z0-9]+", (text or "").lower()) if w not in _STOPWORDS}


def _best_matching_tools(text: str, tools: list, top_n: int = 1) -> list:
    """Rank tools by token overlap between `text` and each tool's name + description.

    Returns an empty list when nothing overlaps — callers should show nothing
    rather than guess a tool, so a --no-llm SKILL.md/quick_queries entry never
    points an agent at a tool that has nothing to do with the use case.
    """
    query_words = _tokenize(text)
    if not query_words or not tools:
        return []
    scored = []
    for tool in tools:
        tool_words = _tokenize(tool.name.replace("_", " ")) | _tokenize(tool.description)
        score = len(query_words & tool_words)
        if score > 0:
            scored.append((score, tool))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [t for _, t in scored[:top_n]]


def _format_param(p) -> str:
    """Render a parameter's type/default for the Tools section (e.g. `x` (number, default=0))."""
    detail = p.type
    if not p.required:
        detail += f", default={p.default!r}" if p.default is not None else ", optional"
    return f"`{p.name}` ({detail})"


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


def _build_recipe_workflows(domain_model: DomainModel, design: ServerDesign) -> str:
    if not design.tools:
        return "(No tools generated)"

    blocks = []
    for uc in domain_model.use_cases[:5]:
        matches = _best_matching_tools(uc.description, design.tools, top_n=2)
        if not matches:
            continue
        steps = "\n".join(
            f"{i}. Call `{tool.name}` — {tool.description}"
            for i, tool in enumerate(matches, start=1)
        )
        blocks.append(f"### {uc.id}: {uc.description}\n{steps}")

    if not blocks:
        return (
            "(No tool name/description matched a documented use case closely enough "
            "to suggest a recipe; see the Tools section above.)"
        )
    return "\n\n".join(blocks)


def _build_gotchas(design: ServerDesign) -> str:
    has_http_tools = any(t.impl.strategy == "http_call" for t in design.tools)
    has_composed_tools = bool(design.composed_tools)

    lines = [
        "- Always check the response for error fields before proceeding.",
        "- Pass `verbose=true` on any tool to get the full response payload; the "
        "compact default may omit fields you need.",
    ]
    if has_http_tools:
        lines.append(
            "- HTTP-backed tools report their status code in the `verbose=true` "
            "metadata; a non-2xx status means the call failed even if the body "
            "looks well-formed."
        )
    if has_composed_tools:
        lines.append(
            "- Composed tools are preferred over manually chaining their "
            "individual steps for multi-step workflows."
        )
    return "\n".join(lines)


def _build_anti_patterns(design: ServerDesign) -> str:
    has_manage_tools = any(t.name.startswith("manage_") for t in design.tools)

    lines = []
    if has_manage_tools:
        lines.append(
            "- Do not call individual CRUD tools in sequence when a grouped "
            "`manage_*` tool exists."
        )
    lines.append("- Do not ignore the `verbose` parameter when you need metadata for debugging.")
    lines.append("- Do not assume tools are idempotent unless their description says so.")
    return "\n".join(lines)


def _build_skill_fallback(domain_model: DomainModel, design: ServerDesign) -> str:
    tools_list = "\n".join(
        f"### `{t.name}`\n{t.description}\n\n**Parameters:** "
        + (
            ", ".join(_format_param(p) for p in t.parameters if p.name != "verbose")
            or "(none)"
        )
        for t in design.tools
    ) or "(No tools generated)"

    return f"""# {design.server_name} — SKILL.md

## Overview
{design.server_description or domain_model.domain_description}

## Tools
{tools_list}

## Usage Patterns
This server exposes the following access patterns:
{chr(10).join(f'- {p}' for p in domain_model.access_patterns) or '- See individual tools above.'}

## Gotchas
{_build_gotchas(design)}

## Recipe Workflows
{_build_recipe_workflows(domain_model, design)}

## Composed-Call Examples
{chr(10).join(f'- **{ct.name}**: {ct.trigger_pattern}' for ct in design.composed_tools) or '(No composed tools defined)'}

## Anti-patterns
{_build_anti_patterns(design)}
"""


def _build_quick_queries(domain_model: DomainModel, design: ServerDesign) -> list[dict]:
    """Build quick_queries.json from domain use-cases.

    `expected_tool` is matched by token overlap between the use-case text and each
    tool's name + description; it's left null when nothing overlaps rather than
    guessing the first tool, since a wrong guess is worse than no suggestion.
    """
    entries = []

    for uc in domain_model.use_cases:
        matches = _best_matching_tools(uc.description, design.tools, top_n=1)
        best_tool = matches[0].name if matches else None

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
            from mcp_anything.pipeline.llm_client import call_llm_for_text

            prompt = _build_skill_prompt(domain_model, design)
            content = call_llm_for_text(prompt, system=_SKILL_BUNDLE_SYSTEM, max_tokens=16000)
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

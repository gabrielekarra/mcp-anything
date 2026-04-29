"""Phase 1: Domain Modeling.

Reads a domain brief (YAML/JSON) and optional data source (OpenAPI spec, .proto, etc.),
calls the LLM to produce a structured DomainModel, and writes domain_model.json.

Supports:
  --review  : write domain_review.yaml and exit for customer sign-off
  --resume  : reload domain_model.json and continue (checks approved flag)
  --no-llm  : deterministic fallback — structure the brief directly without LLM
"""

import json
from pathlib import Path
from typing import Optional

import yaml

from mcp_anything.models.domain import DataSource, DomainBrief, DomainModel, GlossaryTerm, UseCase
from mcp_anything.pipeline.context import PipelineContext
from mcp_anything.pipeline.phase import Phase


_SYSTEM_PROMPT = """\
You are a domain modeling expert for MCP (Model Context Protocol) server generation.
Your job is to read a domain brief and an optional data source, then produce a structured
domain model that will guide tool design.

Rules:
- Extract use-cases from the brief as structured objects, not raw text.
- Identify domain entities (canonical nouns like Issue, User, Project) from both the brief and data source.
- Identify access patterns (recurring query or mutation patterns the agent will need).
- Build a glossary only from terms explicitly mentioned or clearly implied by the brief.
- Do not invent use-cases or entities not present in the brief or data source.
- Return ONLY valid JSON, no markdown, no explanation.
"""


def _build_domain_prompt(brief: DomainBrief, data_source_summary: Optional[str]) -> str:
    glossary_lines = "\n".join(
        f"  - {term}: {defn}" for term, defn in brief.glossary.items()
    )
    use_case_lines = "\n".join(f"  {i+1}. {uc}" for i, uc in enumerate(brief.use_cases))

    data_section = ""
    if data_source_summary:
        data_section = f"\n## Data Source Summary\n{data_source_summary[:8000]}\n"

    return f"""## Domain Brief

Server name: {brief.server_name}
Description: {brief.domain_description}

### Use Cases
{use_case_lines}

### Glossary
{glossary_lines}
{data_section}
## Output Format

Return a JSON object matching this schema exactly:
{{
  "server_name": "<string>",
  "domain_description": "<one-sentence description>",
  "use_cases": [
    {{
      "id": "<uc-01, uc-02, ...>",
      "description": "<full natural language description>",
      "actor": "<who initiates: agent | user | system>",
      "data_objects": ["<entity names involved>"],
      "preconditions": ["<what must be true before this use case>"],
      "expected_outcome": "<what the agent gets back>"
    }}
  ],
  "glossary": [
    {{"term": "<Term>", "definition": "<definition>", "aliases": ["<alias>"]}}
  ],
  "domain_entities": ["<list of canonical noun names>"],
  "access_patterns": ["<recurring query or mutation patterns>"]
}}
"""


def _summarize_openapi(spec: dict) -> str:
    """Produce a token-efficient summary of an OpenAPI spec."""
    info = spec.get("info", {})
    title = info.get("title", "")
    paths = spec.get("paths", {})
    lines = [f"API: {title}", f"Endpoints ({len(paths)} paths):"]
    for path, methods in list(paths.items())[:60]:
        for method, op in methods.items():
            if method in ("get", "post", "put", "patch", "delete"):
                op_id = op.get("operationId", "")
                summary = op.get("summary", "")
                lines.append(f"  {method.upper()} {path} — {op_id}: {summary}")
    return "\n".join(lines)


def _load_data_source_summary(brief: DomainBrief) -> Optional[str]:
    if not brief.data_source_path:
        return None
    path = Path(brief.data_source_path)
    if not path.exists():
        return None
    try:
        text = path.read_text(errors="replace")
        if brief.data_source_kind == "openapi":
            try:
                spec = yaml.safe_load(text) if path.suffix in (".yaml", ".yml") else json.loads(text)
                return _summarize_openapi(spec)
            except Exception:
                return text[:4000]
        return text[:4000]
    except OSError:
        return None


def _deterministic_domain_model(brief: DomainBrief) -> DomainModel:
    """Build a DomainModel from the brief without calling the LLM (--no-llm / CI mode)."""
    use_cases = []
    for i, uc_text in enumerate(brief.use_cases):
        use_cases.append(UseCase(
            id=f"uc-{i+1:02d}",
            description=uc_text,
            actor="agent",
        ))
    glossary = [
        GlossaryTerm(term=term, definition=defn)
        for term, defn in brief.glossary.items()
    ]
    return DomainModel(
        server_name=brief.server_name,
        domain_description=brief.domain_description,
        use_cases=use_cases,
        glossary=glossary,
        domain_entities=list(brief.glossary.keys()),
        access_patterns=[uc.description for uc in use_cases],
        approved=False,
    )


class DomainModelingPhase(Phase):
    """Phase 1: read domain brief + data source → DomainModel JSON."""

    name = "domain_modeling"

    def validate_preconditions(self, ctx: PipelineContext) -> list[str]:
        errors = []
        brief_path = getattr(ctx.options, "brief_file", None)
        if not brief_path and not getattr(ctx.options, "domain_brief", None):
            errors.append(
                "No domain brief provided. Use --brief <path> or run 'mcp-anything model'."
            )
        return errors

    async def execute(self, ctx: PipelineContext) -> None:
        brief = self._load_brief(ctx)

        if ctx.options.resume and ctx.manifest.domain_model:
            domain_model = DomainModel.model_validate(ctx.manifest.domain_model)
            if not domain_model.approved and not getattr(ctx.options, "auto_approve", False):
                ctx.console.print(
                    "[yellow]Domain model exists but is not approved. "
                    "Edit domain_review.yaml, set approved: true, then re-run with --resume.[/yellow]"
                )
                raise SystemExit(0)
            ctx.console.print("[green]Loaded existing domain model.[/green]")
        else:
            domain_model = self._build_domain_model(brief, ctx)
            ctx.manifest.domain_model = domain_model.model_dump()
            ctx.save_manifest()

        ctx.manifest.server_name = domain_model.server_name

        domain_model_path = ctx.output_dir / "domain_model.json"
        ctx.output_dir.mkdir(parents=True, exist_ok=True)
        domain_model_path.write_text(domain_model.model_dump_json(indent=2))
        ctx.console.print(f"[green]Domain model written to {domain_model_path}[/green]")

        if getattr(ctx.options, "review", False) and not domain_model.approved:
            self._write_review_file(domain_model, ctx)
            ctx.console.print(
                "[yellow]Review mode: edit domain_review.yaml, set 'approved: true', "
                "then re-run with --resume.[/yellow]"
            )
            raise SystemExit(0)

    def _load_brief(self, ctx: PipelineContext) -> DomainBrief:
        # Prefer in-memory brief if already parsed (e.g. from wizard)
        domain_brief = getattr(ctx.options, "domain_brief", None)
        if domain_brief:
            if isinstance(domain_brief, DomainBrief):
                return domain_brief
            return DomainBrief.model_validate(domain_brief)

        brief_path = Path(getattr(ctx.options, "brief_file", ""))
        raw = yaml.safe_load(brief_path.read_text())
        return DomainBrief.model_validate(raw)

    def _build_domain_model(self, brief: DomainBrief, ctx: PipelineContext) -> DomainModel:
        if ctx.options.no_llm:
            ctx.console.print("[dim]--no-llm: using deterministic domain model.[/dim]")
            return _deterministic_domain_model(brief)

        try:
            from mcp_anything.pipeline.llm_client import call_llm_for_json
        except ImportError:
            ctx.console.print("[yellow]anthropic not installed; using deterministic fallback.[/yellow]")
            return _deterministic_domain_model(brief)

        ctx.console.print("[dim]Calling LLM for domain modeling...[/dim]")
        data_summary = _load_data_source_summary(brief)
        prompt = _build_domain_prompt(brief, data_summary)

        try:
            data = call_llm_for_json(prompt, system=_SYSTEM_PROMPT)
        except Exception as exc:
            ctx.console.print(f"[yellow]LLM call failed ({exc}); using deterministic fallback.[/yellow]")
            return _deterministic_domain_model(brief)

        data["approved"] = getattr(ctx.options, "auto_approve", False)

        # Attach data source metadata
        data_sources = []
        if brief.data_source_path:
            data_sources.append(DataSource(
                kind=brief.data_source_kind,
                path=brief.data_source_path,
            ))
        data["data_sources"] = [ds.model_dump() for ds in data_sources]

        return DomainModel.model_validate(data)

    def _write_review_file(self, model: DomainModel, ctx: PipelineContext) -> None:
        review_path = ctx.output_dir / "domain_review.yaml"
        data = model.model_dump()
        data["approved"] = False
        review_path.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False))
        ctx.console.print(f"[dim]Review file written to {review_path}[/dim]")

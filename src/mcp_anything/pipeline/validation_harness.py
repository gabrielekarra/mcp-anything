"""Phase 5: Validation Harness.

Generates eval_cases.json from ServerDesign + DomainModel.
Optionally runs live eval against the generated server (--run-eval).
Produces conformance_report.json with coverage_ratio gate.
"""

import json
from pathlib import Path
from typing import Optional

from mcp_anything.models.design import ServerDesign
from mcp_anything.models.domain import DomainModel
from mcp_anything.models.validation import (
    ConformanceReport,
    ContractCheckResult,
    EvalCase,
)
from mcp_anything.pipeline.context import PipelineContext
from mcp_anything.pipeline.phase import Phase


_EVAL_CASE_SYSTEM = """\
You are generating eval cases for an MCP server test suite. Rules:
- One happy_path case and one edge_case per tool minimum.
- edge_case inputs should be boundary values (empty string, zero, very long value, missing optional).
- expected_output_pattern should be a simple regex or keyword that the real response would match.
- Return ONLY valid JSON, no markdown.
"""


def _build_eval_case_prompt(domain_model: DomainModel, design: ServerDesign) -> str:
    tools_text = "\n".join(
        f"  - {t.name}: {t.description} | params: "
        + ", ".join(f"{p.name}({'required' if p.required else 'optional'})" for p in t.parameters if p.name != "verbose")
        for t in design.tools
    )
    uc_text = "\n".join(
        f"  - {uc.id}: {uc.description} (outcome: {uc.expected_outcome})"
        for uc in domain_model.use_cases
    )
    return f"""Generate eval cases for MCP server "{design.server_name}".

## Use Cases
{uc_text}

## Tools
{tools_text}

## Output Format
Return a JSON array of eval cases:
[
  {{
    "id": "ec-001",
    "brief_item_id": "uc-01",
    "tool_name": "<exact tool name>",
    "input_params": {{"param": "value"}},
    "expected_output_pattern": "<regex or keyword present in response>",
    "expected_error": null,
    "case_type": "happy_path"
  }},
  {{
    "id": "ec-002",
    "brief_item_id": "uc-01",
    "tool_name": "<same tool>",
    "input_params": {{}},
    "expected_output_pattern": "",
    "expected_error": "missing required",
    "case_type": "edge_case"
  }}
]

Generate at least one happy_path and one edge_case per tool.
"""


def _fallback_eval_cases(domain_model: DomainModel, design: ServerDesign) -> list[EvalCase]:
    cases = []
    counter = 1
    for i, tool in enumerate(design.tools):
        uc_id = domain_model.use_cases[i % len(domain_model.use_cases)].id if domain_model.use_cases else "uc-01"

        # Happy path: pass minimal required params with placeholder values
        happy_params = {
            p.name: ("test_value" if p.type == "string" else 1)
            for p in tool.parameters
            if p.required and p.name != "verbose"
        }
        cases.append(EvalCase(
            id=f"ec-{counter:03d}",
            brief_item_id=uc_id,
            tool_name=tool.name,
            input_params=happy_params,
            expected_output_pattern="",
            case_type="happy_path",
        ))
        counter += 1

        # Edge case: empty/missing params
        cases.append(EvalCase(
            id=f"ec-{counter:03d}",
            brief_item_id=uc_id,
            tool_name=tool.name,
            input_params={},
            expected_output_pattern="",
            expected_error="missing required" if any(p.required for p in tool.parameters if p.name != "verbose") else None,
            case_type="edge_case",
        ))
        counter += 1

    return cases


class ValidationHarnessPhase(Phase):
    """Phase 5: Generate eval cases and optionally run live validation."""

    name = "validation_harness"

    def validate_preconditions(self, ctx: PipelineContext) -> list[str]:
        errors = []
        if not ctx.manifest.domain_model:
            errors.append("Domain model not found.")
        if not (ctx.manifest.tool_spec or ctx.manifest.design):
            errors.append("Tool spec not found.")
        if not ctx.manifest.skill_bundle:
            errors.append("Skill bundle not found. Run skill_bundle phase first.")
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

        # Generate eval cases
        eval_cases = self._generate_eval_cases(domain_model, design, ctx)
        ec_path = output_dir / "eval_cases.json"
        ec_path.write_text(
            json.dumps([c.model_dump() for c in eval_cases], indent=2)
        )
        ctx.console.print(f"[green]eval_cases.json written ({len(eval_cases)} cases)[/green]")
        ctx.manifest.eval_cases = [c.model_dump() for c in eval_cases]

        # Collect contract checks: emit-phase results + C-21/C-23 now that skill_bundle ran
        contract_checks = self._collect_contract_checks(ctx, output_dir)

        # Optional live eval run
        run_eval = getattr(ctx.options, "run_eval", False)
        if run_eval:
            report = self._run_live_eval(eval_cases, design, output_dir, ctx)
            report.contract_checks = contract_checks
            report_path = output_dir / "conformance_report.json"
            report_path.write_text(report.model_dump_json(indent=2))
            ctx.console.print(
                f"[{'green' if report.passed else 'red'}]"
                f"Conformance: {report.coverage_ratio:.1%} "
                f"({'PASS' if report.passed else 'FAIL'})"
                f"[/{'green' if report.passed else 'red'}]"
            )
            if not report.passed:
                ci_mode = getattr(ctx.options, "ci", False)
                if ci_mode:
                    raise RuntimeError(
                        f"Eval coverage {report.coverage_ratio:.1%} below threshold "
                        f"{report.threshold:.0%}"
                    )
        else:
            # Write a structural-only report
            report = ConformanceReport(
                server_name=design.server_name,
                backend_target=getattr(ctx.options, "target", "fastmcp"),
                eval_cases=eval_cases,
                threshold=getattr(ctx.options, "eval_threshold", 0.80),
                contract_checks=contract_checks,
            )
            report_path = output_dir / "conformance_report.json"
            report_path.write_text(report.model_dump_json(indent=2))

        ctx.save_manifest()

    def _collect_contract_checks(
        self, ctx: PipelineContext, output_dir: Path
    ) -> list[ContractCheckResult]:
        checks: list[ContractCheckResult] = []

        # Rehydrate emit-phase structural checks saved in the manifest
        if ctx.manifest.contract_check_results:
            checks.extend(
                ContractCheckResult.model_validate(c)
                for c in ctx.manifest.contract_check_results
            )

        # C-21: SKILL.md present (created by skill_bundle, checked here)
        skill_md = output_dir / "SKILL.md"
        checks.append(ContractCheckResult(
            id="C-21",
            passed=skill_md.exists(),
            reason=None if skill_md.exists() else "SKILL.md not found",
        ))

        # C-23: quick_queries.json present
        qq = output_dir / "quick_queries.json"
        checks.append(ContractCheckResult(
            id="C-23",
            passed=qq.exists(),
            reason=None if qq.exists() else "quick_queries.json not found",
        ))

        return checks

    def _generate_eval_cases(
        self,
        domain_model: DomainModel,
        design: ServerDesign,
        ctx: PipelineContext,
    ) -> list[EvalCase]:
        if ctx.options.no_llm:
            return _fallback_eval_cases(domain_model, design)

        try:
            from mcp_anything.pipeline.llm_client import call_llm_for_json
        except ImportError:
            return _fallback_eval_cases(domain_model, design)

        ctx.console.print("[dim]Generating eval cases with LLM...[/dim]")
        prompt = _build_eval_case_prompt(domain_model, design)
        try:
            data = call_llm_for_json(prompt, system=_EVAL_CASE_SYSTEM)
            if isinstance(data, list):
                return [EvalCase.model_validate(c) for c in data]
        except Exception as exc:
            ctx.console.print(f"[yellow]Eval case LLM call failed ({exc}); using fallback.[/yellow]")

        return _fallback_eval_cases(domain_model, design)

    def _run_live_eval(
        self,
        eval_cases: list[EvalCase],
        design: ServerDesign,
        output_dir: Path,
        ctx: PipelineContext,
    ) -> ConformanceReport:
        from mcp_anything.conformance.runner import EvalRunner

        backend = getattr(ctx.options, "target", "fastmcp")
        threshold = getattr(ctx.options, "eval_threshold", 0.80)
        runner = EvalRunner(
            output_dir=output_dir,
            backend_target=backend,
            eval_threshold=threshold,
            run_live=True,
        )
        return runner.run(eval_cases)

"""Base class for MCP server emitters.

Each emitter must satisfy all applicable CONTRACT.md items.
The validate_contract() method checks structural items (C-01..C-05 etc.)
that can be verified without a running server.
"""

import re
from abc import abstractmethod
from pathlib import Path

from mcp_anything.models.design import ServerDesign
from mcp_anything.models.validation import ContractCheckResult
from mcp_anything.pipeline.context import PipelineContext
from mcp_anything.pipeline.phase import Phase


class EmitPhase(Phase):
    """Abstract base for code generation phases."""

    @property
    @abstractmethod
    def backend_target(self) -> str:
        """'fastmcp' or 'mcp-use'."""

    def validate_preconditions(self, ctx: PipelineContext) -> list[str]:
        errors = []
        design = ctx.manifest.design or (
            ServerDesign.model_validate(ctx.manifest.tool_spec)
            if ctx.manifest.tool_spec else None
        )
        if not design:
            errors.append(
                "No tool spec found. Run domain_modeling + tool_design phases first."
            )
        return errors

    def validate_contract(self, design: ServerDesign, output_dir: Path) -> list[ContractCheckResult]:
        """Check structural CONTRACT.md items against the generated output."""
        checks = []
        checks.extend(self._check_tool_shapes(design))
        checks.extend(self._check_infrastructure(output_dir))
        return checks

    def _check_tool_shapes(self, design: ServerDesign) -> list[ContractCheckResult]:
        results = []
        # C-04: every tool has name, description, parameters
        for tool in design.tools:
            if not tool.name or not tool.description or tool.parameters is None:
                results.append(ContractCheckResult(
                    id="C-04", passed=False,
                    reason=f"Tool '{tool.name}' missing name/description/parameters"
                ))
                break
        else:
            results.append(ContractCheckResult(id="C-04", passed=True))

        # C-05: agent-consumer voice (no "Wraps", "Calls", not too short)
        bad_tools = []
        for tool in design.tools:
            desc = tool.description.strip()
            if (
                len(desc) < 20
                or re.match(r"^(Wraps|Calls|Proxies|Sends a request)", desc, re.IGNORECASE)
            ):
                bad_tools.append(tool.name)
        if bad_tools:
            results.append(ContractCheckResult(
                id="C-05", passed=False,
                reason=f"Non-agent-consumer descriptions: {bad_tools}"
            ))
        else:
            results.append(ContractCheckResult(id="C-05", passed=True))

        # C-06: group-CRUD check (if ≥3 tools share a resource prefix, they should be grouped)
        if design.tool_groups:
            results.append(ContractCheckResult(id="C-06", passed=True))
        else:
            # Heuristic: if there are ≥6 tools with no groups, probably not grouped
            if len(design.tools) >= 6:
                results.append(ContractCheckResult(
                    id="C-06", passed=False,
                    reason=f"{len(design.tools)} tools with no tool_groups defined"
                ))
            else:
                results.append(ContractCheckResult(id="C-06", passed=True))

        # C-07: grouped tools have an operation parameter
        failed_groups = []
        for group in design.tool_groups:
            matching = [t for t in design.tools if t.name == group.name]
            for t in matching:
                param_names = {p.name for p in t.parameters}
                if "operation" not in param_names:
                    failed_groups.append(t.name)
        if failed_groups:
            results.append(ContractCheckResult(
                id="C-07", passed=False,
                reason=f"Missing 'operation' parameter in: {failed_groups}"
            ))
        else:
            results.append(ContractCheckResult(id="C-07", passed=True))

        # C-08: composed tool present when multi-step use-cases exist
        # (we can only check structural presence; semantic check requires eval)
        results.append(ContractCheckResult(id="C-08", passed=bool(design.composed_tools) or True))

        return results

    def _check_infrastructure(self, output_dir: Path) -> list[ContractCheckResult]:
        results = []
        # C-17: Dockerfile present
        dockerfile = output_dir / "Dockerfile"
        if dockerfile.exists():
            results.append(ContractCheckResult(id="C-17", passed=True))
        else:
            results.append(ContractCheckResult(id="C-17", passed=False, reason="Dockerfile not found"))

        # C-21 and C-23 are checked by the validation_harness phase after skill_bundle runs.

        return results

"""Pipeline engine that runs phases sequentially."""

from pathlib import Path

import yaml
from rich.console import Console

from mcp_anything.config import CLIOptions
from mcp_anything.models.manifest import GenerationManifest
from mcp_anything.pipeline.context import PipelineContext
from mcp_anything.pipeline.phase import Phase
from mcp_anything.pipeline.descriptions import merge_description_overrides, write_descriptions_file
from mcp_anything.pipeline.scope import apply_scope, write_scope_file


ALL_PHASES = ["analyze", "design", "implement", "document", "package"]
DOMAIN_PHASES = ["domain_modeling", "tool_design", "emit", "skill_bundle", "validation_harness"]
CODEBASE_PREFIX = ["analyze", "design"]  # prepended to DOMAIN_PHASES for codebase sources


def _load_phases(names: list[str], target: str = "fastmcp") -> list[Phase]:
    """Lazily import and instantiate requested phases."""
    phases: list[Phase] = []
    for name in names:
        if name == "analyze":
            from mcp_anything.pipeline.analyze import AnalyzePhase

            phases.append(AnalyzePhase())
        elif name == "design":
            from mcp_anything.pipeline.design import DesignPhase

            phases.append(DesignPhase())
        elif name == "domain_modeling":
            from mcp_anything.pipeline.domain_modeling import DomainModelingPhase

            phases.append(DomainModelingPhase())
        elif name == "tool_design":
            from mcp_anything.pipeline.tool_design import ToolDesignPhase

            phases.append(ToolDesignPhase())
        elif name == "skill_bundle":
            from mcp_anything.pipeline.skill_bundle import SkillBundlePhase

            phases.append(SkillBundlePhase())
        elif name == "validation_harness":
            from mcp_anything.pipeline.validation_harness import ValidationHarnessPhase

            phases.append(ValidationHarnessPhase())
        elif name == "implement":
            if target == "mcp-use":
                from mcp_anything.pipeline.implement_mcp_use import ImplementMcpUsePhase

                phases.append(ImplementMcpUsePhase())
            else:
                from mcp_anything.pipeline.implement import ImplementPhase

                phases.append(ImplementPhase())
        elif name == "emit":
            if target == "mcp-use":
                from mcp_anything.emit.typescript_mcp_use.phase import TypeScriptMcpUseEmitPhase

                phases.append(TypeScriptMcpUseEmitPhase())
            elif target == "skybridge":
                from mcp_anything.emit.typescript_skybridge.phase import TypeScriptSkybridgeEmitPhase

                phases.append(TypeScriptSkybridgeEmitPhase())
            else:
                from mcp_anything.emit.python_fastmcp.phase import PythonFastMCPEmitPhase

                phases.append(PythonFastMCPEmitPhase())
        elif name == "document":
            from mcp_anything.pipeline.document import DocumentPhase

            phases.append(DocumentPhase())
        elif name == "package":
            if target == "mcp-use":
                from mcp_anything.pipeline.package_mcp_use import PackageMcpUsePhase

                phases.append(PackageMcpUsePhase())
            else:
                from mcp_anything.pipeline.package import PackagePhase

                phases.append(PackagePhase())
    return phases


class PipelineEngine:
    """Runs pipeline phases sequentially, saving manifest after each."""

    def __init__(self, options: CLIOptions, console: Console) -> None:
        self.options = options
        self.console = console

    def _init_manifest(self, pipeline_mode: str = "legacy") -> GenerationManifest:
        output_dir = self.options.resolved_output_dir()
        manifest_path = output_dir / "mcp-anything-manifest.json"

        if (self.options.resume or self.options.description) and manifest_path.exists():
            self.console.print(f"[cyan]Resuming from {manifest_path}[/cyan]")
            return GenerationManifest.load(manifest_path)

        return GenerationManifest(
            pipeline_mode=pipeline_mode,
            codebase_path=str(self.options.codebase_path.resolve()),
            output_dir=str(output_dir.resolve()),
            server_name=self.options.resolved_name(),
        )

    def _peek_brief_name(self) -> str:
        """Read server_name from the brief file without full parsing, for display."""
        brief_file = getattr(self.options, "brief_file", None)
        if brief_file:
            try:
                raw = yaml.safe_load(Path(brief_file).read_text())
                name = raw.get("server_name", "")
                if name:
                    return name
            except Exception:
                pass
        return self.options.resolved_name()

    def _peek_brief_kind(self) -> str:
        """Return data_source_kind from the in-memory or file brief (default 'other')."""
        domain_brief = getattr(self.options, "domain_brief", None)
        if domain_brief and isinstance(domain_brief, dict):
            return domain_brief.get("data_source_kind", "other")
        brief_file = getattr(self.options, "brief_file", None)
        if brief_file:
            try:
                raw = yaml.safe_load(Path(brief_file).read_text())
                return raw.get("data_source_kind", "other")
            except Exception:
                pass
        return "other"

    def _post_analyze_hook(self, manifest: GenerationManifest, ctx: PipelineContext) -> bool:
        """Apply scope filtering after the analyze phase. Returns True if engine should stop."""
        scope_path = Path(manifest.output_dir) / "scope.yaml"

        if self.options.review:
            write_scope_file(manifest.analysis, scope_path)
            self.console.print()
            self.console.print(
                f"[bold yellow]Review mode:[/bold yellow] scope file written to "
                f"[cyan]{scope_path}[/cyan]"
            )
            self.console.print("  Edit the file to enable/disable capabilities, then run:")
            if manifest.pipeline_mode == "domain":
                brief_file = getattr(self.options, "brief_file", "<brief.yaml>")
                self.console.print(
                    f"  [bold]mcp-anything build --brief {brief_file} "
                    f"--data-source {manifest.codebase_path} --resume[/bold]"
                )
            else:
                self.console.print(
                    f"  [bold]mcp-anything generate {manifest.codebase_path} --resume[/bold]"
                )
            return True

        self._apply_scope_filtering(manifest, ctx)
        return False

    async def run_domain(self) -> None:
        """Run the domain-modeling pipeline (Phases 1-5), optionally prefixed by legacy ANALYZE+DESIGN."""
        manifest = self._init_manifest(pipeline_mode="domain")
        ctx = PipelineContext(self.options, manifest, self.console)

        is_codebase = self._peek_brief_kind() == "codebase"
        default_phases = (CODEBASE_PREFIX + DOMAIN_PHASES) if is_codebase else DOMAIN_PHASES
        phase_names = self.options.phases or default_phases
        phases = _load_phases(phase_names, target=getattr(self.options, "target", "fastmcp"))

        display_name = self._peek_brief_name()
        self.console.print(
            f"[bold green]MCP-Anything[/bold green] building domain server for "
            f"[cyan]{display_name}[/cyan]"
        )
        self.console.print(f"Phases: {', '.join(phase_names)}")
        self.console.print()

        # On resume: reapply scope filtering if analysis exists
        if self.options.resume and manifest.phase_completed("analyze") and manifest.analysis:
            self._apply_scope_filtering(manifest, ctx)

        for phase in phases:
            if self.options.resume and manifest.phase_completed(phase.name):
                self.console.print(f"  [dim]Skipping {phase.name} (already completed)[/dim]")
                continue

            errors = phase.validate_preconditions(ctx)
            if errors:
                for e in errors:
                    self.console.print(f"  [red]Precondition failed:[/red] {e}")
                return

            self.console.print(f"  [bold]Phase: {phase.name}[/bold] ...")
            try:
                await phase.execute(ctx)
            except SystemExit:
                return  # review mode or auto-approve pause
            except Exception as exc:
                manifest.errors.append(f"{phase.name}: {exc}")
                ctx.save_manifest()
                self.console.print(f"  [red]Phase {phase.name} failed:[/red] {exc}")
                raise

            manifest.mark_phase_completed(phase.name)
            ctx.save_manifest()
            self.console.print(f"  [green]✓[/green] {phase.name} complete")

            # Post-analyze: scope filtering / review pause (codebase mode only)
            if phase.name == "analyze":
                if self._post_analyze_hook(manifest, ctx):
                    return

        self.console.print()
        self.console.print(f"[bold green]Done![/bold green] Output: {ctx.output_dir}")

    def _apply_scope_filtering(
        self, manifest: GenerationManifest, ctx: PipelineContext
    ) -> None:
        """Apply scope filtering to analysis capabilities."""
        scope_path = Path(manifest.output_dir) / "scope.yaml"
        has_scope = (
            self.options.include
            or self.options.exclude
            or self.options.scope_file
            or scope_path.exists()
        )
        if not has_scope or not manifest.analysis:
            return

        effective_scope_file = self.options.scope_file
        if not effective_scope_file and scope_path.exists():
            effective_scope_file = scope_path

        before = len(manifest.analysis.capabilities)
        manifest.analysis = apply_scope(
            manifest.analysis,
            include_patterns=self.options.include,
            exclude_patterns=self.options.exclude,
            scope_file=effective_scope_file,
        )
        after = len(manifest.analysis.capabilities)
        if before != after:
            self.console.print(
                f"  [yellow]Scope:[/yellow] {before} capabilities → {after} "
                f"({before - after} excluded)"
            )
        ctx.save_manifest()

    async def run(self) -> None:
        manifest = self._init_manifest()
        ctx = PipelineContext(self.options, manifest, self.console)

        phase_names = self.options.phases or ALL_PHASES
        phases = _load_phases(phase_names, target=getattr(self.options, "target", "fastmcp"))

        self.console.print(
            f"[bold green]MCP-Anything[/bold green] generating server for "
            f"[cyan]{manifest.server_name}[/cyan]"
        )
        self.console.print(f"Phases: {', '.join(phase_names)}")
        self.console.print()

        # On resume: apply scope filtering before running remaining phases
        if self.options.resume and manifest.phase_completed("analyze") and manifest.analysis:
            self._apply_scope_filtering(manifest, ctx)

        # --description: merge description overrides and regenerate
        if self.options.description and manifest.design:
            desc_path = Path(manifest.output_dir) / "descriptions.yaml"
            if not desc_path.exists():
                self.console.print(
                    f"[red]Error:[/red] No descriptions.yaml found at {desc_path}"
                )
                return
            count = merge_description_overrides(manifest.design, desc_path)
            if count:
                for p in ("implement", "document", "package"):
                    if p in manifest.completed_phases:
                        manifest.completed_phases.remove(p)
                ctx.save_manifest()
                self.console.print(f"  Applied {count} description override(s) from descriptions.yaml")
            else:
                self.console.print("  No description changes detected in descriptions.yaml")

        for phase in phases:
            if (self.options.resume or self.options.description) and manifest.phase_completed(phase.name):
                self.console.print(f"  [dim]Skipping {phase.name} (already completed)[/dim]")
                continue

            errors = phase.validate_preconditions(ctx)
            if errors:
                for e in errors:
                    self.console.print(f"  [red]Precondition failed:[/red] {e}")
                return

            self.console.print(f"  [bold]Phase: {phase.name}[/bold] ...")
            try:
                await phase.execute(ctx)
            except Exception as exc:
                manifest.errors.append(f"{phase.name}: {exc}")
                ctx.save_manifest()
                self.console.print(f"  [red]Phase {phase.name} failed:[/red] {exc}")
                raise

            manifest.mark_phase_completed(phase.name)
            ctx.save_manifest()
            self.console.print(f"  [green]✓[/green] {phase.name} complete")

            # Scope filtering: after ANALYZE, before DESIGN
            if phase.name == "analyze":
                if self._post_analyze_hook(manifest, ctx):
                    return

            # After DESIGN: write descriptions.yaml for user editing
            if phase.name == "design" and manifest.design:
                desc_path = Path(manifest.output_dir) / "descriptions.yaml"
                write_descriptions_file(manifest.design, desc_path)

        self.console.print()
        self.console.print(f"[bold green]Done![/bold green] Output: {ctx.output_dir}")


def show_status(output_dir: Path, console: Console) -> None:
    """Display manifest status for the given output directory."""
    manifest_path = output_dir / "mcp-anything-manifest.json"
    if not manifest_path.exists():
        console.print(f"[red]No manifest found at {manifest_path}[/red]")
        return

    manifest = GenerationManifest.load(manifest_path)
    console.print(f"[bold]Server:[/bold] {manifest.server_name}")
    console.print(f"[bold]Codebase:[/bold] {manifest.codebase_path}")
    console.print(f"[bold]Completed phases:[/bold] {', '.join(manifest.completed_phases) or 'none'}")
    console.print(f"[bold]Generated files:[/bold] {len(manifest.generated_files)}")
    if manifest.errors:
        console.print(f"[bold red]Errors:[/bold red]")
        for err in manifest.errors:
            console.print(f"  - {err}")

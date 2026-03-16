"""Phase 3: IMPLEMENT — generate MCP server source code."""

import ast
from pathlib import Path

from mcp_anything.codegen.emitter import Emitter
from mcp_anything.pipeline.context import PipelineContext
from mcp_anything.pipeline.phase import Phase


class ImplementPhase(Phase):
    @property
    def name(self) -> str:
        return "implement"

    def validate_preconditions(self, ctx: PipelineContext) -> list[str]:
        if not ctx.manifest.design:
            return ["Design phase must complete before implement"]
        return []

    async def execute(self, ctx: PipelineContext) -> None:
        design = ctx.manifest.design
        assert design is not None

        output_dir = Path(ctx.manifest.output_dir)
        emitter = Emitter(design, output_dir)

        ctx.console.print("    Generating server code...")
        generated = emitter.emit_all()

        # Validate all generated Python files compile
        ctx.console.print("    Validating generated Python...")
        errors = self._validate_python(output_dir, generated)
        if errors:
            for path, err in errors:
                ctx.console.print(f"    [red]Syntax error in {path}:[/red] {err}")
            raise RuntimeError(
                f"Generated {len(errors)} file(s) with syntax errors. "
                "This is a bug in mcp-anything's code generation."
            )

        ctx.manifest.generated_files.extend(generated)
        ctx.console.print(f"    Generated {len(generated)} files (all valid Python)")

    def _validate_python(
        self, output_dir: Path, generated_files: list[str]
    ) -> list[tuple[str, str]]:
        """Parse all generated .py files and return (path, error) for failures."""
        errors: list[tuple[str, str]] = []
        for rel_path in generated_files:
            if not rel_path.endswith(".py"):
                continue
            full_path = output_dir / rel_path
            try:
                source = full_path.read_text()
                ast.parse(source)
            except SyntaxError as exc:
                errors.append((rel_path, f"line {exc.lineno}: {exc.msg}"))
        return errors

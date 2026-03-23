"""Phase 3: IMPLEMENT — generate MCP server source code."""

import ast
import re
import subprocess
import sys
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

        # Compile .proto files into Python stubs when gRPC tools are present
        if any(t.impl.grpc_proto_module for t in design.tools):
            pkg_name = emitter.package_name
            proto_stubs = self._compile_proto_stubs(ctx, output_dir, pkg_name)
            if proto_stubs:
                generated.extend(proto_stubs)

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

        # Emit packaging files early so generated tests can find pyproject.toml / mcp.json
        packaging = emitter.emit_packaging()
        ctx.manifest.generated_files.extend(packaging)

    def _compile_proto_stubs(
        self, ctx: PipelineContext, output_dir: Path, pkg_name: str
    ) -> list[str]:
        """Compile .proto files to Python gRPC stubs using grpcio-tools.

        Stubs are placed in src/{pkg_name}/proto_stubs/ so the backend can
        import them as `{pkg_name}.proto_stubs.{module}_pb2`.

        Returns list of generated file paths relative to output_dir.
        """
        try:
            from grpc_tools import protoc  # type: ignore[import]
        except ImportError:
            ctx.console.print(
                "    [yellow]grpcio-tools not installed — skipping proto compilation. "
                "Install with: pip install grpcio-tools[/yellow]"
            )
            return []

        # Collect unique .proto files from gRPC tools
        proto_modules = {
            t.impl.grpc_proto_module
            for t in ctx.manifest.design.tools  # type: ignore[union-attr]
            if t.impl.grpc_proto_module
        }

        codebase = Path(ctx.manifest.codebase_path)
        stubs_dir = output_dir / "src" / pkg_name / "proto_stubs"
        stubs_dir.mkdir(parents=True, exist_ok=True)

        generated: list[str] = []
        init_path = stubs_dir / "__init__.py"
        init_path.write_text('"""Compiled gRPC protobuf stubs."""\n')
        generated.append(f"src/{pkg_name}/proto_stubs/__init__.py")

        for module_stem in proto_modules:
            # Search for the .proto file in the codebase
            proto_files = list(codebase.rglob(f"{module_stem}.proto"))
            if not proto_files:
                ctx.console.print(
                    f"    [yellow]Proto file '{module_stem}.proto' not found in codebase[/yellow]"
                )
                continue

            proto_file = proto_files[0]
            proto_dir = str(proto_file.parent)

            ret = protoc.main([
                "grpc_tools.protoc",
                f"--proto_path={proto_dir}",
                f"--python_out={stubs_dir}",
                f"--grpc_python_out={stubs_dir}",
                str(proto_file),
            ])

            if ret != 0:
                ctx.console.print(
                    f"    [yellow]Proto compilation failed for {proto_file.name}[/yellow]"
                )
                continue

            pb2 = f"src/{pkg_name}/proto_stubs/{module_stem}_pb2.py"
            pb2_grpc = f"src/{pkg_name}/proto_stubs/{module_stem}_pb2_grpc.py"
            for rel in (pb2, pb2_grpc):
                if (output_dir / rel).exists():
                    generated.append(rel)

            # grpcio-tools generates bare `import <stem>_pb2 as ...` in _pb2_grpc.py.
            # Patch to relative imports so the stubs work as a sub-package.
            grpc_stub_path = output_dir / pb2_grpc
            if grpc_stub_path.exists():
                self._patch_grpc_stub_imports(grpc_stub_path)

            ctx.console.print(f"    Compiled {proto_file.name} → proto_stubs/")

        return generated

    def _patch_grpc_stub_imports(self, grpc_stub_path: Path) -> None:
        """Replace bare proto imports with relative imports in a compiled _pb2_grpc.py.

        grpcio-tools emits `import foo_pb2 as foo__pb2` at module level.
        When proto_stubs is a sub-package this bare import fails at runtime.
        Replace with `from . import foo_pb2 as foo__pb2` so the stubs resolve
        correctly as part of the package.
        """
        content = grpc_stub_path.read_text()
        patched = re.sub(
            r"^import (\w+_pb2) as (\w+)$",
            r"from . import \1 as \2",
            content,
            flags=re.MULTILINE,
        )
        if patched != content:
            grpc_stub_path.write_text(patched)

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

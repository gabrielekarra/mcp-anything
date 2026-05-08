"""Tests for codebase fusion in the domain pipeline.

Covers:
- Auto-detect of codebase data-source in CLI
- Engine branches to ANALYZE+DESIGN prefix when kind=codebase
- Domain modeling reads from manifest.analysis (not disk)
- Reshape mode: seed tools are preserved, LLM authority is enforced
- No-LLM path: seed design passes through unchanged
- Spec-only path: no regression (no analyze/design prefix)
"""

import asyncio
import textwrap
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from mcp_anything.config import CLIOptions
from mcp_anything.models.analysis import AnalysisResult, Capability
from mcp_anything.models.design import ServerDesign, ToolImpl, ToolSpec
from mcp_anything.models.domain import DataSource, DomainBrief, DomainModel, GlossaryTerm, UseCase
from mcp_anything.models.manifest import GenerationManifest
from mcp_anything.pipeline.context import PipelineContext
from mcp_anything.pipeline.domain_modeling import _summarize_analysis, _load_data_source_summary
from mcp_anything.pipeline.engine import PipelineEngine, CODEBASE_PREFIX, DOMAIN_PHASES
from mcp_anything.pipeline.tool_design import ToolDesignPhase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_analysis(n=3) -> AnalysisResult:
    caps = [
        Capability(
            name=f"get_item_{i}",
            description=f"Get item {i}",
            category="api",
            http_method="GET",
            http_path=f"/items/{i}",
        )
        for i in range(n)
    ]
    return AnalysisResult(app_name="my-app", app_description="Test app", capabilities=caps)


def _make_seed_design(n=3) -> ServerDesign:
    tools = [
        ToolSpec(
            name=f"get_item_{i}",
            description=f"Get item {i}",
            impl=ToolImpl(strategy="http_call", http_method="GET", http_path=f"/items/{i}"),
        )
        for i in range(n)
    ]
    return ServerDesign(server_name="my-app", tools=tools)


def _make_domain_model(use_cases=None) -> DomainModel:
    return DomainModel(
        server_name="my-app",
        domain_description="A test app",
        use_cases=use_cases or [UseCase(id="uc-01", description="Get item 0", actor="agent")],
        glossary=[GlossaryTerm(term="Item", definition="A domain item")],
        domain_entities=["Item"],
        access_patterns=["get item"],
        approved=True,
        data_sources=[DataSource(kind="codebase", path=".")],
    )


def _make_options(brief_file=None, codebase_path=Path("."), no_llm=True) -> CLIOptions:
    return CLIOptions(
        codebase_path=codebase_path,
        no_llm=no_llm,
        brief_file=brief_file,
    )


# ---------------------------------------------------------------------------
# Unit: _summarize_analysis
# ---------------------------------------------------------------------------

class TestSummarizeAnalysis:
    def test_includes_app_name(self):
        analysis = _make_analysis(2)
        summary = _summarize_analysis(analysis)
        assert "my-app" in summary

    def test_includes_capability_names(self):
        analysis = _make_analysis(2)
        summary = _summarize_analysis(analysis)
        assert "get_item_0" in summary
        assert "get_item_1" in summary

    def test_includes_http_method_and_path(self):
        analysis = _make_analysis(2)
        summary = _summarize_analysis(analysis)
        assert "GET" in summary
        assert "/items/0" in summary

    def test_caps_at_6000_chars(self):
        caps = [
            Capability(name=f"tool_{i}", description="x" * 100, http_method="GET", http_path=f"/a/{i}")
            for i in range(200)
        ]
        analysis = AnalysisResult(app_name="big-app", capabilities=caps)
        summary = _summarize_analysis(analysis)
        assert len(summary) <= 6000


# ---------------------------------------------------------------------------
# Unit: _load_data_source_summary codebase branch
# ---------------------------------------------------------------------------

class TestLoadDataSourceSummary:
    def test_codebase_kind_uses_manifest_analysis(self):
        brief = DomainBrief(
            server_name="app",
            data_source_kind="codebase",
            data_source_path=".",
            use_cases=["get item"],
        )
        ctx = MagicMock()
        ctx.manifest.analysis = _make_analysis(2)
        summary = _load_data_source_summary(brief, ctx)
        assert summary is not None
        assert "my-app" in summary

    def test_codebase_kind_no_analysis_returns_none(self):
        brief = DomainBrief(
            server_name="app",
            data_source_kind="codebase",
            data_source_path=".",
            use_cases=["get item"],
        )
        ctx = MagicMock()
        ctx.manifest.analysis = None
        result = _load_data_source_summary(brief, ctx)
        assert result is None

    def test_no_ctx_for_codebase_returns_none(self):
        brief = DomainBrief(
            server_name="app",
            data_source_kind="codebase",
            data_source_path=".",
            use_cases=["get item"],
        )
        result = _load_data_source_summary(brief, ctx=None)
        assert result is None

    def test_non_codebase_kind_reads_file(self, tmp_path):
        spec_file = tmp_path / "api.txt"
        spec_file.write_text("raw content")
        brief = DomainBrief(
            server_name="app",
            data_source_kind="other",
            data_source_path=str(spec_file),
            use_cases=["get item"],
        )
        result = _load_data_source_summary(brief)
        assert result == "raw content"


# ---------------------------------------------------------------------------
# Unit: ToolDesignPhase._is_actionable_seed_tool
# ---------------------------------------------------------------------------

class TestIsActionableSeedTool:
    def _tool(self, strategy, **impl_kwargs):
        from mcp_anything.models.design import ToolImpl, ToolSpec
        impl = ToolImpl(strategy=strategy, **impl_kwargs)
        return ToolSpec(name="t", description="d", impl=impl)

    def test_http_call_with_path_is_actionable(self):
        t = self._tool("http_call", http_method="GET", http_path="/items")
        assert ToolDesignPhase._is_actionable_seed_tool(t) is True

    def test_http_call_without_path_not_actionable(self):
        t = self._tool("http_call", http_method="GET", http_path="")
        assert ToolDesignPhase._is_actionable_seed_tool(t) is False

    def test_python_call_with_module_is_actionable(self):
        t = self._tool("python_call", python_module="my.module", python_function="fn")
        assert ToolDesignPhase._is_actionable_seed_tool(t) is True

    def test_python_call_without_module_not_actionable(self):
        t = self._tool("python_call", python_module="", python_function="fn")
        assert ToolDesignPhase._is_actionable_seed_tool(t) is False

    def test_cli_subcommand_is_actionable(self):
        t = self._tool("cli_subcommand", cli_subcommand="list")
        assert ToolDesignPhase._is_actionable_seed_tool(t) is True

    def test_protocol_call_without_grpc_not_actionable(self):
        t = self._tool("protocol_call", grpc_service="")
        assert ToolDesignPhase._is_actionable_seed_tool(t) is False

    def test_protocol_call_with_grpc_is_actionable(self):
        t = self._tool("protocol_call", grpc_service="MyService", grpc_method="MyMethod")
        assert ToolDesignPhase._is_actionable_seed_tool(t) is True

    def test_stub_not_actionable(self):
        t = self._tool("stub")
        assert ToolDesignPhase._is_actionable_seed_tool(t) is False

    def test_stubs_filtered_from_reshape_prompt(self, tmp_path):
        """Non-actionable protocol_call stubs are removed before the LLM sees the seed."""
        options = _make_options(no_llm=True)
        manifest = GenerationManifest(codebase_path=".", output_dir=str(tmp_path), server_name="x")
        ctx = PipelineContext(options, manifest, MagicMock())
        # 2 actionable + 1 stub
        tools = [
            ToolSpec(name="real", description="d",
                     impl=ToolImpl(strategy="http_call", http_method="GET", http_path="/x")),
            ToolSpec(name="stub", description="d",
                     impl=ToolImpl(strategy="protocol_call", grpc_service="")),
        ]
        seed = ServerDesign(server_name="s", tools=tools)
        result = ToolDesignPhase()._reshape_tools(_make_domain_model(), seed, ctx)
        assert len(result.tools) == 1
        assert result.tools[0].name == "real"


# ---------------------------------------------------------------------------
# Unit: ToolDesignPhase._reshape_tools
# ---------------------------------------------------------------------------

class TestReshapeTools:
    def _make_ctx(self, no_llm=True):
        import tempfile
        manifest = GenerationManifest(
            codebase_path=".",
            output_dir=tempfile.mkdtemp(prefix="mcp_test_"),
            server_name="my-app",
        )
        options = _make_options(no_llm=no_llm)
        console = MagicMock()
        ctx = PipelineContext(options, manifest, console)
        return ctx

    def test_nollm_returns_seed_unchanged(self):
        ctx = self._make_ctx(no_llm=True)
        seed = _make_seed_design(3)
        domain_model = _make_domain_model()
        phase = ToolDesignPhase()
        result = phase._reshape_tools(domain_model, seed, ctx)
        # All seed tools are actionable http_call tools, so count must match
        assert len(result.tools) == len(seed.tools)
        assert [t.name for t in result.tools] == [t.name for t in seed.tools]

    def test_llm_kept_tools_preserve_impl(self):
        ctx = self._make_ctx(no_llm=False)
        seed = _make_seed_design(3)
        domain_model = _make_domain_model()

        llm_response = {
            "kept_tools": [
                {
                    "seed_name": "get_item_0",
                    "new_name": "fetch_item",
                    "description": "Retrieves a single item from the catalog.",
                    "disclosure_level": "default",
                    "compact_fields": ["id", "name"],
                }
            ],
            "tool_groups": [],
            "composed_tools": [],
            "dropped_tools": ["get_item_1", "get_item_2"],
            "drop_reasons": {"get_item_1": "not in brief", "get_item_2": "not in brief"},
        }

        phase = ToolDesignPhase()
        with patch("mcp_anything.pipeline.llm_client.call_llm_for_json", return_value=llm_response):
            result = phase._reshape_tools(domain_model, seed, ctx)

        assert len(result.tools) == 1
        kept = result.tools[0]
        assert kept.name == "fetch_item"
        assert kept.description == "Retrieves a single item from the catalog."
        # impl must be from seed, not LLM
        assert kept.impl.http_path == "/items/0"
        assert kept.impl.http_method == "GET"
        assert kept.impl.strategy == "http_call"

    def test_llm_invalid_seed_name_rejected(self):
        ctx = self._make_ctx(no_llm=False)
        seed = _make_seed_design(2)
        domain_model = _make_domain_model()
        phase = ToolDesignPhase()

        llm_response = {
            "kept_tools": [
                {
                    "seed_name": "invented_tool_not_in_seed",
                    "new_name": "invented_tool_not_in_seed",
                    "description": "This tool was invented by the LLM.",
                },
            ],
            "tool_groups": [],
            "composed_tools": [],
            "dropped_tools": [],
            "drop_reasons": {},
        }

        with patch("mcp_anything.pipeline.llm_client.call_llm_for_json", return_value=llm_response):
            result = phase._reshape_tools(domain_model, seed, ctx)

        # All invalid → fallback to seed (equal tools, different object due to model_copy)
        assert [t.name for t in result.tools] == [t.name for t in seed.tools]

    def test_llm_cannot_change_impl_via_kept_tools(self):
        ctx = self._make_ctx(no_llm=False)
        seed = _make_seed_design(1)
        domain_model = _make_domain_model()
        phase = ToolDesignPhase()

        llm_response = {
            "kept_tools": [
                {
                    "seed_name": "get_item_0",
                    "new_name": "get_item_0",
                    "description": "Valid description from the agent perspective.",
                    # LLM tries to sneak in impl changes — these should be ignored
                    "impl": {"strategy": "stub", "http_path": "/hacked"},
                }
            ],
            "tool_groups": [],
            "composed_tools": [],
            "dropped_tools": [],
        }

        with patch("mcp_anything.pipeline.llm_client.call_llm_for_json", return_value=llm_response):
            result = phase._reshape_tools(domain_model, seed, ctx)

        # impl must be from seed
        assert result.tools[0].impl.http_path == "/items/0"
        assert result.tools[0].impl.strategy == "http_call"

    def test_llm_failure_falls_back_to_seed(self):
        ctx = self._make_ctx(no_llm=False)
        seed = _make_seed_design(2)
        domain_model = _make_domain_model()
        phase = ToolDesignPhase()

        with patch(
            "mcp_anything.pipeline.llm_client.call_llm_for_json",
            side_effect=RuntimeError("API down"),
        ):
            result = phase._reshape_tools(domain_model, seed, ctx)

        # Failure fallback returns seed tools (different object due to model_copy)
        assert [t.name for t in result.tools] == [t.name for t in seed.tools]


# ---------------------------------------------------------------------------
# Integration: engine branches correctly for codebase vs. spec
# ---------------------------------------------------------------------------

class TestEnginePhaseSelection:
    def _make_engine(self, brief_kind: str, tmp_path: Path) -> PipelineEngine:
        brief = {
            "server_name": "test-server",
            "domain_description": "test",
            "use_cases": ["do something"],
            "data_source_kind": brief_kind,
            "data_source_path": str(tmp_path),
        }
        brief_file = tmp_path / "brief.yaml"
        brief_file.write_text(yaml.dump(brief))
        options = CLIOptions(
            codebase_path=tmp_path,
            brief_file=brief_file,
        )
        console = MagicMock()
        return PipelineEngine(options, console)

    def test_codebase_kind_prefixes_phases(self, tmp_path):
        engine = self._make_engine("codebase", tmp_path)
        assert engine._peek_brief_kind() == "codebase"

    def test_openapi_kind_no_prefix(self, tmp_path):
        engine = self._make_engine("openapi", tmp_path)
        assert engine._peek_brief_kind() == "openapi"

    def test_in_memory_brief_overrides_file(self, tmp_path):
        options = CLIOptions(
            codebase_path=tmp_path,
            domain_brief={"server_name": "x", "data_source_kind": "codebase"},
        )
        engine = PipelineEngine(options, MagicMock())
        assert engine._peek_brief_kind() == "codebase"


# ---------------------------------------------------------------------------
# Integration: no-LLM pipeline with fake_flask_app fixture
# ---------------------------------------------------------------------------

FLASK_BRIEF_YAML = textwrap.dedent("""
    server_name: flask-test-server
    domain_description: A small Flask API for testing
    use_cases:
      - List all items
      - Get a single item
    data_source_kind: codebase
    data_source_path: "{codebase_path}"
""")

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.skipif(
    not (FIXTURES / "fake_flask_app").exists(),
    reason="fake_flask_app fixture not found",
)
class TestNoLLMCodebaseFusion:
    def test_analyze_and_design_run_before_domain_phases(self, tmp_path):
        codebase = FIXTURES / "fake_flask_app"
        brief_content = FLASK_BRIEF_YAML.format(codebase_path=str(codebase))
        brief_file = tmp_path / "brief.yaml"
        brief_file.write_text(brief_content)

        options = CLIOptions(
            codebase_path=codebase,
            output_dir=tmp_path / "output",
            brief_file=brief_file,
            no_llm=True,
            domain_brief=yaml.safe_load(brief_content),
        )
        console = MagicMock()
        engine = PipelineEngine(options, console)

        asyncio.run(engine.run_domain())

        # Manifest should have both analysis and tool_spec
        from mcp_anything.models.manifest import GenerationManifest
        manifest_path = tmp_path / "output" / "mcp-anything-manifest.json"
        assert manifest_path.exists(), "manifest not written"
        manifest = GenerationManifest.load(manifest_path)

        assert manifest.analysis is not None, "analysis not populated"
        assert manifest.tool_spec is not None, "tool_spec not populated"

        # In no-LLM codebase mode, the seed design passes through unchanged
        # so tool_spec should reflect the legacy design tools
        from mcp_anything.models.design import ServerDesign
        design = ServerDesign.model_validate(manifest.tool_spec)
        assert len(design.tools) > 0, "no tools in output"

        # All tools should have concrete strategies (not stub), since Flask detector
        # produces http_call tools
        strategies = {t.impl.strategy for t in design.tools}
        assert "stub" not in strategies, (
            f"Expected no stub tools when Flask routes are detected, got: {strategies}"
        )

    def test_completed_phases_include_analyze_and_design(self, tmp_path):
        codebase = FIXTURES / "fake_flask_app"
        brief_content = FLASK_BRIEF_YAML.format(codebase_path=str(codebase))
        brief_file = tmp_path / "brief.yaml"
        brief_file.write_text(brief_content)

        options = CLIOptions(
            codebase_path=codebase,
            output_dir=tmp_path / "output",
            brief_file=brief_file,
            no_llm=True,
            domain_brief=yaml.safe_load(brief_content),
        )
        console = MagicMock()
        engine = PipelineEngine(options, console)

        asyncio.run(engine.run_domain())

        from mcp_anything.models.manifest import GenerationManifest
        manifest = GenerationManifest.load(tmp_path / "output" / "mcp-anything-manifest.json")
        assert "analyze" in manifest.completed_phases
        assert "design" in manifest.completed_phases
        assert "domain_modeling" in manifest.completed_phases
        assert "tool_design" in manifest.completed_phases

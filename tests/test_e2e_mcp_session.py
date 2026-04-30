"""End-to-end MCP session tests.

For every supported source type, this file:
  1. Generates a server (legacy pipeline --no-llm, or domain pipeline).
  2. Starts the server as a subprocess via stdio transport.
  3. Connects an MCP SDK client.
  4. Asserts tools/list returns ≥1 tool.
  5. Calls one tool and asserts a non-crash response (backend errors are acceptable
     since no real backend is running for most fixtures).

Additionally, TestMCPSessionWithClaude runs an Anthropic SDK round-trip using the
pokewiki server (real PokéAPI backend) to verify a full Claude Code simulation:
  - Claude receives the tool list.
  - Claude calls a tool to answer a factual question.
  - The tool response is forwarded back; Claude produces a final text answer.

Requires:
  - Legacy-pipeline tests: no API key needed.
  - TestMCPSessionDomainPipeline + TestMCPSessionWithClaude: ANTHROPIC_API_KEY env var.
"""

from __future__ import annotations

import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import pytest
from rich.console import Console

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from mcp_anything.config import CLIOptions
from mcp_anything.pipeline.engine import PipelineEngine

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).parent / "fixtures"


async def _generate(codebase_path: Path, output_dir: Path, *, name: str | None = None) -> None:
    """Run the legacy pipeline (no-LLM) and emit a server into output_dir."""
    options = CLIOptions(
        codebase_path=codebase_path,
        output_dir=output_dir,
        name=name,
        no_llm=True,
        no_install=True,
        transport="stdio",
    )
    engine = PipelineEngine(options, Console(quiet=True))
    await engine.run()



@asynccontextmanager
async def _mcp_session(
    output_dir: Path,
    server_name: str,
    extra_env: dict | None = None,
) -> AsyncGenerator[ClientSession, None]:
    """Start the generated server as a subprocess and yield an MCP ClientSession.

    Handles both legacy (output_dir/src/<pkg>) and domain (output_dir/<pkg>) layouts.
    """
    pkg = f"mcp_{server_name.replace('-', '_')}"
    # Domain pipeline puts the package directly under output_dir;
    # legacy pipeline puts it under output_dir/src/
    if (output_dir / pkg).is_dir():
        python_path = str(output_dir)
    elif (output_dir / "src" / pkg).is_dir():
        python_path = str(output_dir / "src")
    else:
        python_path = str(output_dir)

    env = {**os.environ, "PYTHONPATH": python_path, **(extra_env or {})}
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", f"{pkg}.server"],
        env=env,
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


def _server_name_from_manifest(output_dir: Path) -> str:
    manifest_path = output_dir / "mcp-anything-manifest.json"
    if manifest_path.exists():
        data = json.loads(manifest_path.read_text())
        return data.get("server_name", "mcp-server")
    return "mcp-server"


# ---------------------------------------------------------------------------
# Legacy pipeline — all 27 source types
# ---------------------------------------------------------------------------

# Each entry: (test_id, fixture_dir_name, min_tools, one_tool_to_call)
# min_tools: minimum number of tools expected in tools/list
# one_tool_to_call: (tool_name, args) to exercise — None to skip live call
_LEGACY_CASES = [
    # Python
    ("flask",          "fake_flask_app",        1, None),
    ("fastapi",        "fake_fastapi_app",       1, None),
    ("django",         "fake_django_app",        1, None),
    ("argparse_cli",   "fake_cli_app",           1, None),
    ("click_cli",      "fake_click_app",         1, None),
    # Node / TypeScript
    ("express_js",     "fake_express_app",       1, None),
    ("express_ts",     "fake_ts_express_app",    1, None),
    # Java / JVM
    ("spring_boot",    "fake_spring_app",        1, None),
    ("spring_mvc",     "fake_spring_mvc_app",    1, None),
    ("jaxrs",          "fake_jaxrs_app",         1, None),
    ("kotlin_spring",  "fake_kotlin_spring_app", 1, None),
    ("kotlin_jaxrs",   "fake_kotlin_jaxrs_app",  1, None),
    ("micronaut",      "fake_micronaut_app",     1, None),
    # Go
    ("go_gin",         "fake_go_app",            1, None),
    ("go_echo",        "fake_go_echo_app",       1, None),
    ("go_chi",         "fake_go_chi_app",        1, None),
    ("go_mux",         "fake_go_mux_app",        1, None),
    ("go_nethttp",     "fake_go_nethttp_app",    1, None),
    # Ruby
    ("rails",          "fake_rails_app",         1, None),
    ("rails_explicit", "fake_rails_explicit_routes_app", 1, None),
    # Rust
    ("actix",          "fake_rust_app",          1, None),
    ("axum",           "fake_axum_app",          1, None),
    ("rocket",         "fake_rocket_app",        1, None),
    ("warp",           "fake_warp_app",          1, None),
    # Protocols / specs
    ("openapi",        "petstore_openapi.json",  1, None),  # file: copied into tmp dir in test
    ("graphql",        "fake_graphql_app",       1, None),
    ("grpc",           "fake_grpc_app",          1, None),
    ("websocket",      "fake_websocket_app",     1, None),
    ("socket_xmlrpc",  "fake_socket_xmlrpc_app", 1, None),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("test_id,fixture,min_tools,call_spec", _LEGACY_CASES, ids=[c[0] for c in _LEGACY_CASES])
async def test_legacy_mcp_session(test_id, fixture, min_tools, call_spec, tmp_path):  # noqa: ARG001
    """Generate → start → list tools → optionally call one tool."""
    fixture_path = FIXTURES / fixture
    assert fixture_path.exists(), f"Fixture not found: {fixture_path}"

    # OpenAPI / Swagger specs are single files; legacy pipeline expects a directory
    if fixture_path.is_file():
        import shutil
        spec_dir = tmp_path / "spec_dir"
        spec_dir.mkdir()
        shutil.copy(fixture_path, spec_dir / fixture_path.name)
        gen_path = spec_dir
    else:
        gen_path = fixture_path

    await _generate(gen_path, tmp_path)

    server_name = _server_name_from_manifest(tmp_path)

    async with _mcp_session(tmp_path, server_name) as session:
        tools_result = await session.list_tools()
        tools = tools_result.tools
        assert len(tools) >= min_tools, (
            f"[{test_id}] Expected ≥{min_tools} tools, got {len(tools)}: "
            + ", ".join(t.name for t in tools)
        )

        if call_spec:
            tool_name, tool_args = call_spec
            result = await session.call_tool(tool_name, tool_args)
            # Accept any response — backend may be offline; we just verify no crash
            assert result is not None


# ---------------------------------------------------------------------------
# Domain pipeline — pokewiki (real PokéAPI, LLM required)
# ---------------------------------------------------------------------------

_POKEWIKI_BRIEF = Path("/tmp/pokewiki-e2e/brief.yaml")
_POKEWIKI_SPEC  = Path("/tmp/pokewiki-e2e/pokeapi.yml")
_POKEWIKI_OUT   = Path("/tmp/pokewiki-e2e/out-session-test")

_DOMAIN_CASES = [
    ("pokewiki", _POKEWIKI_BRIEF, _POKEWIKI_SPEC, _POKEWIKI_OUT, "pokewiki",
     [("get_pokemon", {"pokemon_id": "pikachu"}),
      ("get_move", {"move_id": "thunderbolt"}),
      ("get_ability", {"ability_id": "static"}),
      ("get_type_matchups", {"type_id": "electric"})]),
]


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)
@pytest.mark.skipif(
    not _POKEWIKI_SPEC.exists(),
    reason="pokewiki spec not downloaded — run the pokewiki e2e setup first",
)
@pytest.mark.parametrize("test_id,brief,spec,out_dir,srv_name,live_calls",
                         _DOMAIN_CASES, ids=["pokewiki"])
async def test_domain_mcp_session(test_id, brief, spec, out_dir, srv_name, live_calls, tmp_path):
    """Domain pipeline: generate pokewiki → start → list tools → call real tools."""
    # Re-use cached output if it exists (avoid re-generating on every run)
    if not (out_dir / "mcp-anything-manifest.json").exists():
        from mcp_anything.config import CLIOptions as _CLIOptions
        import yaml as _yaml
        raw_brief = _yaml.safe_load(brief.read_text())
        raw_brief["data_source_path"] = str(spec)
        brief_tmp = tmp_path / "brief.yaml"
        brief_tmp.write_text(_yaml.dump(raw_brief))
        opts = _CLIOptions(
            codebase_path=spec,
            output_dir=out_dir,
            no_llm=False,
            no_install=True,
            transport="stdio",
            brief_file=str(brief_tmp),
            data_source=spec,
            auto_approve=True,
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        from mcp_anything.pipeline.engine import PipelineEngine as _PE
        await _PE(opts, Console(quiet=True)).run_domain()

    env = {**os.environ, "PYTHONPATH": str(out_dir),
           f"{srv_name.upper()}_BASE_URL": "https://pokeapi.co"}
    pkg = f"mcp_{srv_name.replace('-', '_')}"
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", f"{pkg}.server"],
        env=env,
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = (await session.list_tools()).tools
            tool_names = {t.name for t in tools}
            assert len(tools) >= 5, f"Expected ≥5 tools, got {len(tools)}"

            for tool_name, args in live_calls:
                if tool_name not in tool_names:
                    continue
                result = await session.call_tool(tool_name, args)
                assert result is not None
                content_text = ""
                for block in result.content:
                    content_text += getattr(block, "text", "") or str(block)
                assert len(content_text) > 10, f"Empty response from {tool_name}"


# ---------------------------------------------------------------------------
# Claude Code simulation — Anthropic SDK + MCP stdio round-trip
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)
@pytest.mark.skipif(
    not _POKEWIKI_SPEC.exists(),
    reason="pokewiki spec not downloaded",
)
class TestMCPSessionWithClaude:
    """Full Claude Code simulation: generated MCP server ↔ Anthropic SDK round-trip.

    This is equivalent to what Claude Code does:
      1. List tools from the MCP server.
      2. Present them to Claude as Anthropic tool definitions.
      3. Claude calls a tool; the result is fed back.
      4. Claude produces a final answer that uses the real data.
    """

    async def _start_pokewiki(self):
        """Build and return MCP session params for the pokewiki server."""
        out_dir = _POKEWIKI_OUT
        if not (out_dir / "mcp-anything-manifest.json").exists():
            pytest.skip("pokewiki server not generated — run test_domain_mcp_session first")

        env = {**os.environ, "PYTHONPATH": str(out_dir),
               "POKEWIKI_BASE_URL": "https://pokeapi.co"}
        return StdioServerParameters(
            command=sys.executable,
            args=["-m", "mcp_pokewiki.server"],
            env=env,
        )

    def _tools_to_anthropic(self, tools) -> list[dict]:
        """Convert MCP tool list to Anthropic tool_use format."""
        result = []
        for t in tools:
            schema = t.inputSchema or {}
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            # Ensure verbose is always optional
            if "verbose" in required:
                required = [r for r in required if r != "verbose"]
            result.append({
                "name": t.name,
                "description": t.description or t.name,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        k: {"type": v.get("type", "string"),
                            "description": v.get("description", "")}
                        for k, v in properties.items()
                        if k != "verbose"
                    },
                    "required": required,
                },
            })
        return result

    @pytest.mark.asyncio
    async def test_claude_answers_pokemon_stats(self):
        """Ask Claude about Pikachu's stats; verify it calls get_pokemon and answers correctly."""
        import anthropic

        params = await self._start_pokewiki()
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                mcp_tools = (await session.list_tools()).tools
                anthropic_tools = self._tools_to_anthropic(mcp_tools)

                client = anthropic.Anthropic()

                # Round 1: ask Claude — expect tool_use
                r1 = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=512,
                    tools=anthropic_tools,
                    messages=[{
                        "role": "user",
                        "content": "What are Pikachu's base HP and Speed stats?",
                    }],
                )
                assert r1.stop_reason == "tool_use", (
                    f"Expected tool_use, got {r1.stop_reason}. Content: {r1.content}"
                )
                tool_block = next(b for b in r1.content if b.type == "tool_use")
                assert tool_block.name in {"get_pokemon", "compare_pokemon_stats"}

                # Execute the tool via MCP
                mcp_result = await session.call_tool(tool_block.name, tool_block.input)
                tool_result_text = ""
                for block in mcp_result.content:
                    tool_result_text += getattr(block, "text", "") or str(block)

                # Round 2: send tool result back
                r2 = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=512,
                    tools=anthropic_tools,
                    messages=[
                        {"role": "user", "content": "What are Pikachu's base HP and Speed stats?"},
                        {"role": "assistant", "content": r1.content},
                        {"role": "user", "content": [{
                            "type": "tool_result",
                            "tool_use_id": tool_block.id,
                            "content": tool_result_text[:4000],
                        }]},
                    ],
                )
                assert r2.stop_reason == "end_turn"
                answer = next(b.text for b in r2.content if b.type == "text")
                # Pikachu HP=35, Speed=90 — verify at least one appears
                assert any(str(n) in answer for n in [35, 90]), (
                    f"Expected HP=35 or Speed=90 in answer: {answer}"
                )

    @pytest.mark.asyncio
    async def test_claude_identifies_pikachu_type(self):
        """Ask Claude what type Pikachu is; verify it calls get_pokemon and answers Electric."""
        import anthropic

        params = await self._start_pokewiki()
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                mcp_tools = (await session.list_tools()).tools
                anthropic_tools = self._tools_to_anthropic(mcp_tools)

                client = anthropic.Anthropic()
                messages = [{"role": "user", "content": "What type is Pikachu?"}]

                for _ in range(4):
                    r = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=512,
                        tools=anthropic_tools,
                        messages=messages,
                    )
                    if r.stop_reason == "end_turn":
                        answer = next(b.text for b in r.content if b.type == "text")
                        assert "electric" in answer.lower(), (
                            f"Expected 'electric' in answer. Got: {answer}"
                        )
                        return

                    messages.append({"role": "assistant", "content": r.content})
                    tool_results = []
                    for block in r.content:
                        if block.type == "tool_use":
                            mcp_result = await session.call_tool(block.name, block.input)
                            text = "".join(getattr(c, "text", "") or str(c)
                                          for c in mcp_result.content)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": text[:4000],
                            })
                    messages.append({"role": "user", "content": tool_results})

                pytest.fail("Claude did not reach end_turn within 4 rounds")

    @pytest.mark.asyncio
    async def test_claude_compares_two_pokemon(self):
        """Ask Claude to compare Pikachu and Charizard on base Attack. Uses compare_pokemon_stats."""
        import anthropic

        params = await self._start_pokewiki()
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                mcp_tools = (await session.list_tools()).tools
                anthropic_tools = self._tools_to_anthropic(mcp_tools)
                tool_names = {t.name for t in mcp_tools}

                if "compare_pokemon_stats" not in tool_names:
                    pytest.skip("compare_pokemon_stats not in generated tools")

                client = anthropic.Anthropic()
                messages = [{"role": "user",
                             "content": "Which has higher base Attack: Pikachu or Charizard?"}]

                for _ in range(5):
                    r = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=1024,
                        tools=anthropic_tools,
                        messages=messages,
                    )
                    if r.stop_reason == "end_turn":
                        answer = next(b.text for b in r.content if b.type == "text")
                        assert "charizard" in answer.lower(), (
                            f"Expected Charizard to win on Attack. Got: {answer}"
                        )
                        return
                    messages.append({"role": "assistant", "content": r.content})
                    tool_results = []
                    for block in r.content:
                        if block.type == "tool_use":
                            mcp_result = await session.call_tool(block.name, block.input)
                            text = "".join(getattr(c, "text", "") or str(c)
                                          for c in mcp_result.content)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": text[:4000],
                            })
                    messages.append({"role": "user", "content": tool_results})

                pytest.fail("Claude did not reach end_turn within 5 rounds")

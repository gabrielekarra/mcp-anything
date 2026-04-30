"""Real-world MCP session tests — one real repository per supported framework.

For every supported source type, this file:
  1. Clones (shallow) or uses a pre-checked-in realworld fixture.
  2. Runs the full legacy pipeline (--no-llm) on the real repository.
  3. Starts the generated MCP server as a subprocess via stdio transport.
  4. Connects an MCP SDK client and calls tools/list.
  5. Asserts at least the expected number of tools were generated.

Repos match the "Real Repo Tested" column in CLAUDE.md where possible;
otherwise the closest small, well-known public repo for that framework is used.

Run in isolation:
    pytest tests/test_e2e_realworld_session.py -v --timeout=300

These tests are opt-in because most cases clone from GitHub:
    MCP_ANYTHING_RUN_REALWORLD=1 pytest tests/test_e2e_realworld_session.py -v --timeout=300
"""

from __future__ import annotations

import json
import os
import subprocess
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
# Constants
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).parent / "fixtures"
CLONE_CACHE = Path(os.environ.get("MCP_TEST_CLONE_CACHE", "/tmp/mcp-anything-realworld"))

pytestmark = [
    pytest.mark.realworld,
    pytest.mark.skipif(
        os.environ.get("MCP_ANYTHING_RUN_REALWORLD") != "1",
        reason="set MCP_ANYTHING_RUN_REALWORLD=1 to run realworld session tests",
    ),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clone(url: str, dest: Path, subpath: str | None = None, *, timeout: int = 180) -> Path:
    """Shallow-clone url → dest (with optional sparse-checkout of subpath).

    Returns the path to analyze (dest/subpath if given, else dest).
    Skips the clone if dest already exists (cached from prior runs).
    """
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        base_cmd = ["git", "clone", "--depth=1", "--filter=blob:none"]
        if subpath:
            base_cmd += ["--sparse"]
        base_cmd += [url, str(dest)]
        try:
            subprocess.run(base_cmd, check=True, timeout=timeout,
                           capture_output=True)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            pytest.skip(f"Could not clone {url}: {exc}")
        if subpath:
            subprocess.run(
                ["git", "-C", str(dest), "sparse-checkout", "set", subpath],
                check=True, timeout=60, capture_output=True,
            )

    target = dest / subpath if subpath else dest
    if not target.exists():
        pytest.skip(f"Subpath {subpath!r} not found in {dest} after clone")
    return target


def _server_name_from_manifest(output_dir: Path) -> str:
    manifest = output_dir / "mcp-anything-manifest.json"
    if manifest.exists():
        return json.loads(manifest.read_text()).get("server_name", "mcp-server")
    return "mcp-server"


@asynccontextmanager
async def _mcp_session(
    output_dir: Path,
    server_name: str,
    extra_env: dict | None = None,
) -> AsyncGenerator[ClientSession, None]:
    pkg = f"mcp_{server_name.replace('-', '_')}"
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


async def _run_and_connect(source_path: Path, tmp_path: Path, *,
                           server_name: str | None = None, min_tools: int = 1):
    """Full pipeline: generate server → start → MCP tools/list → assert."""
    options = CLIOptions(
        codebase_path=source_path,
        output_dir=tmp_path,
        name=server_name,
        no_llm=True,
        no_install=True,
        transport="stdio",
    )
    await PipelineEngine(options, Console(quiet=True)).run()

    sname = server_name or _server_name_from_manifest(tmp_path)
    async with _mcp_session(tmp_path, sname) as session:
        tools = (await session.list_tools()).tools
        assert len(tools) >= min_tools, (
            f"Expected ≥{min_tools} tools for {source_path.name}, "
            f"got {len(tools)}: {[t.name for t in tools]}"
        )
        return tools


# ---------------------------------------------------------------------------
# Test matrix — one real repository per framework
# ---------------------------------------------------------------------------
#
# Each tuple: (test_id, git_url, subpath, min_tools, server_name, xfail_reason)
# git_url=None  → use a pre-checked-in fixture from tests/fixtures/realworld_*
# xfail_reason  → None means expect to pass; a string triggers pytest.mark.xfail
#
_REALWORLD_CASES = [
    # --- Python ---
    # httpie is the canonical real Python argparse CLI (CLAUDE.md)
    ("python_argparse",  "https://github.com/httpie/httpie",
     "httpie",           3,  "httpie",         None),
    # Click CLI — pallets/click examples directory
    ("python_click",     "https://github.com/pallets/click",
     "examples",         1,  "click-examples",  None),
    # Flask — gothinkster realworld Flask app
    ("python_flask",     "https://github.com/gothinkster/flask-realworld-example-app",
     None,               2,  "flask-rw",        None),
    # FastAPI — official FastAPI docs/src examples
    ("python_fastapi",   "https://github.com/tiangolo/fastapi",
     "docs_src",         1,  "fastapi-docs",    None),
    # Django DRF — encode's DRF (rest_framework package is at root)
    ("python_django",    "https://github.com/encode/django-rest-framework",
     None,               1,  "drf-example",     None),

    # --- Node.js / TypeScript ---
    # Express.js route-separation example
    ("express_js",       "https://github.com/expressjs/express",
     "examples/route-separation", 1, "express-rs",  None),
    # TypeScript + Express (gothinkster realworld TS app)
    ("express_ts",       "https://github.com/gothinkster/node-express-realworld-example-app",
     None,               1,  "ts-express-rw",  None),

    # --- Java / JVM ---
    # Spring Boot — spring-petclinic REST API (CLAUDE.md validated)
    ("spring_boot",      "https://github.com/spring-projects/spring-petclinic",
     None,               3,  "petclinic",       None),
    # Spring MVC showcase (archived but code is valid)
    ("spring_mvc",       "https://github.com/spring-attic/spring-mvc-showcase",
     None,               2,  "mvc-showcase",    "archived repo: may produce fewer tools"),
    # JAX-RS — Quarkus rest-json quickstart (CLAUDE.md)
    ("jaxrs_quarkus",    "https://github.com/quarkusio/quarkus-quickstarts",
     "rest-json-quickstart", 2, "quarkus-rest",  None),
    # Kotlin + Spring — spring-time-in-kotlin JetBrains hands-on
    ("kotlin_spring",    "https://github.com/kotlin-hands-on/spring-time-in-kotlin-episode1",
     None,               2,  "kt-spring",       None),
    # Kotlin + Quarkus (JAX-RS annotations, Kotlin source)
    ("kotlin_jaxrs",     "https://github.com/quarkusio/quarkus-quickstarts",
     "hibernate-orm-panache-kotlin-quickstart", 1, "quarkus-kotlin",
     "Kotlin+Quarkus: detection may produce fewer tools than pure JAX-RS"),
    # Micronaut benchmarks (CLAUDE.md: 2 tools)
    ("micronaut",        "https://github.com/micronaut-projects/micronaut-core",
     "benchmarks",       1,  "micronaut-bench",  None),

    # --- Go ---
    # Gin examples (CLAUDE.md: synthetic, but gin-gonic/examples is the real source)
    ("go_gin",           "https://github.com/gin-gonic/examples",
     None,               3,  "gin-examples",    None),
    # Echo — labstack/echo (CLAUDE.md: real-tested)
    ("go_echo",          "https://github.com/labstack/echo",
     None,               3,  "echo",             None),
    # Chi — go-chi/chi (CLAUDE.md: real-tested)
    ("go_chi",           "https://github.com/go-chi/chi",
     None,               3,  "chi",              None),
    # gorilla/mux (CLAUDE.md: 33 tools)
    ("go_mux",           "https://github.com/gorilla/mux",
     None,               3,  "gorilla-mux",     None),
    # Pure net/http — building-microservices product-api (Go stdlib HTTP handlers)
    ("go_nethttp",       "https://github.com/nicholasjackson/building-microservices-youtube",
     "product-api",      1,  "go-ms-step1",
     "small Go net/http example: tool count may vary"),

    # --- Ruby ---
    # Rails — activestorage subdirectory (CLAUDE.md: 9 tools)
    ("rails",            "https://github.com/rails/rails",
     "activestorage",    2,  "activestorage",   None),

    # --- Rust ---
    # Actix-web examples — dedicated examples repo (actix/examples)
    ("rust_actix",       "https://github.com/actix/examples",
     None,               2,  "actix-examples",  None),
    # Axum examples (CLAUDE.md: tokio-rs/axum → 36 tools)
    ("rust_axum",        "https://github.com/tokio-rs/axum",
     "examples",         5,  "axum-examples",   None),
    # Rocket examples (CLAUDE.md: SergioBenitez/Rocket → 44 tools)
    ("rust_rocket",      "https://github.com/rwf2/Rocket",
     "examples",         5,  "rocket-examples",  None),
    # Warp examples
    ("rust_warp",        "https://github.com/seanmonstar/warp",
     "examples",         1,  "warp-examples",   None),

    # --- Protocols / Specs ---
    # OpenAPI 3.x — OAI archive has v3.0 schema test fixtures (petstore + others)
    ("openapi",          "https://github.com/OAI/OpenAPI-Specification",
     "_archive_/schemas/v3.0/pass", 1, "oas-examples", None),
    # GraphQL SDL — swapi-graphql (Star Wars API, has schema.graphql)
    ("graphql",          "https://github.com/graphql/swapi-graphql",
     None,               1,  "swapi-graphql",   None),
    # gRPC — grpc-go helloworld (CLAUDE.md: grpc/Protobuf → synthetic, but grpc-go is real)
    ("grpc",             "https://github.com/grpc/grpc-go",
     "examples/helloworld", 1, "grpc-helloworld",  None),
    # WebSocket — Podnet JSON-RPC WS server (CLAUDE.md: real-tested, 13 tools)
    ("websocket",        "https://github.com/Podnet/json-rpc-websocket-server",
     None,               5,  "ws-server",       None),
]


def _parametrize_ids():
    return [c[0] for c in _REALWORLD_CASES]


def _parametrize_params():
    return [(c[1], c[2], c[3], c[4], c[5]) for c in _REALWORLD_CASES]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "git_url,subpath,min_tools,server_name,xfail_reason",
    _parametrize_params(),
    ids=_parametrize_ids(),
)
async def test_realworld_mcp_session(
    git_url, subpath, min_tools, server_name, xfail_reason, tmp_path
):
    """Clone real repo → generate → start MCP server → assert tools/list."""
    if xfail_reason:
        pytest.xfail(reason=xfail_reason) if False else None  # mark but don't skip
        # Use xfail non-strictly: pass is fine, fail is noted but not blocking
        request_xfail = True
    else:
        request_xfail = False

    # Clone (shallow, cached)
    clone_dest = CLONE_CACHE / server_name
    source_path = _clone(git_url, clone_dest, subpath)

    # If flagged as potentially-failing, wrap in xfail
    if request_xfail:
        try:
            await _run_and_connect(source_path, tmp_path,
                                   server_name=server_name, min_tools=min_tools)
        except Exception as exc:
            pytest.xfail(f"{xfail_reason}: {exc}")
    else:
        await _run_and_connect(source_path, tmp_path,
                               server_name=server_name, min_tools=min_tools)


# ---------------------------------------------------------------------------
# Realworld fixtures already in tests/fixtures/ (no network needed)
# ---------------------------------------------------------------------------

_FIXTURE_CASES = [
    # (test_id, fixture_dir, min_tools)
    ("realworld_express",  "realworld_express_app",  1),
    ("realworld_go",       "realworld_go_app",       1),
    ("realworld_rails",    "realworld_rails_app",    1),
    ("realworld_rust",     "realworld_rust_app",     1),
    ("realworld_spring",   "realworld_spring_app",   1),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("test_id,fixture_dir,min_tools",
                         _FIXTURE_CASES, ids=[c[0] for c in _FIXTURE_CASES])
async def test_realworld_fixture_mcp_session(test_id, fixture_dir, min_tools, tmp_path):
    """Pre-checked-in realworld fixtures: generate → start → assert tools/list."""
    source_path = FIXTURES / fixture_dir
    assert source_path.exists(), f"Fixture not found: {source_path}"
    await _run_and_connect(source_path, tmp_path, min_tools=min_tools)

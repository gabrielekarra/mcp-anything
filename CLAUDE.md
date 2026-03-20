# MCP-Anything

## What this project does
Auto-generates MCP servers from any scriptable application's source code.
One command: `mcp-anything generate <path>` → pip-installable MCP server package.

## Development
- Install: `pip install -e ".[dev,llm]"`
- Run tests: `pytest tests/ -v`
- Run CLI: `mcp-anything --help`

## Architecture
- 6-phase pipeline: ANALYZE → DESIGN → IMPLEMENT → TEST → DOCUMENT → PACKAGE
- Static detectors + optional LLM analysis (Claude API)
- Jinja2 templates for code generation (`src/mcp_anything/codegen/templates/`)
- Generated servers use `mcp` SDK's FastMCP
- Pipeline state saved as JSON manifest for resume support
- Emitter prefixes package names with `mcp_` (e.g. `my-app` → `mcp_my_app`)

## Key Files
- `src/mcp_anything/cli.py` — CLI entry point
- `src/mcp_anything/pipeline/engine.py` — phase orchestration
- `src/mcp_anything/pipeline/scope.py` — scope filtering (--include/--exclude/--review/--scope-file)
- `src/mcp_anything/pipeline/analyze.py` — phase 1: detection + AST analysis
- `src/mcp_anything/pipeline/design.py` — phase 2: capability → tool mapping
- `src/mcp_anything/pipeline/implement.py` — phase 3: code generation
- `src/mcp_anything/pipeline/test_phase.py` — phase 4: test generation + execution
- `src/mcp_anything/pipeline/document.py` — phase 5: docs generation
- `src/mcp_anything/pipeline/package.py` — phase 6: pyproject.toml + install
- `src/mcp_anything/codegen/emitter.py` — Jinja2 template rendering
- `src/mcp_anything/models/` — Pydantic models (analysis, design, manifest)
- `src/mcp_anything/url_fetcher.py` — URL spec fetching and type detection

## Detectors (17 total)
Located in `src/mcp_anything/analyzers/`:
- Python: CLI (argparse/click/typer), AST (functions/classes), Flask/FastAPI, Django DRF
- Java: Spring Boot, Spring MVC, JAX-RS/Quarkus, Micronaut
- JS/TS: Express.js
- Go: Gin, Echo, Chi, net/http, gorilla/mux
- Ruby: Rails
- Rust: Actix, Axum, Rocket, Warp
- Specs: OpenAPI 3.x/Swagger 2.x, GraphQL SDL, gRPC/Protobuf
- Other: Socket, File I/O, WebSocket, --help text parser

---

## Current Status (verified 2026-03-17)

### What's WORKING (tested end-to-end with real generation)

All of these produce valid Python, install correctly, and pass generated tests:

| Source Type | Detection | Tools | Status |
|---|---|---|---|
| Python CLI (argparse) | 0.90 confidence | Correct | Working |
| Flask REST | 0.95 | Routes → tools | Working |
| FastAPI + Pydantic | 0.95 | Routes + params | Working |
| Express.js | 0.95 | Routes → tools | Working |
| Spring Boot | 0.95 | Annotations → tools | Working |
| Go Gin | 0.95 | Routes → tools | Working |
| Django DRF ViewSets | 0.95 | Actions → tools | Working |
| OpenAPI 3.0 spec | 0.88 | Operations → tools | Working |
| gRPC / Protobuf | 0.95 | RPCs → tools | Working |
| GraphQL SDL | 0.95 | Queries/mutations → tools | Working |
| Ruby on Rails | 0.95 | Resources → tools | Working |
| Rust Actix | 0.95 | Macros → tools | Working |
| WebSocket (raw) | 0.85 | Functions → protocol_call | Working |

Working features:
- All 6 pipeline phases execute
- 6 backend strategies: cli_subcommand, cli_function, python_call, http_call, protocol_call, stub
- HTTP transport mode (`--transport http`)
- `mcp-anything serve` command
- `--resume` for interrupted pipelines
- Auto-install of generated server
- MCP config (mcp.json) generation
- AGENTS.md generation
- MCP resources and prompts generation
- LLM-enhanced analysis (optional, via Claude API)
- Auth support on backend calls (API key, Bearer, Basic, OAuth2)
- URL-based generation (`mcp-anything generate https://api.example.com/openapi.json`)
- Scope filtering: `--include`/`--exclude` patterns, `--review` mode, `--scope-file`

### What's BROKEN (bugs to fix)

**Bug 1: TEST phase runs before package is installed — FIXED 2026-03-16**
- Fixed by injecting `PYTHONPATH=<output_dir>/src` into the test subprocess env
  in `test_phase.py`, so tests can import the generated package before pip install.

**Bug 2: Package `_verify_structure` uses wrong path — FIXED 2026-03-16**
- Fixed by prepending `mcp_` to the package name in `package.py` to match
  what the emitter actually creates.

**Bug 3: Express Router routes lose mount path prefix — FIXED 2026-03-16**
- Fixed by capturing the router variable name in `_ROUTE_RE` and `_ROUTE_CHAIN_RE`,
  then looking it up in `router_prefixes` to prepend the mount path to routes.
- Also added cross-file router mount resolution: `build_router_mount_map()` scans
  all JS/TS files for `require`/`import` + `app.use()` patterns to build a
  file→prefix map, so router files in separate directories get the correct prefix.

**Bug 4: OpenTelemetry is dead code — FIXED 2026-03-16**
- Fixed by passing `_tracer` from `server.py.j2` to `register_tools()` in
  `tool_module.py.j2`, which defines a `_trace` decorator that wraps each
  tool handler with `tracer.start_as_current_span("tool.<name>")`.

**Bug 5: HTTP tools send conflicting OpenAPI defaults — FIXED 2026-03-16**
- Generated HTTP tools baked OpenAPI spec default values into Python function
  signatures (e.g. `type: str = "all"`, `affiliation: str = "owner,..."`).
  When both params had defaults, they were always sent as query params even
  when the user didn't provide them — causing 422 errors on APIs that reject
  mutually exclusive params (e.g. GitHub's `type` + `affiliation`).
- Fixed in `src/mcp_anything/codegen/renderer.py`: `_default_value()` now
  always returns `None` for optional params. Only explicitly provided values
  are sent to the backend.

**Bug 6: Docker is template-only (LOW)**
- Location: `src/mcp_anything/codegen/templates/Dockerfile.j2`
- Problem: Dockerfile is generated but never validated (no build test).
- Not a blocker — generating a Dockerfile the user can build manually is fine,
  but the ROADMAP shouldn't mark "Docker packaging" as complete.

### ROADMAP accuracy — FIXED 2026-03-16
- OTel marked complete, Docker wording clarified, v0.5.0 items moved to Completed
- Version bumped to 0.1.1

### Docs sync — FIXED 2026-03-17
- Detector count: 15 → 17 across README, ROADMAP, CLAUDE.md (JAX-RS/Quarkus, Micronaut were missing)
- Moved URL-based generation from "Future" to "Completed" in ROADMAP
- Added JAX-RS/Micronaut to ROADMAP detector list and completed sections
- README Java section now mentions JAX-RS/Quarkus and Micronaut
- Replaced old examples (ffmpeg, httpstat, click, imagemagick) with single concrete
  example: auto-generated GitHub MCP server from OpenAPI spec (1,093 tools in ~6s)
- `examples/github-server/` contains the full generated output

### Protocol backend support — IMPLEMENTED 2026-03-17
- **Problem**: `backend_protocol.py.j2` was a pure stub with TODOs; protocol/socket
  capabilities fell through to `"stub"` strategy calling nonexistent `run_subcommand()`
- **New `protocol_call` strategy**: PROTOCOL and SOCKET capabilities now get
  `protocol_call` in `design.py` instead of `stub`. Tool handlers call
  `backend.execute(tool_name, **kwargs)` with JSON-RPC messaging.
- **WebSocket backend** (`backend_protocol.py.j2`): Real implementation using
  `websockets` library — JSON-RPC 2.0 messages, retry with exponential backoff,
  connection pooling, version-compatible close detection. MQTT gets scaffolding,
  other protocols (D-Bus, OSC) get clear "manual wiring required" documentation.
- **Socket backend** (`backend_socket.py.j2`): Upgraded with `BackendError`,
  retry logic, JSON-RPC response parsing, env var configuration.
- **Tool template** (`tool_module.py.j2`): Added `protocol_call` handler between
  `cli_function` and `python_call`, imports `BackendError` for protocol tools.
- **Dependencies**: `websockets>=12.0` auto-added when protocol_call tools exist.
- **Live tested**: WebSocket JSON-RPC server → 5 calls all returned correct results.
- **Real-world tested**: Podnet/json-rpc-websocket-server → 13 tools, 15 tests pass.

### Scope filtering — IMPLEMENTED 2026-03-20
- **Problem**: Large codebases (e.g. 1500-route monoliths) expose everything as MCP tools.
  Users need to curate which capabilities are exposed incrementally.
- **Three mechanisms**:
  1. `--include`/`--exclude` CLI flags: glob patterns on capability name, source path, description
  2. `--review` mode: pause after ANALYZE, write `scope.yaml`, user edits, then `--resume`
  3. `--scope-file`: point to a pre-existing scope YAML for repeatable builds
- **Scope file semantics**: per-capability `enabled: false` = always excluded,
  `enabled: true` = always included (overrides patterns), omitted = patterns decide
- **Implementation**: `src/mcp_anything/pipeline/scope.py` + wired into engine.py
  between ANALYZE and DESIGN phases. On `--resume`, auto-loads `scope.yaml` if present.
- **28 tests** in `tests/test_scope.py` covering: file I/O, include/exclude patterns,
  scope file overrides, combined CLI+file patterns, edge cases, review/resume workflow.

### Integration Test Coverage (updated 2026-03-20)

434 total tests. `tests/test_integration.py` covers:
- Python CLI (argparse), Flask, FastAPI, Django DRF
- Express.js (including cross-file router mount prefix regression test)
- Spring Boot, JAX-RS, Micronaut
- Go Gin, Ruby Rails, Rust Actix
- OpenAPI 3.0 spec, GraphQL SDL, gRPC/Protobuf
- **WebSocket protocol** (raw websockets library, protocol_call strategy)
- HTTP transport (Dockerfile + SSE config)
- stdio transport (command-based mcp.json)
- Pipeline resume (partial run → resume completes remaining phases)
- Manifest integrity (analysis + design populated, files tracked)
- AGENTS.md content (tool names documented)
- **Scope filtering** (include/exclude patterns, scope file, review/resume workflow)

---

## Implementation Plan

### Phase 1: Fix Bugs — DONE (2026-03-16)

All three bugs (1.1 test phase ordering, 1.2 verify_structure path, 1.3 Express
Router tool naming) have been fixed. 314 unit tests pass.

### Phase 2: Add Integration Tests — DONE (2026-03-16)

20 integration tests in `tests/test_integration.py` covering all 12 source types,
transport modes, resume, manifest integrity, and AGENTS.md generation. Each test
runs the full 6-phase pipeline and verifies: file structure, Python syntax validity,
server importability, correct tool names/strategies, and generated test passing.

### Phase 3: Wire Up OpenTelemetry Properly — DONE (2026-03-16)

Passed `_tracer` to `register_tools()` and added a `_trace` decorator in
`tool_module.py.j2` that wraps each tool handler with
`tracer.start_as_current_span("tool.<name>")`.

### Phase 4: URL-based generation — DONE (2026-03-16)

`mcp-anything generate https://api.example.com/openapi.json` now works.
New module `src/mcp_anything/url_fetcher.py` handles URL detection, spec
fetching, type detection (OpenAPI JSON/YAML, Swagger, GraphQL SDL, Protobuf),
name derivation from spec title or hostname, and Swagger UI/ReDoc URL resolution.
24 tests in `tests/test_url_fetcher.py` including full pipeline integration.

### Phase 5: Protocol backend support — DONE (2026-03-17)

New `protocol_call` strategy for WebSocket and Socket backends. Replaced the
protocol stub with a real WebSocket backend using `websockets` library. Socket
backend upgraded with BackendError, retry logic, JSON-RPC parsing. Added
integration test for WebSocket protocol. 359 total tests pass.

### Phase 6: Scope Filtering — DONE (2026-03-20)

`--include`, `--exclude`, `--review`, `--scope-file` CLI flags. Scope YAML file
for per-capability curation. 28 tests in `tests/test_scope.py`. See scope.py docs.

### Phase 7: Future Features (from ROADMAP v0.6.0+)

In priority order:
1. **CLI UX** — validate `--phases` input, better error messages
2. **Generated test improvements** — mock backends so tests verify tool logic
   without needing the real service running
3. **Multi-service composition** — one MCP server proxying multiple backends
4. **Config file** — `.mcp-anything.yaml` for persistent project settings
5. **Plugin system** — custom detectors for niche frameworks

### What "Done" Looks Like

The product is "done" when:
1. `mcp-anything generate <any-codebase>` produces a working MCP server
2. The generated tests pass during generation (not just after manual install)
3. `mcp-anything serve <output>` starts the server and it responds to MCP calls
4. Users see zero warnings or errors during normal generation
5. Integration tests cover all 12+ source types automatically
6. The generated server actually proxies calls to the target application

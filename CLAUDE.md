# MCP-Anything

## What this project does
Auto-generates MCP servers from any scriptable application's source code.
One command: `mcp-anything generate <path>` → pip-installable MCP server package.

## Development
- Install: `pip install -e ".[dev,llm]"`
- Run tests: `pytest tests/ -v`
- Run CLI: `mcp-anything --help`

## Architecture
- 5-phase pipeline: ANALYZE → DESIGN → IMPLEMENT → DOCUMENT → PACKAGE
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
- `src/mcp_anything/pipeline/document.py` — phase 4: docs generation
- `src/mcp_anything/pipeline/package.py` — phase 5: pyproject.toml + install
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

## Current Status (verified 2026-03-23)

### What's WORKING (tested end-to-end with real generation)

All of these produce valid Python and install correctly.
All have integration tests + were validated against real open-source repositories.

| Source Type | Detection | Tools | Real Repo Tested |
|---|---|---|---|
| Python CLI (argparse) | 0.90 confidence | Correct | httpie/httpie |
| Flask REST | 0.95 | Routes → tools | synthetic fixture |
| FastAPI + Pydantic | 0.95 | Routes + params | synthetic fixture |
| Express.js | 0.95 | Routes → tools | synthetic fixture |
| Spring Boot | 0.95 | Annotations → tools | synthetic fixture |
| Go Gin | 0.95 | Routes → tools | synthetic fixture |
| Go Echo | 0.95 | Routes → tools | labstack/echo |
| Go Chi | 0.90 | Routes → tools | go-chi/chi |
| Go gorilla/mux | 0.90 | Routes → tools | gorilla/mux (33 tools) |
| Go net/http | 0.80 | Routes → tools | synthetic fixture |
| Django DRF ViewSets | 0.95 | Actions → tools | synthetic fixture |
| OpenAPI 3.0 spec | 0.88 | Operations → tools | GitHub API (1,093 tools) |
| gRPC / Protobuf | 0.95 | RPCs → tools | synthetic fixture |
| GraphQL SDL | 0.95 | Queries/mutations → tools | synthetic fixture |
| Ruby on Rails | 0.95 | resources + explicit routes | rails/rails activestorage (9 tools) |
| Rust Actix | 0.95 | Macros → tools | actix/examples (3 tools) |
| Rust Axum | 0.95 | .route() → tools | tokio-rs/axum examples (36 tools) |
| Rust Rocket | 0.95 | Macros → tools | SergioBenitez/Rocket examples (44 tools) |
| JAX-RS / Quarkus | 0.90 | Annotations → tools | quarkusio/rest-json-quickstart (4 tools) |
| Micronaut | 0.90 | Annotations → tools | micronaut-core benchmarks (2 tools) |
| Kotlin Spring | 0.95 | Annotations → tools | synthetic fixture |
| Kotlin JAX-RS | 0.90 | Annotations → tools | synthetic fixture |
| Spring MVC | 0.95 | Annotations → tools | synthetic fixture |
| TypeScript Express | 0.95 | Routes → tools | synthetic fixture |
| Python Click CLI | 0.90 | Commands → tools | synthetic fixture |
| Rust Warp | 0.80 | Filter chains → tools | synthetic fixture |
| WebSocket (raw) | 0.85 | Functions → protocol_call | synthetic fixture |
| Socket / XML-RPC | 0.85 | Functions → protocol_call | synthetic fixture |

Working features:
- All 5 pipeline phases execute
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

**Bug 1: TEST phase — REMOVED 2026-03-21**
- Test generation phase removed entirely. Generated tests were fake (didn't mock
  backends) and created false confidence or visible failures.

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

**Bug 7: `analyze.py` missing `Path` import — FIXED 2026-03-23**
- `AnalyzePhase._ast_fallback` used `Path | None` type hint but `Path` was never
  imported. Caused `NameError: name 'Path' is not defined` at import time, blocking
  all 25 integration tests. Fixed by adding `from pathlib import Path`.

**Bug 8: Rust Rocket/Warp not supported in analyzer — FIXED 2026-03-23**
- `rust_web_analyzer.py` returned `None` for any non-Actix/non-Axum Rust file.
  Added `_ROCKET_MACRO_RE` (handles `#[get("/path")]` with optional extra attrs like
  `data="<body>"`), `_normalize_rocket_path()` (converts `<id>` to `{id}`), and
  basic Warp filter chain detection via `_WARP_FILTER_RE`.

**Bug 11: WebSocket PROTOCOL env var overridden by FastAPI detector — FIXED 2026-03-23**
- `fake_websocket_app` (FastAPI WebSocket) had `PROTOCOL=http` set by the FastAPI
  detector, which caused `backend_protocol.py.j2` to render the generic
  `{% else %}` stub (NotImplementedError) instead of the websocket branch.
- Fixed in `design.py` `_build_backend_config()`: after processing IPC mechanism
  details, if any capability has `category == 'websocket'`, override PROTOCOL to
  'websocket'. This ensures WS apps always get the real WebSocket backend.

**Bug 12: gRPC backend was an unimplemented stub — FIXED 2026-03-23**
- gRPC tools used `protocol_call` strategy, but the protocol backend only had
  websocket and mqtt branches. gRPC apps got the generic `{% else %}` stub with
  `NotImplementedError`.
- Fixed: added `ToolImpl.grpc_service`, `grpc_method`, `grpc_proto_module` fields.
  `design.py` populates them from the capability name (`ServiceName.MethodName`).
  `implement.py` compiles `.proto` files to `proto_stubs/` using `grpcio-tools`
  if available. `backend_protocol.py.j2` now has a `{% elif protocol == 'grpc' %}`
  branch that imports compiled stubs and makes real `grpc.aio` calls.

**Bug 10: Emitter picks wrong backend for WebSocket apps — FIXED 2026-03-23**
- `emitter.py` `_emit_backend()` checked `env_vars.get("PROTOCOL") == "http"` to decide
  between `backend_http.py.j2` and `backend_protocol.py.j2`. HTTP detectors set
  `PROTOCOL=http` for all web frameworks including FastAPI WebSocket apps, causing
  the HTTP backend to be emitted for WebSocket tools. Since WebSocket tools call
  `backend.execute()` which doesn't exist on the HTTP backend, every protocol_call
  tool would raise `BackendError("no protocol mapping")` at runtime.
- Fixed in `src/mcp_anything/codegen/emitter.py`: replaced the `env_vars` check
  with pure tool-strategy logic: `is_http = has_http_tools and not has_protocol_tools`.

**Bug 9: Rails explicit route syntax not supported — FIXED 2026-03-23**
- `_parse_routes_rb` only matched `to: 'controller#action'` syntax but real Rails
  apps (including Rails own engines) use `=> 'controller#action'` and namespaced
  controllers like `'active_storage/blobs/redirect#show'`.
  Also `scope <expression> do` (not just `scope 'string' do`) was not handled,
  causing routes inside engine scope blocks to be silently skipped.
  Fixed: regex now accepts both `to:` and `=>`, allows `/` in controller paths,
  and pushes a placeholder for variable-expression scopes.

### ROADMAP accuracy — FIXED 2026-03-16
- OTel marked complete, v0.5.0 items moved to Completed
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

### High-Confidence Framework Promotion — DONE (2026-03-23)

**Root cause fixed**: `analyze.py` was missing `from pathlib import Path`, blocking
all 25 integration tests with `NameError` at import time.

**New framework coverage added** (fixtures + integration tests + real-repo validation):
- **Rust Axum**: `fake_axum_app/`, real-tested against tokio-rs/axum (36 tools)
- **Rust Rocket**: `fake_rocket_app/`, real-tested against SergioBenitez/Rocket (44 tools)
  - Fixed: `_ROCKET_MACRO_RE` now handles extra attrs like `data="<body>"`
  - Fixed: `_normalize_rocket_path()` converts `<id>` to `{id}` for path params
- **Go Echo**: `fake_go_echo_app/`, real-tested against labstack/echo (22 tools)
- **Go Chi**: `fake_go_chi_app/`, real-tested against go-chi/chi (15 tools)
- **Go gorilla/mux**: `fake_go_mux_app/`, real-tested against gorilla/mux (33 tools)
- **Go net/http**: `fake_go_nethttp_app/`, unit-tested
- **Socket/XML-RPC**: `fake_socket_xmlrpc_app/`, integration test added
- **Rails explicit routes**: `fake_rails_explicit_routes_app/` covering `=>`, `to:`,
  `namespace`, `only:`, and variable-expression `scope`. Real-tested against
  rails/rails activestorage (9 tools).

### Full Framework Coverage — DONE (2026-03-23)

All supported frameworks now have integration tests + real-repo or fixture validation.
Remaining gap closed:
- **Kotlin Spring** — `TestKotlinSpring` added (path params, 4+ tools)
- **Kotlin JAX-RS** — `TestKotlinJaxRS` added (path params, 4+ tools)
- **Spring MVC** — `TestSpringMVC` added (separate from Spring Boot test)
- **TypeScript Express** — `TestTypeScriptExpress` added
- **Python Click CLI** — `TestPythonClick` added (`cli_subcommand` strategy)
- **Rust Warp** — `fake_warp_app` fixture created + `TestRustWarp` added

### Integration Test Coverage (updated 2026-03-23)

484 total tests. `tests/test_integration.py` covers every supported framework.
`tests/test_functional.py` (35 tests) verifies tool functions **actually call the backend**
with correct method/path/params by injecting mock backends into generated tool modules.
`tests/test_e2e_http.py` (4 tests) proves end-to-end round-trips against real servers:
HTTP (Flask→mock HTTP server), CLI (subprocess spawn), WebSocket (real WS JSON-RPC server),
gRPC (real gRPC server with compiled proto stubs).
Every supported framework has a functional test — not just a structural one.
- Python CLI (argparse + Click), Flask, FastAPI, Django DRF
- Express.js (JS + TypeScript, including cross-file router mount prefix regression)
- Spring Boot, Spring MVC, JAX-RS, Micronaut
- **Kotlin Spring, Kotlin JAX-RS**
- **Go Gin, Go Echo, Go Chi, Go gorilla/mux, Go net/http** (all 5 Go frameworks)
- **Ruby Rails** (resources + explicit `=>` + `to:` + namespace + only:)
- **Rust Actix, Rust Axum, Rust Rocket, Rust Warp** (all 4 Rust frameworks)
- OpenAPI 3.0 spec, GraphQL SDL, gRPC/Protobuf
- **WebSocket protocol** (raw websockets library, protocol_call strategy)
- **Socket/XML-RPC** (SimpleXMLRPCServer, socket IPC detection)
- HTTP transport (SSE config)
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
server importability, and correct tool names/strategies.

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
2. **Multi-service composition** — one MCP server proxying multiple backends
3. **Config file** — `.mcp-anything.yaml` for persistent project settings
4. **Plugin system** — custom detectors for niche frameworks

### What "Done" Looks Like

The product is "done" when:
1. `mcp-anything generate <any-codebase>` produces a working MCP server
2. Tool descriptions are clean and useful for LLMs
3. `mcp-anything serve <output>` starts the server and it responds to MCP calls
4. Users see zero warnings or errors during normal generation
5. Integration tests cover all 12+ source types automatically
6. The generated server actually proxies calls to the target application

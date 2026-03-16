# Roadmap

Current version: **0.1.1**

## Completed

### Core Pipeline
- [x] 6-phase pipeline: ANALYZE → DESIGN → IMPLEMENT → TEST → DOCUMENT → PACKAGE
- [x] JSON manifest for pipeline state and resume support
- [x] Post-generation AST validation of all generated Python
- [x] Auto-install target project and generated server dependencies
- [x] MCP config (`mcp.json`) auto-generation for Claude Code

### Python Analysis
- [x] AST-based function/class/parameter extraction
- [x] Click decorator parsing (`@click.option`, `@click.argument`, `click.Choice`)
- [x] Typer parameter extraction (`typer.Option`, `typer.Argument`)
- [x] Argparse subcommand and argument detection
- [x] Entry point detection (`__main__.py`, `if __name__ == '__main__':`)
- [x] Smart filtering (skip tests, private methods, factories, `sys.exit()` callers)
- [x] Docstring parsing (Google, NumPy, Sphinx styles)

### IPC Detection (15 detectors)
- [x] CLI (argparse, click, typer, fire, getopt)
- [x] Socket (TCP/UDP, xmlrpc, ZeroMQ)
- [x] Python API (ctypes, cffi, pybind11)
- [x] Protocol (WebSocket, gRPC, D-Bus, MQTT)
- [x] File I/O (JSON, YAML, CSV, SQLite)
- [x] Flask/FastAPI (route decorators, APIRouter, Blueprint)
- [x] Spring Boot (Java annotations, REST controllers)
- [x] OpenAPI/Swagger (spec file ingestion)
- [x] Express.js (route definitions, Router mounts)
- [x] Django REST Framework (ViewSets, APIViews)
- [x] Go web (Gin, Echo, Chi, net/http, gorilla/mux)
- [x] Ruby on Rails (controllers, routes.rb)
- [x] Rust web (Actix, Axum, Rocket, Warp)
- [x] GraphQL (SDL schemas, Graphene, Strawberry, Apollo)
- [x] gRPC/Protobuf (.proto service definitions)

### HTTP Framework Support
- [x] **FastAPI** — route extraction, `Query()`/`Path()`/`Body()` params, `Depends()` filtering, APIRouter prefixes, Pydantic model detection
- [x] **Flask** — `@app.route()` with `methods=`, `<type:param>` path params, Blueprint support
- [x] **Spring Boot** — `@RestController`, `@GetMapping`/`@PostMapping`/etc., `@RequestParam`/`@PathVariable`/`@RequestBody`, `application.properties` port extraction

### OpenAPI/Swagger
- [x] OpenAPI 3.x and Swagger 2.x parsing
- [x] `$ref` resolution for schemas and parameters
- [x] Request body property extraction from referenced schemas
- [x] Enum values, defaults, and type mapping
- [x] Server/host/basePath extraction
- [x] Recursive spec file discovery
- [x] Works with spec-only directories (no source code needed)

### Code Generation
- [x] 5 implementation strategies: `cli_subcommand`, `cli_function`, `python_call`, `http_call`, `stub`
- [x] Async HTTP backend with `httpx` for REST API proxying
- [x] CLI backend with subprocess execution
- [x] Auto-generated `run_<app>` tool for single-purpose CLI apps
- [x] Resource implementations (status, commands, config)
- [x] `--help` parser for non-Python CLIs

### LLM Enhancement (Optional)
- [x] Claude API analysis for capability discovery
- [x] LLM-enhanced tool descriptions
- [x] LLM-assisted tool grouping

### Authentication & Reliability (v0.2.0)
- [x] **HTTP authentication support** — API keys (header/query), Bearer tokens, Basic auth, OAuth2 client credentials
- [x] **Environment variable configuration** — secrets via env vars (`<APP>_TOKEN`, `<APP>_API_KEY`, `<APP>_USERNAME`/`<APP>_PASSWORD`), never hardcoded
- [x] **Error handling improvements** — retry with exponential backoff on 429/5xx, configurable timeout (`<APP>_TIMEOUT`), structured `BackendError` with status code/method/path/response
- [x] **Base URL configuration** — configurable via `<APP>_BASE_URL` env var, auto-extracted from OpenAPI servers/host

### More Languages & Frameworks (v0.3.0)
- [x] **Express.js / Node.js** — route extraction from `app.get()`, `router.post()`, path params (`:id`), `req.params`/`req.query`/`req.body` extraction, cross-file router mount prefix resolution
- [x] **Go Gin / Echo / Chi / net-http** — route extraction, route groups, path params, query/body parameter detection, gorilla/mux support
- [x] **Django REST Framework** — ViewSets (list/create/retrieve/update/destroy), `@action` custom actions, serializer field extraction, `urls.py` pattern parsing
- [x] **Ruby on Rails** — `routes.rb` parsing (`resources`, `namespace`, `only:` constraints, explicit routes), controller action extraction, strong parameters
- [x] **Rust Actix/Axum** — Actix attribute macros (`#[get]`, `#[post]`), Axum `.route()` chaining, struct field extraction for `Query`/`Json` params

### Smarter Analysis (v0.4.0)
- [x] **Request/response schema extraction** — infer JSON body shapes from Pydantic models, Java POJOs, TypeScript interfaces
- [x] **Cross-file dependency resolution** — follow imports to find related types and models (Python, Java, TypeScript)
- [x] **GraphQL support** — SDL schema parsing, query/mutation/subscription extraction with argument types
- [x] **gRPC/protobuf support** — `.proto` file parsing, service/method extraction, message field mapping, streaming detection
- [x] **WebSocket endpoint support** — FastAPI WebSocket, Django Channels, Socket.IO, ws library detection

### Enterprise & Agentic Engineering (v0.5.0)
- [x] **Streamable HTTP transport** — `--transport http` flag to generate servers with SSE/streamable HTTP instead of stdio, configurable host/port via env vars
- [x] **MCP Prompts generation** — auto-generate server-delivered prompts (skills) for usage guidance and debugging from analysis results
- [x] **MCP Resources as dynamic docs** — tool index and category documentation served as always-up-to-date MCP resources
- [x] **AGENTS.md generation** — full tool index with parameters, resources, prompts, and MCP config for coding agent discoverability
- [x] **OpenTelemetry integration** — TracerProvider initialization + `_trace` decorator wraps each tool handler with `start_as_current_span`
- [x] **Docker packaging** — auto-generated `Dockerfile` for HTTP transport (template-only, no build validation)
- [x] **`mcp-anything serve`** — run generated servers directly without installing, with transport override support

### Bug Fixes & Quality (v0.1.1)
- [x] **Test phase ordering** — generated tests now pass during generation (PYTHONPATH injection)
- [x] **Package structure verification** — `_verify_structure` uses correct `mcp_` prefix
- [x] **Express Router mount prefix** — cross-file prefix resolution for router-mounted routes
- [x] **OpenTelemetry instrumentation** — `_tracer` now wraps tool handlers with spans (was dead code)
- [x] **Integration test suite** — 20 end-to-end tests covering all 12+ source types, transport modes, resume, and manifest integrity

---

## Planned

### v0.6.0 — Quality & Ecosystem

- [ ] **OAuth/token auth on MCP server** — protect the MCP server itself with OAuth2 or token-based auth (not just backend API auth)
- [ ] **Generated test improvements** — integration tests with mocked backends, snapshot testing
- [ ] **Plugin system** — custom detectors and analyzers as pip-installable plugins
- [ ] **Multi-service composition** — generate a single MCP server that proxies to multiple backend services
- [ ] **Hot reload** — watch source changes and regenerate automatically
- [ ] **Config file support** — `.mcp-anything.yaml` for project-specific settings

### Future

- [x] **URL-based generation** — `mcp-anything generate https://api.example.com/openapi.json` with auto-detection of OpenAPI/Swagger/GraphQL/Protobuf specs, Swagger UI/ReDoc URL resolution, and name derivation
- [ ] **npm/cargo/go package support** — generate MCP servers in other languages
- [ ] **MCP server marketplace** — publish generated servers to a registry
- [ ] **VS Code extension** — right-click a project to generate an MCP server
- [ ] **CI/CD integration** — GitHub Action to auto-regenerate on source changes

---

## Tested Against

Real-world projects used for end-to-end validation:

| Project | Type | Tools Generated |
|---------|------|-----------------|
| [httpstat](https://github.com/reorx/httpstat) | Python CLI (argparse) | 2 tools (run_httpstat, print_help) |
| [gs-rest-service](https://github.com/spring-guides/gs-rest-service) | Spring Boot (Java) | 1 tool (get_greeting) |
| [full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) | FastAPI (Python) | 49 tools (23 HTTP routes + utilities) |
| [Swagger Petstore](https://petstore3.swagger.io/) | OpenAPI 3.x spec | 19 tools |
| [RealWorld Conduit](https://github.com/gothinkster/realworld) | OpenAPI 3.x spec (YAML) | 19 tools |

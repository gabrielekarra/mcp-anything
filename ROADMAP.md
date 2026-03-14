# Roadmap

Current version: **0.1.0**

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

### IPC Detection (8 detectors)
- [x] CLI (argparse, click, typer, fire, getopt)
- [x] Socket (TCP/UDP, xmlrpc, ZeroMQ)
- [x] Python API (ctypes, cffi, pybind11)
- [x] Protocol (WebSocket, gRPC, D-Bus, MQTT)
- [x] File I/O (JSON, YAML, CSV, SQLite)
- [x] Flask/FastAPI (route decorators, APIRouter, Blueprint)
- [x] Spring Boot (Java annotations, REST controllers)
- [x] OpenAPI/Swagger (spec file ingestion)

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

---

### v0.2.0 — Authentication & Reliability
- [x] **HTTP authentication support** — API keys (header/query), Bearer tokens, Basic auth, OAuth2 client credentials
- [x] **Environment variable configuration** — secrets via env vars (`<APP>_TOKEN`, `<APP>_API_KEY`, `<APP>_USERNAME`/`<APP>_PASSWORD`), never hardcoded
- [x] **Error handling improvements** — retry with exponential backoff on 429/5xx, configurable timeout (`<APP>_TIMEOUT`), structured `BackendError` with status code/method/path/response
- [x] **Base URL configuration** — configurable via `<APP>_BASE_URL` env var, auto-extracted from OpenAPI servers/host

---

## In Progress

_Nothing currently in progress._

---

## Planned

### v0.3.0 — More Languages & Frameworks

- [ ] **Express.js / Node.js** — route extraction from `app.get()`, `router.post()`, middleware chains
- [ ] **Go net/http / Gin / Echo** — handler extraction from `http.HandleFunc`, Gin route groups
- [ ] **Django REST Framework** — ViewSets, serializers, URL patterns
- [ ] **Ruby on Rails** — `routes.rb` parsing, controller action extraction
- [ ] **Rust Actix/Axum** — handler extraction from route macros

### v0.4.0 — Smarter Analysis

- [ ] **Request/response schema extraction** — infer JSON body shapes from Pydantic models, Java POJOs, TypeScript interfaces
- [ ] **Cross-file dependency resolution** — follow imports to find related types and models
- [ ] **GraphQL support** — schema introspection, query/mutation extraction
- [ ] **gRPC/protobuf support** — `.proto` file parsing, service/method extraction
- [ ] **WebSocket endpoint support** — bidirectional communication tools

### v0.5.0 — Developer Experience

- [ ] **`mcp-anything serve`** — run the generated server directly without installing
- [ ] **Hot reload** — watch source changes and regenerate automatically
- [ ] **Interactive mode** — review and customize detected tools before generation
- [ ] **Docker integration** — auto-start target app in container before proxying
- [ ] **Config file support** — `.mcp-anything.yaml` for project-specific settings

### v0.6.0 — Quality & Ecosystem

- [ ] **Generated test improvements** — integration tests with mocked backends, snapshot testing
- [ ] **MCP resource templates** — richer resource types (logs, metrics, database schemas)
- [ ] **Plugin system** — custom detectors and analyzers as pip-installable plugins
- [ ] **MCP prompt generation** — auto-generate MCP prompts from docstrings and usage patterns
- [ ] **Multi-service composition** — generate a single MCP server that proxies to multiple backend services

### Future

- [ ] **URL-based generation** — `mcp-anything generate https://api.example.com/openapi.json`
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

# Roadmap

Current version: **0.2.0**

---

## Completed

### v0.2.0 — Domain pipeline

- [x] **`mcp-anything build --brief`** — brief-driven generation from a YAML domain description + any data source
- [x] **Phase 1: Domain modeling** — LLM extracts entities, use cases, access patterns, glossary from brief + OpenAPI/gRPC/GraphQL
- [x] **Phase 2: Tool design** — LLM applies 2026 MCP rules: group CRUD, lifecycle operations, agent-optimised descriptions, verbose flag, composed tools
- [x] **Phase 3: Emit (Python/FastMCP)** — inline code generation, AST validation, all tools registered, Dockerfile, pyproject.toml
- [x] **Phase 4: Skill bundle** — LLM generates `SKILL.md` (agent guide with recipes, gotchas, anti-patterns) and `quick_queries.json`
- [x] **Phase 5: Validation harness** — LLM generates `eval_cases.json`, conformance report against 29 CONTRACT.md items
- [x] **CONTRACT.md** — 29 testable output contract items (C-01..C-29) covering tools, auth, transport, telemetry, packaging, SKILL.md
- [x] **Conformance suite** — `ConformanceParity`, `EvalRunner`, `ConformanceReporter` in `src/mcp_anything/conformance/`
- [x] **Discovery endpoint** — every generated server exposes `GET /.well-known/mcp`
- [x] **Telemetry** — anonymised per-call logging via `MCP_TELEMETRY_ENDPOINT`, never logs parameter values
- [x] **27 static detectors** — added Kotlin Spring/JAX-RS, Spring MVC, TypeScript Express, Python Click, Rust Warp, Go Echo/Chi/gorilla/mux/net-http, Socket/XML-RPC, Rails explicit route syntax
- [x] **Scope filtering** — `--include`/`--exclude` glob patterns, `--review` mode, `--scope-file` for curated builds
- [x] **Protocol backends** — real WebSocket (JSON-RPC), gRPC (grpcio-tools), Socket/XML-RPC with retry and error handling
- [x] **Full framework integration tests** — 484 tests covering all 27 source types, functional tests, e2e HTTP/CLI/WebSocket/gRPC

### v0.1.x — Foundation

- [x] 5-phase legacy pipeline: ANALYZE → DESIGN → IMPLEMENT → DOCUMENT → PACKAGE
- [x] JSON manifest with resume support (`--resume`)
- [x] 6 backend strategies: `cli_subcommand`, `cli_function`, `python_call`, `http_call`, `protocol_call`, `stub`
- [x] HTTP authentication: API key, Bearer token, Basic auth, OAuth2 client credentials
- [x] HTTP transport: `--transport http` with SSE, configurable host/port, Docker packaging
- [x] TypeScript / mcp-use target: `--target mcp-use`
- [x] URL-based generation: `mcp-anything generate https://api.example.com/openapi.json`
- [x] MCP Prompts, Resources, AGENTS.md generation
- [x] OpenTelemetry tracing integration
- [x] `mcp-anything serve` command
- [x] AST validation of all generated Python

---

## Planned

### v0.3.0 — TypeScript emit for domain pipeline

- [ ] **`--target mcp-use` support for `build`** — TypeScript/mcp-use emit phase in the domain pipeline (currently Python/FastMCP only)
- [ ] **Emit parity tests** — conformance suite verifies both emitters produce equivalent tool signatures

### v0.4.0 — Multi-source and composition

- [ ] **Multi-service composition** — single MCP server proxying to multiple backends, tool namespacing per service
- [ ] **Config file** — `.mcp-anything.yaml` for persistent project-level settings (brief path, target, scope file, output dir)

### v0.5.0 — Ecosystem

- [ ] **Plugin system** — custom detectors and analyzers as pip-installable plugins
- [ ] **GitHub Action** — auto-regenerate on source changes in CI/CD
- [ ] **VS Code extension** — right-click any project to generate an MCP server

### Future

- [ ] **MCP server registry** — publish generated servers for discovery and reuse
- [ ] **Live eval runner** — run `eval_cases.json` against a live server and report pass rate
- [ ] **npm / cargo / go package support** — generated servers in languages other than Python/TypeScript

---

## Tested Against

Real-world projects used for end-to-end validation:

| Project | Type | Tools |
|---|---|---|
| [Stripe OpenAPI spec](https://github.com/stripe/openapi) | OpenAPI 3.x (domain pipeline) | 13 grouped tools, full payment lifecycle |
| [github/rest-api-description](https://github.com/github/rest-api-description) | OpenAPI 3.x (domain pipeline) | 22 grouped tools, 100% in-scope coverage |
| [tokio-rs/axum examples](https://github.com/tokio-rs/axum) | Rust Axum | 36 tools |
| [SergioBenitez/Rocket examples](https://github.com/SergioBenitez/Rocket) | Rust Rocket | 44 tools |
| [gorilla/mux](https://github.com/gorilla/mux) | Go gorilla/mux | 33 tools |
| [labstack/echo](https://github.com/labstack/echo) | Go Echo | 22 tools |
| [go-chi/chi](https://github.com/go-chi/chi) | Go Chi | 15 tools |
| [rails/rails activestorage](https://github.com/rails/rails) | Ruby on Rails | 9 tools |
| [quarkusio/rest-json-quickstart](https://github.com/quarkusio/quarkus-quickstarts) | JAX-RS / Quarkus | 4 tools |
| [micronaut-core benchmarks](https://github.com/micronaut-projects/micronaut-core) | Micronaut | 2 tools |
| [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) | FastAPI | 49 tools |
| [spring-guides/gs-rest-service](https://github.com/spring-guides/gs-rest-service) | Spring Boot | 1 tool |
| [Swagger Petstore](https://petstore3.swagger.io/) | OpenAPI 3.x | 19 tools |

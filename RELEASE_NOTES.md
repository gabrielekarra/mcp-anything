# v0.2.0 — Domain pipeline

The headline feature of this release is `mcp-anything build --brief` — a brief-driven pipeline that takes a plain-language description of what agents should be able to do and produces a production-ready MCP server automatically.

## What's new

### `build` command — brief-driven generation

Write a short YAML file describing your domain, use cases, and data source. The LLM pipeline does the rest:

```bash
mcp-anything build --brief my-api.yaml -o ./my-mcp-server
```

Five LLM phases run end-to-end:
1. **Domain modeling** — extracts entities, access patterns, use cases, and glossary from your brief + data source
2. **Tool design** — groups related operations, writes agent-optimised descriptions, applies 2026 MCP design rules
3. **Emit** — generates valid Python (FastMCP) or TypeScript (mcp-use) with all tools wired up
4. **Skill bundle** — generates `SKILL.md` (agent guide with recipes, gotchas, anti-patterns) and `quick_queries.json`
5. **Validation harness** — generates `eval_cases.json` and a `conformance_report.json` against 29 contract items

### 2026 tool design rules

The tool design phase applies a set of rules automatically:
- **Group CRUD**: ≥3 operations on the same resource → single `manage_X(operation=...)` tool
- **Compact + verbose**: every tool has a `verbose` flag; compact by default
- **Discovery endpoint**: every server exposes `GET /.well-known/mcp`
- **Telemetry**: anonymised per-call logging via `MCP_TELEMETRY_ENDPOINT`
- **Dockerfile**: every server ships with a container-ready Dockerfile

### Validated against real APIs

- **Stripe**: 13 grouped tools covering the full payment lifecycle — 10+ capabilities absent from the official 15-tool Stripe agent toolkit
- **GitHub**: 22 grouped tools covering 100% of the in-scope API surface — matching the official 51-tool server at 57% fewer tools

### 27 static detectors (generate mode)

Added Kotlin Spring, Kotlin JAX-RS, Spring MVC, TypeScript Express, Python Click, Rust Warp, Go Echo, Go Chi, Go gorilla/mux, Go net/http, Socket/XML-RPC, and Rails explicit route syntax.

### Conformance suite

`CONTRACT.md` defines 29 testable output contract items (C-01..C-29). Every generated server is checked automatically; results appear in `conformance_report.json`.

## Installation

```bash
pip install -U mcp-anything
```

# v0.1.2 — Founder trial hardening

This release tightens the path from `mcp-anything generate ...` to a working MCP server for real production codebases, with a specific focus on HTTP onboarding and frameworks the upcoming founder trial depends on.

## Highlights

- **Direct OpenAPI file input** — `mcp-anything generate ./openapi.json` now works without wrapping the spec in a directory first
- **HTTP onboarding fixes** — generated docs now explain upstream `*_BASE_URL` and upstream auth environment variables
- **Safer `mcp.json` generation** — stdio configs now include required env placeholders for HTTP proxy tools, and the `mcp-anything serve` fallback preserves them if editable install fails
- **Better Express coverage** — added support for `routing-controllers` decorator-based apps and fixed HTTP body handling in generated tools
- **Stronger validation** — added regression coverage for codegen, integration, CLI, and new framework detection paths

## Real-repo validation

- `spring-guides/gs-rest-service`
- `spring-projects/spring-petclinic`
- `w3tecch/express-typescript-boilerplate`
- `eclipse-ee4j/jersey` (`examples/helloworld-webapp`)

These checks exercised real Spring, Express/TypeScript, and Jersey/JAX-RS repositories and validated the generated MCP packages and fallback configs end to end.

## Installation

```bash
pip install -U mcp-anything
```

See the [README](https://github.com/gabrielekarra/mcp-anything#readme) for the latest quickstart and deployment notes.

# v0.1.0 — First public release

MCP-Anything auto-generates fully functional MCP server packages from any codebase. Point it at source code — Python, Java, Go, Rust, Ruby, TypeScript — and get a pip-installable MCP server in minutes, no manual wrapping required.

## Key capabilities

- **15 static detectors** — CLI (argparse, Click, Typer), HTTP frameworks (FastAPI, Flask, Spring Boot, Express, Django, Rails, Gin, Actix, Axum), OpenAPI/Swagger, GraphQL, gRPC/Protobuf, WebSockets
- **5-phase pipeline** — Analyze, Design, Implement, Test, Document, Package — with JSON manifest for resume support
- **Multiple backend strategies** — CLI subprocess, HTTP proxy, Python call, stub — auto-selected based on what the codebase exposes
- **Full MCP protocol** — Tools, Resources, Prompts, AGENTS.md generation for agent discoverability
- **HTTP transport** — `--transport http` for remote deployment with OpenTelemetry tracing and Docker packaging
- **LLM-enhanced analysis** — Optional Claude API integration for better tool descriptions and grouping

## Installation

```bash
pip install mcp-anything
```

## Quick start

```bash
mcp-anything generate /path/to/any/app
```

See the [README](https://github.com/gabrielekarra/mcp-anything#readme) for full documentation, examples, and usage.

## What's next

- Desktop software showcase (Blender, GIMP, Audacity)
- Plugin system for custom detectors

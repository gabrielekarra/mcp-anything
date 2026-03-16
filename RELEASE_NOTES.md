# v0.1.0 — First public release

MCP-Anything auto-generates fully functional MCP server packages from any codebase. Point it at source code — Python, Java, Go, Rust, Ruby, TypeScript — and get a pip-installable MCP server in minutes, no manual wrapping required.

## Key capabilities

- **15 static detectors** — CLI (argparse, Click, Typer), HTTP frameworks (FastAPI, Flask, Spring Boot, Express, Django, Rails, Gin, Actix, Axum), OpenAPI/Swagger, GraphQL, gRPC/Protobuf, WebSockets
- **6-phase pipeline** — Analyze, Design, Implement, Test, Document, Package — with JSON manifest for resume support
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
- OAuth/token auth on the MCP server itself
- Plugin system for custom detectors

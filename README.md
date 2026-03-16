# MCP-Anything

**One command to turn any software into an MCP server.**

Not just REST APIs. Not just OpenAPI specs. Any software — CLI tools, desktop apps, Python libraries, web frameworks, even codebases with no API at all.

[![Discord](https://img.shields.io/badge/Discord-Join%20us-7289da?logo=discord&logoColor=white)](https://discord.gg/5zCwnfJBxG)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/mcp-anything.svg)](https://pypi.org/project/mcp-anything/)

![mcp-anything demo](promo.gif)

## The problem

There are 9,000+ MCP servers today. Almost all of them are hand-built.

Each one takes days or weeks of work. [blender-mcp](https://github.com/ahujasid/blender-mcp) has 17,600+ stars and took months to build. Every desktop application — Blender, GIMP, Audacity, LibreOffice — needs someone to manually write the bridge code between the application and the MCP protocol.

Meanwhile, OpenAPI-to-MCP generators (Speakeasy, Stainless, FastMCP, liblab, etc.) only work if your software already has a REST API spec. Desktop software doesn't. CLI tools don't. Most Python libraries don't.

**MCP-Anything bridges the gap.** It reads source code directly — Python AST, CLI help output, HTTP route decorators, OpenAPI specs, GraphQL schemas, gRPC definitions — and generates a fully functional, pip-installable MCP server package.

## How we compare

|  | OpenAPI-to-MCP tools | Hand-built servers | **MCP-Anything** |
|--|---------------------|--------------------|-------------------|
| **Input required** | OpenAPI/Swagger spec | Manual code | Any source code |
| **Desktop software** | No | Yes (manual) | Yes (auto) |
| **CLI tools** | No | Yes (manual) | Yes (auto) |
| **Web frameworks** | Partial | Yes (manual) | Yes (auto) |
| **Time to server** | Minutes | Days to weeks | Minutes |
| **Test suite** | No | Manual | Auto-generated |
| **Documentation** | Partial | Manual | Auto-generated |

## Quick start

```bash
pip install mcp-anything
mcp-anything generate /path/to/software
```

That's it. You get a complete MCP server package in `mcp-<name>-server/`, ready to install and use.

## How it works

MCP-Anything runs a 6-phase pipeline:

1. **Analyze** — Scans your codebase with 15 static detectors to find IPC mechanisms (CLI args, HTTP routes, gRPC services, GraphQL schemas, WebSockets, sockets, file I/O).
2. **Design** — Maps discovered capabilities to MCP tool specifications with typed parameters, descriptions, and grouping. Optional LLM enhancement via Claude API.
3. **Implement** — Generates Python server code using Jinja2 templates. Picks the right backend strategy (subprocess, HTTP proxy, Python call) for each tool.
4. **Test** — Generates a pytest test suite and validates all output with AST parsing.
5. **Document** — Produces AGENTS.md, MCP resources, and server-delivered prompts for agent discoverability.
6. **Package** — Emits a pip-installable package with pyproject.toml, mcp.json config, and optional Dockerfile.

Pipeline state is saved as JSON — use `--resume` to pick up where you left off.

## What it detects

**Python** — FastAPI, Flask, Django REST, Click, Typer, argparse, entry points, Pydantic models, docstrings (Google/NumPy/Sphinx)

**Java** — Spring Boot controllers, annotations, request/path/body parameters

**JavaScript/TypeScript** — Express.js routes, Router mounts, req.params/query/body

**Go** — Gin, Echo, Chi, net/http, gorilla/mux route groups and handlers

**Ruby** — Rails controllers, routes.rb, resources, strong parameters

**Rust** — Actix, Axum, Rocket, Warp attribute macros and route chaining

**API specs** — OpenAPI 3.x, Swagger 2.x (with $ref resolution), GraphQL SDL, gRPC/Protobuf

**Other** — WebSocket endpoints, cross-file import resolution, CLI `--help` parsing for any language

## Output

```
mcp-<name>-server/
├── src/<name>/
│   ├── server.py        # FastMCP server (stdio or HTTP)
│   ├── backend.py       # Backend adapter (CLI/HTTP/API)
│   ├── tools/           # Tool modules by category
│   ├── prompts.py       # Server-delivered MCP prompts
│   └── resources.py     # Dynamic MCP resources
├── tests/               # Generated pytest tests
├── AGENTS.md            # Tool index for coding agents
├── Dockerfile           # Container deployment (HTTP mode)
├── mcp.json             # Claude Code / MCP client config
└── pyproject.toml       # pip install -e .
```

## Usage

```bash
# Full pipeline
mcp-anything generate /path/to/app

# Override the server name
mcp-anything generate /path/to/app --name my-service

# Static analysis only (no Claude API key needed)
mcp-anything generate /path/to/app --no-llm

# Force a specific backend strategy
mcp-anything generate /path/to/app --backend cli

# Run specific phases
mcp-anything generate /path/to/app --phases analyze,design

# Resume from a previous run
mcp-anything generate /path/to/app --resume

# Generate with HTTP transport for remote deployment
mcp-anything generate /path/to/app --transport http

# Analysis only (no code generation)
mcp-anything analyze /path/to/app

# Run a generated server without installing
mcp-anything serve ./mcp-myapp-server

# Check generation status
mcp-anything status ./mcp-myapp-server
```

## Backend strategies

| Strategy | When used | Example |
|----------|-----------|---------|
| `cli_subcommand` | Target app has CLI subcommands | `git`, `docker`, Click/Typer apps |
| `cli_function` | Single-purpose CLI tool | `httpstat`, `curl` |
| `http_call` | Target app exposes HTTP endpoints | FastAPI, Flask, Spring Boot |
| `python_call` | Target app is a Python library | Direct function invocation |
| `stub` | Capability detected but no clear invocation path | Placeholder for manual wiring |

## Examples

| Project | Type | Tools generated | Command |
|---------|------|-----------------|---------|
| [httpstat](https://github.com/reorx/httpstat) | Python CLI (argparse) | 2 | `mcp-anything generate ./httpstat --name httpstat` |
| [click](https://github.com/pallets/click) | Python library (129 functions, 71 classes) | 50 | `mcp-anything generate ./click --name click` |

See [`examples/`](examples/) for the full generated server code, mcp.json configs, and details.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full roadmap. Top priorities:

- [ ] Desktop software showcase (Blender, GIMP, Audacity)
- [ ] OAuth/token auth on the MCP server itself
- [ ] Generated test improvements with mocked backends
- [ ] Plugin system for custom detectors
- [ ] URL-based generation (`mcp-anything generate https://api.example.com/openapi.json`)

## Development

```bash
pip install -e ".[dev,llm]"
pytest tests/ -v
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for architecture details and how to add new detectors.

---

Stop writing MCP servers by hand.

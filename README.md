# MCP-Anything

[![Discord](https://img.shields.io/badge/Discord-Join%20us-7289da?logo=discord&logoColor=white)](https://discord.gg/5zCwnfJBxG)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

![mcp-anything demo](promo.gif)

**Turn any codebase into an MCP server. One command.**

```bash
mcp-anything generate /path/to/app
```

Point it at any project — Python, Go, Java, Rust, Ruby, TypeScript — and get a production-ready MCP server package. No manual wrapping. No boilerplate.

## Why

MCP is becoming the standard protocol for connecting AI agents to tools. But wrapping existing software into MCP servers is tedious, repetitive work.

`mcp-anything` automates the entire process: it analyzes your code, extracts every endpoint and command, and generates a fully typed, tested, documented MCP server — with support for the latest MCP features like streamable HTTP transport, server-delivered prompts, and agent-discoverable tool indexes.

## Quick Start

```bash
git clone https://github.com/gabrielekarra/mcp-anything.git
cd mcp-anything
pip install -e ".[dev,llm]"

# Generate a server
mcp-anything generate /path/to/your/app
```

## What Gets Generated

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
└── pyproject.toml       # pip install -e .
```

## Local or Remote

**Local (stdio)** — the default. Runs as a subprocess, zero config:

```bash
mcp-anything generate /path/to/app
```

**Remote (HTTP)** — streamable HTTP/SSE transport for production deployment:

```bash
mcp-anything generate /path/to/app --transport http
```

This adds OpenTelemetry tracing, a Dockerfile, and an HTTP endpoint your agents can reach over the network.

## Supported Languages & Frameworks

| Language | Frameworks |
|----------|-----------|
| Python | FastAPI, Flask, Django REST, Click, Typer, argparse |
| Java | Spring Boot |
| TypeScript/JS | Express.js |
| Go | Gin, Echo, Chi, net/http, gorilla/mux |
| Ruby | Rails |
| Rust | Actix, Axum, Rocket, Warp |
| Any | OpenAPI/Swagger specs, GraphQL SDL, gRPC/Protobuf |

Plus WebSocket detection (FastAPI-WS, Django Channels, Socket.IO), cross-file import resolution, and schema extraction from Pydantic models, Java POJOs, and TypeScript interfaces.

## Built for the Agentic Era

MCP is evolving beyond simple tool calls. `mcp-anything` generates servers that use the full protocol:

- **MCP Prompts** — server-delivered skills that teach agents how to use your tools effectively
- **MCP Resources** — dynamic, always-up-to-date documentation served as resources, not stale markdown
- **AGENTS.md** — a structured tool index that coding agents (Cursor, Claude Code, Copilot) can discover automatically
- **OpenTelemetry** — traces every tool invocation so you can monitor what your agents are actually doing
- **Docker-ready** — one command to containerize and deploy your MCP server anywhere

## Commands

```bash
mcp-anything generate /path/to/app     # Full pipeline: analyze → package
mcp-anything analyze /path/to/app      # Analysis only
mcp-anything serve ./mcp-myapp-server  # Run without installing
mcp-anything status ./mcp-myapp-server # Check generation status
```

### Key Flags

```
--transport http     Streamable HTTP instead of stdio
--name NAME          Override server name
--no-llm             Static analysis only (no API key needed)
--no-install         Skip dependency installation
--resume             Resume from saved pipeline state
```

## Example

```bash
mcp-anything generate /path/to/httpstat --name httpstat
```

Add to your Claude Code config:

```json
{
  "mcpServers": {
    "httpstat": {
      "command": "mcp-httpstat"
    }
  }
}
```

Or with HTTP transport:

```json
{
  "mcpServers": {
    "httpstat": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

## How It Works

```
ANALYZE → DESIGN → IMPLEMENT → TEST → DOCUMENT → PACKAGE
```

15 static detectors scan your codebase for IPC patterns (CLI args, HTTP routes, gRPC services, GraphQL schemas, WebSocket endpoints). Optional LLM analysis via Claude API enhances tool descriptions and grouping. Jinja2 templates emit valid, tested Python. Pipeline state is saved as JSON for resume support.

## Development

```bash
pip install -e ".[dev,llm]"
pytest tests/ -v
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the architecture guide and how to add new detectors.

See [ROADMAP.md](ROADMAP.md) for what's shipped and what's next.

## License

MIT

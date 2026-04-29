# MCP-Anything

**Describe what you want. Get a production-ready MCP server.**

[![Discord](https://img.shields.io/badge/Discord-Join%20us-7289da?logo=discord&logoColor=white)](https://discord.gg/5zCwnfJBxG)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/mcp-anything.svg)](https://pypi.org/project/mcp-anything/)

![mcp-anything](banner.png)

MCP-Anything turns any data source into a fully implemented MCP server — from a plain-language brief describing what agents should be able to do. It also works directly from codebases, OpenAPI specs, gRPC protos, and GraphQL schemas. Two modes, one tool.

---

## Quick start

**1. Install**

```bash
pip install mcp-anything
export ANTHROPIC_API_KEY=sk-...
```

**2. Write a brief** — describe your domain and point at your data source

```yaml
# my-api.yaml
server_name: payments-mcp
domain_description: >
  A payment API for managing customers, invoices, and subscriptions.
use_cases:
  - "Create a customer with email and name"
  - "Issue an invoice and send it to the customer"
  - "Create and cancel subscriptions"
  - "Issue refunds"
data_source_path: ./openapi.json   # local file or URL
data_source_kind: openapi          # openapi | graphql | grpc
auth_method: bearer_token
backend_target: fastmcp
```

**3. Build**

```bash
mcp-anything build --brief my-api.yaml -o ./my-mcp-server
```

**4. Run**

```bash
cd my-mcp-server
pip install -e .
python -m mcp_payments_mcp.server
```

That's it. You now have a running MCP server. Add it to your agent:

```json
{
  "mcpServers": {
    "payments": { "command": "python", "args": ["-m", "mcp_payments_mcp.server"] }
  }
}
```

---

## Two modes

### `build` — brief-driven (recommended)

The LLM reads your brief, groups related operations into ergonomic tools, writes agent-optimised descriptions, and generates the full server package including a SKILL.md agent guide and an eval harness.

### `generate` — codebase scanner (no brief required)

Point at source code or a spec URL. Static detection, no LLM needed.

```bash
# From a local codebase
mcp-anything generate /path/to/your/app

# From a URL (OpenAPI, GraphQL, gRPC)
mcp-anything generate https://api.example.com/openapi.json
```

---

## What you get

Both modes produce a complete, pip-installable package:

```
my-mcp-server/
├── mcp_<name>/
│   ├── server.py          # FastMCP server (stdio or HTTP)
│   ├── tools/             # One file per tool, HTTP calls via httpx
│   ├── discovery.py       # GET /.well-known/mcp
│   └── telemetry.py       # Anonymised per-call logging
├── SKILL.md               # Agent-readable usage guide (recipes, gotchas, anti-patterns)
├── quick_queries.json     # Eval set derived from your use cases
├── eval_cases.json        # LLM-generated evaluation cases
├── conformance_report.json
├── Dockerfile
└── pyproject.toml
```

**SKILL.md** is the key output. It's a structured document written for AI agents — not humans — that lists every tool with its parameters, operation modes, usage recipes, gotchas, and anti-patterns. Agents read it before making any calls, which dramatically reduces hallucinations and misuse.

---

## How tools get designed

The LLM follows 2026 MCP design rules automatically:

**Group CRUD.** Three or more operations on the same resource become a single `manage_X(operation=...)` tool. Fewer tools, broader coverage, easier for agents to use.

**Full lifecycle.** The tool design phase reads your use cases and maps them to full API coverage — not just the happy path. Create, read, update, delete, list, and any lifecycle transitions (confirm, capture, cancel, finalize, void) are all included.

**Compact + verbose.** Every tool has a `verbose` flag. By default it returns only the essential fields. Pass `verbose=true` to get the full API response with metadata.

**Discovery endpoint.** Every server exposes `GET /.well-known/mcp` listing all tools and their disclosure levels.

---

## Concrete example: Stripe

The [official Stripe agent toolkit](https://github.com/stripe/agent-toolkit) ships 15 flat tools covering create and list operations only. No updates, no deletes, no payment intent lifecycle, no checkout sessions, no coupons.

Running mcp-anything against the Stripe OpenAPI spec with a 41-item brief:

```bash
mcp-anything build --brief stripe.yaml -o ./stripe-mcp --target fastmcp
```

| | Official Stripe toolkit | **mcp-anything** |
|---|---|---|
| Tools | 15 flat tools | **13 grouped tools** |
| Customers | create, list | create, read, **update, delete**, list |
| Payment intents | list only | create, read, list, **confirm, capture, cancel** |
| Invoices | create, finalize | create, read, list, **send, pay, void** |
| Subscriptions | create, cancel | create, read, **update**, cancel, **resume**, list |
| Checkout sessions | ✗ | **create, retrieve, expire** |
| Coupons & promo codes | ✗ | **full support** |

13 tools, 100% brief coverage, 10+ capabilities absent from the official toolkit.

---

## Concrete example: GitHub

The [official GitHub MCP server](https://github.com/github/github-mcp-server) is a hand-built Go project. Building it took months.

```bash
mcp-anything build --brief github.yaml -o ./github-mcp
```

| | Official (hand-built) | **mcp-anything** |
|---|---|---|
| Build time | Months | ~30 seconds |
| Tools | 51 flat tools | **22 grouped tools** |
| Coverage | Curated subset | **100% of in-scope operations** |
| Language | Go | Python |

22 tools cover the same 51 operations — a 57% reduction in surface area with no loss of capability. The grouping (`manage_repository`, `manage_issue`, `manage_pull_request`, etc.) is what agents actually prefer.

See [`examples/github-server/`](examples/github-server/) for the full generated output.

---

## Output targets

| | `fastmcp` (default) | `mcp-use` |
|---|---|---|
| Language | Python | TypeScript |
| SDK | FastMCP | mcp-use |
| Transport | stdio / HTTP | HTTP (port 3000) |
| Install | `pip install -e .` | `npm install && npm run dev` |

```bash
mcp-anything build --brief my-api.yaml --target mcp-use
mcp-anything generate /path/to/app --target mcp-use
```

---

## Transport

**stdio (default):** server runs as a local subprocess.

```json
{
  "mcpServers": {
    "my-app": { "command": "mcp-my-app", "args": [] }
  }
}
```

**HTTP (recommended for shared/remote use):**

```bash
mcp-anything generate /path/to/app --transport http
# server runs at http://localhost:8000/sse
```

```json
{
  "mcpServers": {
    "my-app": { "url": "http://localhost:8000/sse" }
  }
}
```

HTTP lets you deploy once and connect from any agent session, CI pipeline, or team member.

---

## Framework support (generate mode)

27 source types across 8 ecosystems. Static detection, no LLM required.

| Ecosystem | Framework / Source |
|---|---|
| **Python** | argparse, Click, Typer, Flask, FastAPI, Django REST Framework |
| **Java / Kotlin** | Spring Boot, Spring MVC, JAX-RS / Quarkus, Micronaut |
| **JavaScript / TypeScript** | Express.js |
| **Go** | Gin, Echo, Chi, gorilla/mux, Fiber, net/http |
| **Ruby** | Rails |
| **Rust** | Actix-web, Axum, Rocket, Warp |
| **API Specs** | OpenAPI 3.x / Swagger 2.x, GraphQL SDL, gRPC / Protobuf |
| **Protocol / IPC** | WebSocket (JSON-RPC), MQTT, ZeroMQ, XML-RPC, raw socket, D-Bus |

---

## Scoping

Control which capabilities get exposed without editing the generated code.

```bash
# Include / exclude by glob
mcp-anything generate ./my-app --include "/api/v2/*" --exclude "/internal/*"

# Review mode: pause after analysis, curate scope.yaml, then resume
mcp-anything generate ./my-app --review
vim mcp-my-app-server/scope.yaml
mcp-anything generate ./my-app --resume

# Reusable scope file
mcp-anything generate ./my-app --scope-file ./mcp-scope.yaml
```

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full roadmap. See [CONTRIBUTING.md](CONTRIBUTING.md) to contribute.

---

## Star History

<a href="https://www.star-history.com/?repos=Type-MCP%2Fmcp-anything&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=Type-MCP/mcp-anything&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=Type-MCP/mcp-anything&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/image?repos=Type-MCP/mcp-anything&type=date&legend=top-left" />
 </picture>
</a>

---

Stop writing MCP servers by hand.

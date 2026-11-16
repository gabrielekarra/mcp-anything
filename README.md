# MCP-Anything

**Describe what you want. Get a production-ready MCP server. Then prove it is good.**

[![tests](https://github.com/gabrielekarra/mcp-anything/actions/workflows/tests.yml/badge.svg)](https://github.com/gabrielekarra/mcp-anything/actions/workflows/tests.yml)
[![Discord](https://img.shields.io/badge/Discord-Join%20us-7289da?logo=discord&logoColor=white)](https://discord.gg/5zCwnfJBxG)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/mcp-anything.svg)](https://pypi.org/project/mcp-anything/)

![mcp-anything](banner.jpg)

```bash
mcp-anything https://petstore3.swagger.io/api/v3/openapi.json --install claude-code   # a spec in, a server in your client
mcp-anything grade "npx -y @modelcontextprotocol/server-memory"                        # how usable is any MCP server?
```

MCP-Anything turns an API spec, a codebase, or a plain-language brief into a fully implemented MCP server, and grades any MCP server, its own or anyone else's, on how easy it is for an agent to use. It works with Claude, GPT, or a model running on your machine.

<!-- demo: record docs/demo.tape, commit docs/demo.gif, then replace this comment with ![demo](docs/demo.gif) -->

---

## Install

```bash
pip install mcp-anything            # add [llm] for Claude models: pip install "mcp-anything[llm]"
```

The LLM steps use the model you choose (see [Models](#models)); everything also works without one, with `--no-llm`.

### Or inside Claude Code

No install step: the skill installs the CLI for you on first use.

```
/plugin marketplace add gabrielekarra/mcp-anything
/plugin install mcp-anything@mcp-anything
```

Then just ask: *"turn this OpenAPI spec into an MCP server"* or *"wrap my Flask app as MCP tools"*.

---

## One command: from a source to a server

```bash
mcp-anything https://api.example.com/openapi.json
mcp-anything ./openapi.yaml --install cursor
mcp-anything ./my-flask-app --name shop
```

Give it a spec URL, a spec file (OpenAPI, GraphQL, `.proto`) or a code folder. It drafts the brief from the source (the spec's title, description, tags and operations, rewritten by the model when one is available), builds the server, and saves the brief as `brief.yaml` next to it, so you can edit it and rebuild:

```bash
mcp-anything build --brief mcp-petstore-api-server/brief.yaml -o mcp-petstore-api-server
```

### Add it to your client

```bash
mcp-anything install ./mcp-petstore-api-server --client claude-code
```

`--client` takes `claude-code`, `claude-desktop`, `cursor` or `vscode` (repeat it for several). The entry is merged into the client's config, the old file is backed up once, and running it again changes nothing. `--url http://host/mcp` installs a server that is already running over HTTP, and `--print` shows the entry instead of writing it.

---

## Grade any MCP server

```bash
mcp-anything grade "npx -y @modelcontextprotocol/server-filesystem ."   # a command (stdio)
mcp-anything grade https://example.com/mcp                             # a URL (streamable HTTP)
mcp-anything grade ./mcp-petstore-api-server                           # a server folder
mcp-anything grade tools.json --format markdown                        # a saved tools/list result
```

```
./mcp-petstore-api-server
Grade A  95/100   7 tools, about 1,025 tokens of tool list

-  5.1  G10 CRUD operations not grouped: Several tools act on the same resource: pet (5).
         create_pet, delete_pet, get_pet, list_pets, update_pet
         Fix: Consider one manage_<resource>(operation=...) tool where several tools act on the same resource: fewer, broader tools are easier to choose from.
```

The grade is a static review of the tool list, the part of a server an agent actually sees, on fifteen rules. Every rule is deterministic: the same server always gets the same score, with no model involved.

| Rule | What it checks |
|---|---|
| G01, G02 | How many tools there are, and how many tokens the tool list costs on every request |
| G03, G04, G05 | Missing, vague or overlong descriptions |
| G06, G07, G08, G14 | Parameters without a description or a type, opaque objects, allowed values written in prose instead of an enum |
| G09 | Inconsistent or invalid tool names |
| G10 | Several tools acting on the same resource that could be one |
| G11, G12 | Destructive tools without `destructiveHint`, read-only tools without `readOnlyHint` |
| G13 | Near-duplicate tools |
| G15 | Missing or invalid input schemas |

It says how easy a server is to choose from and call correctly, not whether its tools work: [`mcp-anything eval`](#eval-against-a-live-server) measures that.

### A badge, and a check in CI

```bash
mcp-anything grade ./my-server --badge grade.svg --min-score 80
```

`--badge` writes an SVG badge, `--shields` a [shields.io endpoint](https://shields.io/badges/endpoint-badge) file, and `--min-score` exits with an error below the threshold. In GitHub Actions:

```yaml
- uses: gabrielekarra/mcp-anything@main
  with:
    target: python -m my_server
    min-score: 80
```

The action writes the report to the job summary and exposes `score` and `grade` as outputs.

### The leaderboard

[`scripts/leaderboard.py`](scripts/leaderboard.py) grades the servers listed in [`scripts/servers.yaml`](scripts/servers.yaml) (the MCP reference servers and several official ones) and writes `docs/leaderboard.md`, dated and with the version used, so every number can be reproduced. Add a server with a pull request.

---

## Eval against a live server

```bash
mcp-anything eval ./my-server                                   # call each case's tool, check the result
mcp-anything eval ./my-server --agent --model ollama:qwen3:8b   # give each use case to a model with the tools
```

Every server built with a brief ships `eval_cases.json`. Direct mode calls each case's tool with its inputs and checks the output pattern or the expected error. `--agent` gives each use case to a model with the server's tools and passes when it calls the right one, within `--max-steps`. `--min-pass 0.8` fails CI below a pass rate; `--format json` for machines.

---

## Build from a brief

For full control, write the brief yourself:

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

```bash
mcp-anything build --brief my-api.yaml -o ./my-mcp-server --install claude-code
```

The model reads your brief, groups related operations into ergonomic tools, writes descriptions for agents, and generates the full package, including a `SKILL.md` agent guide and an eval set.

### `generate`: the codebase scanner

Point at source code or a spec, with no brief: static detection, no model needed.

```bash
mcp-anything generate /path/to/your/app
mcp-anything generate https://api.example.com/openapi.json
```

---

## Models

```bash
mcp-anything build --brief my-api.yaml --model ollama:qwen3:8b
export MCP_ANYTHING_MODEL=openai:gpt-5
```

| `--model` | Provider | Needs |
|---|---|---|
| `anthropic:claude-opus-5-5` (default) or any `claude-*` id | Anthropic | `pip install "mcp-anything[llm]"`, `ANTHROPIC_API_KEY` |
| `openai:<model>` | OpenAI | `OPENAI_API_KEY` |
| `openrouter:<model>` | OpenRouter | `OPENROUTER_API_KEY` |
| `ollama:<model>` | Ollama (`OLLAMA_HOST`, default `localhost:11434`) | nothing |
| `lmstudio:<model>`, `llamacpp:<model>`, `vllm:<model>` | local OpenAI-compatible servers | nothing |

`MCP_ANYTHING_BASE_URL` points any non-Anthropic provider at another address, and `MCP_ANYTHING_CONTEXT` sets Ollama's context window (32k by default, so long specs are not silently cut). If the model is unavailable or answers badly, each phase falls back to its deterministic version instead of failing.

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
├── brief.yaml             # The brief, when drafted by the one-command mode
├── quick_queries.json     # Eval set derived from your use cases
├── eval_cases.json        # Evaluation cases for mcp-anything eval
├── conformance_report.json
├── Dockerfile
└── pyproject.toml
```

Every parameter carries its description from the spec, allowed values become enums, and tools are annotated as read-only or destructive from their HTTP method. **SKILL.md** is written for agents, not humans: every tool with its parameters, usage recipes, gotchas and anti-patterns.

### How tools get designed

**Group CRUD.** Three or more operations on the same resource become a single `manage_X(operation=...)` tool. Fewer tools, broader coverage, easier for agents to choose from.

**Full lifecycle.** The tool design phase maps your use cases to full API coverage: create, read, update, delete, list, and lifecycle transitions (confirm, capture, cancel, finalize, void).

**Compact + verbose.** Every tool has a `verbose` flag. By default it returns only the essential fields; `verbose=true` returns the full API response with metadata.

**Discovery endpoint.** Every server exposes `GET /.well-known/mcp` listing all tools and their disclosure levels.

See [`examples/`](examples/) for generated servers.

---

## Output targets

| | `fastmcp` (default) | `mcp-use` |
|---|---|---|
| Language | Python | TypeScript |
| SDK | FastMCP | mcp-use |
| Transport | stdio / HTTP | HTTP (port 8000) |
| Install | `pip install -e .` | `npm install && npm run dev` |

```bash
mcp-anything build --brief my-api.yaml --target mcp-use
mcp-anything generate /path/to/app --target mcp-use
```

## Transport

**stdio (default):** the server runs as a local subprocess.

**HTTP (recommended for shared/remote use):**

```bash
mcp-anything generate /path/to/app --transport http
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

## Scoping

Control which capabilities get exposed without editing the generated code.

```bash
# Include / exclude by glob
mcp-anything generate ./my-app --include "/api/v2/*" --exclude "/internal/*"

# Review mode: pause after analysis, curate scope.yaml, then resume
mcp-anything generate ./my-app --review
mcp-anything generate ./my-app --resume

# Reusable scope file
mcp-anything generate ./my-app --scope-file ./mcp-scope.yaml
```

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the roadmap and [CONTRIBUTING.md](CONTRIBUTING.md) to contribute.

---

## Star History

<a href="https://www.star-history.com/?repos=gabrielekarra%2Fmcp-anything&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=gabrielekarra/mcp-anything&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=gabrielekarra/mcp-anything&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/image?repos=gabrielekarra/mcp-anything&type=date&legend=top-left" />
 </picture>
</a>

---

Stop writing MCP servers by hand, and stop guessing whether they are any good.

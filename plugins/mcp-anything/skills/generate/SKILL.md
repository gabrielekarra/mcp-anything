---
name: generate
description: Turn a codebase, an OpenAPI/gRPC/GraphQL spec, or a plain-language description of an API into a production-ready MCP server, using mcp-anything. Use when the user wants to expose software, an API, a CLI tool, or a service as MCP tools for Claude or other agents.
when_to_use: "Use when the user asks to 'turn X into an MCP server', 'make an MCP server for Y', 'wrap this API/CLI as MCP tools', or wants agents to be able to call their software."
argument-hint: "[path-or-url] [--target fastmcp|mcp-use]"
allowed-tools: Bash(mcp-anything *) Bash(pip install *) Bash(pip show *) Bash(command -v mcp-anything)
---

## Generate an MCP server with mcp-anything

mcp-anything (https://github.com/gabrielekarra/mcp-anything) turns a codebase, an API spec, or a
plain-language brief into a working MCP server — Python/FastMCP by default, or TypeScript/mcp-use
with `--target mcp-use`.

### 1. Make sure the CLI is current

The MCP ecosystem moves fast; prefer the latest source over a possibly-stale PyPI release:

!`command -v mcp-anything >/dev/null 2>&1 && mcp-anything --version || echo "not installed"`

If it's missing, install from the repo (not just `pip install mcp-anything` — PyPI can lag):

```bash
pip install --upgrade "mcp-anything[llm] @ git+https://github.com/gabrielekarra/mcp-anything.git"
```

### 2. Find out what to expose

Ask only what's missing:
- **The source**: a local codebase path, or an OpenAPI/GraphQL/gRPC spec (file path or URL).
- **What agents should be able to do with it** — a sentence or two of use cases is enough for
  the richer path below.

### 3. Pick a path

- **Quick scan** (no use-case framing given): `mcp-anything generate <path-or-url> -o <output-dir>`
- **Recommended — curated, agent-optimized tools** (use cases given): write a short domain brief
  to a temp YAML file (`server_name`, `description`, `use_cases: [...]`), then:
  `mcp-anything build --brief <brief.yaml> --data-source <path-or-spec> -o <output-dir> --no-llm`
  — drop `--no-llm` when `ANTHROPIC_API_KEY` is set; grouping and descriptions are noticeably
  better with it.
- Add `--target mcp-use` to either command for TypeScript instead of Python.

### 4. Report back

`mcp-anything` prints the output directory, tool count, and an MCP client config snippet
(`mcpServers: {...}`) — surface that, plus how to try it: `pip install -e <output-dir>` (Python)
or `npm install` (TypeScript) in the output directory, then add the snippet to the user's client
config.

### 5. Optional: validate

`mcp-anything validate <output-dir>` checks the generated server against mcp-anything's own
output contract (tool shape, transport, telemetry, packaging).

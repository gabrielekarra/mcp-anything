# MCP-Anything

[https://github.com/user-attachments/assets/promo.mp4](https://github.com/gabrielekarra/mcp-anything/blob/main/promo.mp4)

Generate an MCP server from any codebase in one command.

```bash
mcp-anything generate /path/to/app
```

`mcp-anything` scans a project's source code, detects how it works (CLI, Python API, sockets, protocols, file I/O), and generates a fully functional MCP server package — ready to install and use with Claude Code or any MCP client.

## Install

```bash
git clone https://github.com/gabrielekarra/mcp-anything.git
cd mcp-anything
pip install -e ".[dev,llm]"
```

The `[llm]` extra adds the Anthropic SDK for LLM-enhanced analysis and tool descriptions. Set `ANTHROPIC_API_KEY` to enable it, or use `--no-llm` for fully static analysis.

## Usage

Generate a full MCP server from any project:

```bash
mcp-anything generate /path/to/app
```

This runs the 6-phase pipeline (analyze, design, implement, test, document, package) and outputs a pip-installable server package.

### Options

```
--name NAME          Override server name (default: directory name)
-o, --output-dir DIR Output directory (default: ./mcp-<name>-server)
--backend TYPE       Force backend: cli, socket, file, python-api, protocol
--no-llm             Skip LLM analysis, use static detection only
--no-install         Skip auto-installing dependencies
--phases PHASES      Run specific phases (e.g. analyze,design)
--resume             Resume from saved manifest
```

### Other commands

```bash
mcp-anything analyze /path/to/app     # Run analysis only
mcp-anything design /path/to/app      # Run analysis + design
mcp-anything status ./mcp-myapp-server # Check generation status
```

## What It Does

### Analysis

- **AST analysis** of Python source code — extracts functions, parameters, types, defaults, docstrings
- **Click/Typer support** — extracts rich parameter info from `@click.option()`, `@click.argument()`, `typer.Option()`, `typer.Argument()`
- **Argparse detection** — finds subcommands via `add_parser()` calls
- **FastAPI/Flask** — route extraction, `Query()`/`Path()`/`Body()` params, `Depends()` filtering, APIRouter prefixes
- **Spring Boot** — Java `@RestController`, `@GetMapping`/`@PostMapping`, `@RequestParam`/`@PathVariable`/`@RequestBody`
- **OpenAPI/Swagger** — parses OpenAPI 3.x and Swagger 2.x specs with `$ref` resolution (works without source code)
- **8 IPC detectors** — CLI, socket, Python API, protocol, file I/O, Flask/FastAPI, Spring Boot, OpenAPI
- **`--help` parser** — for non-Python CLIs (Go, Rust, Node), parses help output to extract commands and flags
- **Smart filtering** — skips test functions, private methods, function factories, `sys.exit()` callers, generic methods

### Code Generation

- **5 implementation strategies**: `cli_subcommand`, `cli_function`, `python_call`, `http_call`, `stub`
- **Async HTTP backend** with `httpx` for REST API proxying
- **Auto-generated `run_<app>` tool** for single-purpose CLI apps
- **Jinja2 templates** with Python-specific filters
- **Post-generation validation** — all generated Python is verified via `ast.parse()`
- **Auto-install** — installs target project and generated server dependencies
- **MCP config generation** — ready-to-paste `mcp.json` for Claude Code

### Output

The generated server package includes:

```
mcp-<name>-server/
├── src/<name>/
│   ├── server.py        # FastMCP server entry point
│   ├── backend.py       # CLI/API backend adapter
│   └── tools/           # Tool modules by category
├── tests/               # Generated pytest tests
├── docs/                # Generated documentation
└── pyproject.toml       # Ready to pip install
```

## Example

Generate an MCP server for [httpstat](https://github.com/reorx/httpstat):

```bash
mcp-anything generate /path/to/httpstat --name httpstat
```

This produces a server with a `run_httpstat` tool that runs HTTP timing analysis:

```json
{
  "mcpServers": {
    "httpstat": {
      "command": "python",
      "args": ["-m", "httpstat.server"]
    }
  }
}
```

Tested against real projects — see [ROADMAP.md](ROADMAP.md#tested-against) for the full list.

## Architecture

```
6-phase pipeline: ANALYZE → DESIGN → IMPLEMENT → TEST → DOCUMENT → PACKAGE
```

- Static detectors + optional LLM analysis (Claude API)
- Jinja2 templates for code generation
- Generated servers use the `mcp` SDK's FastMCP
- Pipeline state saved as JSON manifest for resume support

## Development

```bash
pip install -e ".[dev,llm]"
pytest tests/ -v
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full development guide, architecture overview, and how to add new detectors/analyzers.

See [ROADMAP.md](ROADMAP.md) for planned features and what's been completed.

## License

MIT

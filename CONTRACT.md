# mcp-anything Output Contract v1.0

Both emitters (Python/FastMCP, TypeScript/mcp-use) MUST satisfy every item applicable to the
selected backend. Items are verified by the conformance suite and referenced by ID in
`conformance_report.json`.

Items marked **[both]** apply to both emitters.  
Items marked **[py]** apply to the Python/FastMCP emitter only.  
Items marked **[ts]** apply to the TypeScript/mcp-use emitter only.

---

## Discovery [both]

**C-01** — `GET /.well-known/mcp` returns HTTP 200 with `Content-Type: application/json`.  
**C-02** — Discovery response includes `server_name`, `version`, and `tool_count`.  
**C-03** — Discovery response includes a `tool_groups` array listing each group with its `disclosure_level`.  

---

## Tool Shape [both]

**C-04** — Each tool has a non-empty `name`, `description`, and `parameters` array (may be empty).  
**C-05** — Tool description is written in agent-consumer voice: present tense, action-oriented, ≥ 20 characters, does not start with "Wraps" or "Calls".  
**C-06** — No 1:1 API mirroring: when the data source exposes ≥ 3 CRUD operations on the same resource, they MUST be collapsed into a single grouped tool.  
**C-07** — Every tool group exposes a single entry-point with an `operation` discriminator parameter whose enum lists the collapsed operations.  
**C-08** — At least one `ComposedTool` is present when the domain brief contains a use-case that requires ≥ 3 sequential tool calls.  

---

## Progressive Disclosure [both]

**C-09** — The default tool listing (no flags) returns only tools with `disclosure_level = "default"`.  
**C-10** — Passing `verbose=true` to any tool returns the full response payload including metadata.  
**C-11** — Tools with `disclosure_level = "verbose"` are excluded from the default listing but callable directly by name.  

---

## Response Shape [both]

**C-12** — Default tool responses are compact: contain only the fields declared in the tool spec's `compact_fields` list.  
**C-13** — When `verbose=true`, the response includes the full payload plus a `_meta` key with `latency_ms` and `backend_status`.  

---

## Transport

**C-14** — **[py]** Server starts on stdio transport without requiring environment variables beyond optional API keys. The mcp-use (TypeScript) target is HTTP-first — see C-15.  
**C-15** — **[both]** Server starts on HTTP transport at `0.0.0.0:8000`. **[py]**: via `--transport http` (or `MCP_TRANSPORT=http`). **[ts]**: via `npm run start`, the mcp-use CLI's production command; `package.json` pins its `--host`/`--port` to match.  
**C-16** — **[both]** Server is stateless: no in-process mutable state persists between tool calls.  

---

## Infrastructure [both]

**C-17** — Output directory contains a `Dockerfile` that builds a runnable image with no embedded secrets.  
**C-18** — The Dockerfile exposes port 8000 and reads all API keys from environment variables at runtime.  
**C-19** — The server emits a structured log line per tool call: `{tool, status, latency_ms}` (anonymized — no parameter values).  
**C-20** — Telemetry endpoint is configurable via `MCP_TELEMETRY_ENDPOINT` env var; silently disabled when unset.  

---

## Skill Bundle [both]

**C-21** — `SKILL.md` is present in the output directory.  
**C-22** — `SKILL.md` contains all required sections: Overview, Tools, Usage Patterns, Gotchas, Recipe Workflows, Composed-Call Examples, Anti-patterns.  
**C-23** — `quick_queries.json` is present and contains one entry per use-case from the domain brief, each with `id`, `brief_item_id`, `prompt`, `expected_tool`, and `notes` keys.  

---

## Validation [both]

**C-24** — `eval_cases.json` is present and contains ≥ 1 happy-path case and ≥ 1 edge-case per tool.  
**C-25** — `conformance_report.json` is present and valid when `--run-eval` is passed.  
**C-26** — `coverage_ratio` in `conformance_report.json` is ≥ `eval_threshold` (default 0.80).  

---

## Python/FastMCP Specifics [py]

**C-27** — Generated server imports without error under Python ≥ 3.11.  
**C-28** — `pyproject.toml` declares `mcp>=2.0` and `fastmcp>=4.0` as dependencies.  

---

## TypeScript/mcp-use Specifics [ts]

**C-27** — Generated server compiles without error under `tsc --noEmit` with `strict: true`.  
**C-28** — `package.json` declares `mcp-use>=2.5` as a dependency. The mcp-use package supplies the
underlying `@modelcontextprotocol/{core,client,server,ext-apps}` v2 SDK transitively — generated
code does not import from `@modelcontextprotocol/sdk` (the pre-v2 package) directly.  

---

## How to verify

Run the conformance suite against a generated server:

```bash
mcp-anything validate --output-dir <server-dir> [--run-eval] [--ci]
```

Each item ID appears in `conformance_report.json` under `contract_checks`:

```json
{
  "contract_checks": [
    {"id": "C-01", "passed": true},
    {"id": "C-05", "passed": false, "reason": "Tool 'list_items' description starts with 'Wraps'"}
  ]
}
```

Structural items (C-01..C-05, C-09, C-12, C-17..C-24, C-27..C-28) are checked without a
running server. Transport and response-shape items (C-10, C-11, C-13..C-16, C-19..C-20,
C-25..C-26) require `--run-eval`.

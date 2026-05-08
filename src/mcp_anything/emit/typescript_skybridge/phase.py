"""TypeScript/Skybridge emit phase (Phase 3, skybridge target)."""

import json
import subprocess
from pathlib import Path
from typing import Optional

from mcp_anything.emit.base import EmitPhase
from mcp_anything.models.design import ServerDesign, ToolSpec
from mcp_anything.models.domain import DomainModel
from mcp_anything.pipeline.context import PipelineContext


def _to_pascal(name: str) -> str:
    return "".join(w.capitalize() for w in name.replace("-", "_").split("_"))


class TypeScriptSkybridgeEmitPhase(EmitPhase):
    """Emits a TypeScript/Skybridge MCP + ChatGPT App server from a ServerDesign."""

    name = "emit"
    backend_target = "skybridge"

    async def execute(self, ctx: PipelineContext) -> None:
        design = self._load_design(ctx)
        domain_model = self._load_domain_model(ctx)

        output_dir = Path(ctx.manifest.output_dir) / "skybridge"
        output_dir.mkdir(parents=True, exist_ok=True)

        use_llm = not getattr(ctx.options, "no_llm", False)
        emitter = TypeScriptSkybridgeEmitter(design, domain_model, output_dir, use_llm=use_llm)
        generated = emitter.emit_all()

        if self._tsc_available():
            ctx.console.print("    Type-checking generated TypeScript...")
            errors = self._validate_typescript(output_dir)
            if errors:
                ctx.console.print(f"    [yellow]TypeScript warnings: {errors[:3]}[/yellow]")

        ctx.manifest.generated_files.extend([f"skybridge/{f}" for f in generated])
        ctx.console.print(f"    Generated {len(generated)} Skybridge files")

        contract_results = self.validate_contract(design, output_dir)
        ctx.manifest.contract_check_results = [c.model_dump() for c in contract_results]
        failed = [c for c in contract_results if not c.passed]
        if failed:
            ctx.console.print(
                f"    [yellow]Contract warnings (Skybridge): {[c.id for c in failed]}[/yellow]"
            )

        ctx.save_manifest()

    def _load_design(self, ctx: PipelineContext) -> ServerDesign:
        if ctx.manifest.design:
            return ctx.manifest.design
        if ctx.manifest.tool_spec:
            return ServerDesign.model_validate(ctx.manifest.tool_spec)
        raise RuntimeError("No design available for Skybridge code generation.")

    def _load_domain_model(self, ctx: PipelineContext) -> Optional[DomainModel]:
        if ctx.manifest.domain_model:
            try:
                return DomainModel.model_validate(ctx.manifest.domain_model)
            except Exception:
                return None
        return None

    def _tsc_available(self) -> bool:
        try:
            result = subprocess.run(["tsc", "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _validate_typescript(self, output_dir: Path) -> list[str]:
        tsconfig = output_dir / "tsconfig.json"
        if not tsconfig.exists():
            return []
        try:
            result = subprocess.run(
                ["tsc", "--noEmit", "--project", str(tsconfig)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=output_dir,
            )
            if result.returncode != 0:
                return result.stdout.splitlines()[:10]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return []


class TypeScriptSkybridgeEmitter:
    """Renders TypeScript/Skybridge server + React view files from a ServerDesign."""

    def __init__(
        self,
        design: ServerDesign,
        domain_model: Optional[DomainModel],
        output_dir: Path,
        use_llm: bool = True,
    ) -> None:
        self.design = design
        self.domain_model = domain_model
        self.output_dir = output_dir
        self.use_llm = use_llm
        self.generated_files: list[str] = []

    def emit_all(self) -> list[str]:
        self._emit_server()
        self._emit_views()
        self._emit_discovery()
        self._emit_telemetry()
        self._emit_vite_config()
        self._emit_index_html()
        self._emit_dockerfile()
        self._emit_package_json()
        self._emit_tsconfig()
        self._emit_readme()
        return self.generated_files

    def _write(self, rel_path: str, content: str) -> None:
        full = self.output_dir / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)
        self.generated_files.append(rel_path)

    # ------------------------------------------------------------------ #
    # server.ts
    # ------------------------------------------------------------------ #

    def _emit_server(self) -> None:
        registrations = "\n\n".join(
            self._render_tool_registration(t) for t in self.design.tools
        )
        content = f'''/**
 * Skybridge MCP + ChatGPT App server for {self.design.server_name}
 * Generated by mcp-anything — runs as both an MCP server and a ChatGPT App.
 */
import {{ McpServer }} from "skybridge/server";
import {{ z }} from "zod";
import {{ recordCall }} from "./telemetry.js";
import {{ getDiscoveryInfo }} from "./discovery.js";

const server = new McpServer({{
  name: "{self.design.server_name}",
  version: "1.0.0",
  description: `{self.design.server_description}`,
}});

{registrations}

// /.well-known/mcp discovery endpoint (CONTRACT C-01..C-03)
server.resource("mcp-discovery", "/.well-known/mcp", async () => {{
  return {{
    contents: [{{
      uri: "/.well-known/mcp",
      mimeType: "application/json",
      text: JSON.stringify(getDiscoveryInfo()),
    }}],
  }};
}});

server.run().catch(console.error);
'''
        self._write("src/server.ts", content)

    def _render_tool_registration(self, tool: ToolSpec) -> str:
        input_schema_lines = self._render_zod_shape(tool)
        call_code = self._render_call(tool)

        input_schema_block = (
            f"    inputSchema: {{\n{input_schema_lines}\n    }},\n"
            if input_schema_lines.strip()
            else ""
        )

        return f'''server.registerTool(
  {{
    name: "{tool.name}",
    description: `{tool.description}`,
{input_schema_block}  }},
  async (args: any) => {{
    const start = Date.now();
    let _status = "ok";
    try {{
{call_code}
    }} catch (err) {{
      _status = "error";
      throw err;
    }} finally {{
      recordCall("{tool.name}", Date.now() - start, _status);
    }}
  }}
);'''

    def _render_zod_shape(self, tool: ToolSpec) -> str:
        lines = []
        has_verbose = False
        for p in tool.parameters:
            if p.name == "verbose":
                has_verbose = True
            z_type = self._to_zod_type(p.type)
            if not p.required:
                z_type = f"{z_type}.optional()"
            lines.append(
                f"      {json.dumps(p.name)}: {z_type}.describe({json.dumps(p.description)}),"
            )
        if not has_verbose:
            # CONTRACT C-10: every tool must accept a verbose flag (compact responses by default).
            lines.append(
                '      "verbose": z.boolean().optional()'
                '.describe("Return full details instead of the compact summary."),'
            )
        return "\n".join(lines)

    def _render_auth_blocks(self) -> tuple[str, str]:
        """Return (header_block, query_block) for auth injection in fetch calls.

        Reads design.backend.auth and emits TS that pulls credentials from env vars.
        Returns ("", "") when no auth is configured.
        """
        auth = getattr(self.design.backend, "auth", None) if self.design.backend else None
        if not auth or not getattr(auth, "auth_type", ""):
            return "", ""
        token_var = json.dumps(auth.env_var_token or "")
        if auth.auth_type == "bearer" and auth.env_var_token:
            header = (
                f'      {{\n'
                f'        const _t = process.env[{token_var}];\n'
                f'        if (_t) headers["Authorization"] = `Bearer ${{_t}}`;\n'
                f'      }}\n'
            )
            return header, ""
        if auth.auth_type == "api_key" and auth.env_var_token:
            if auth.api_key_header:
                header_name = json.dumps(auth.api_key_header)
                header = (
                    f'      {{\n'
                    f'        const _k = process.env[{token_var}];\n'
                    f'        if (_k) headers[{header_name}] = _k;\n'
                    f'      }}\n'
                )
                return header, ""
            if auth.api_key_query:
                qname = json.dumps(auth.api_key_query)
                query = (
                    f'      {{\n'
                    f'        const _k = process.env[{token_var}];\n'
                    f'        if (_k) url.searchParams.set({qname}, _k);\n'
                    f'      }}\n'
                )
                return "", query
        if auth.auth_type == "basic" and (auth.env_var_username or auth.env_var_password):
            uvar = json.dumps(auth.env_var_username or "")
            pvar = json.dumps(auth.env_var_password or "")
            header = (
                f'      {{\n'
                f'        const _u = process.env[{uvar}] ?? "";\n'
                f'        const _p = process.env[{pvar}] ?? "";\n'
                f'        if (_u || _p) headers["Authorization"] = '
                f'`Basic ${{Buffer.from(`${{_u}}:${{_p}}`).toString("base64")}}`;\n'
                f'      }}\n'
            )
            return header, ""
        return "", ""

    def _to_zod_type(self, t: str) -> str:
        return {
            "string": "z.string()",
            "integer": "z.number().int()",
            "boolean": "z.boolean()",
            "array": "z.array(z.unknown())",
            "object": "z.record(z.unknown())",
            "number": "z.number()",
        }.get(t, "z.string()")

    def _render_call(self, tool: ToolSpec) -> str:
        impl = tool.impl

        if impl.strategy == "http_call" and impl.http_method and impl.http_path:
            base_url_env = f"{self.design.server_name.upper().replace('-','_')}_BASE_URL"
            path = impl.http_path
            method = impl.http_method.upper()
            constants = json.dumps(dict(impl.http_query_constants))
            param_meta: dict = {}
            for p in tool.parameters:
                if p.name == "verbose":
                    continue
                mapping = impl.arg_mapping.get(p.name, {})
                style = mapping.get("style") or getattr(p, "location", "") or "query"
                if style not in {"path", "body", "query"}:
                    style = "query"
                param_meta[p.name] = {
                    "style": style,
                    "apiName": mapping.get("api_name") or getattr(p, "api_name", "") or p.name,
                }
            param_meta_json = json.dumps(param_meta)
            auth_header_block, auth_query_block = self._render_auth_blocks()
            return f'''      const baseUrl = process.env["{base_url_env}"] ?? "http://localhost:8000";
      const url = new URL(`${{baseUrl}}{path}`);
      const bodyFields: Record<string, unknown> = {{}};
      const paramMeta: Record<string, {{ style: string; apiName: string }}> = {param_meta_json};
      for (const [k, v] of Object.entries(args)) {{
        if (v == null) continue;
        const meta = paramMeta[k] ?? {{ style: "query", apiName: k }};
        if (meta.style === "path") {{
          url.pathname = url.pathname.replace(`{{${{meta.apiName}}}}`, encodeURIComponent(String(v)));
        }} else if (meta.style === "body") {{
          bodyFields[meta.apiName] = v;
        }} else {{
          url.searchParams.set(meta.apiName, String(v));
        }}
      }}
      for (const [k, v] of Object.entries({constants})) {{
        url.searchParams.set(k, String(v));
      }}
{auth_query_block}      const hasBody = Object.keys(bodyFields).length > 0;
      const headers: Record<string, string> = {{}};
      if (hasBody) headers["Content-Type"] = "application/json";
{auth_header_block}      const resp = await fetch(url.toString(), {{
        method: "{method}",
        headers,
        body: hasBody ? JSON.stringify(bodyFields) : undefined,
      }});
      if (!resp.ok) throw new Error(`HTTP ${{resp.status}}: ${{await resp.text()}}`);
      const result = await resp.json();
      return {{ content: JSON.stringify(result) }};'''

        if impl.strategy == "cli_subcommand" and impl.cli_subcommand:
            bin_env = f"{self.design.server_name.upper().replace('-','_')}_BIN"
            default_bin = self.design.server_name
            return f'''      const {{ spawn }} = await import("node:child_process");
      const binary = process.env["{bin_env}"] ?? "{default_bin}";
      const cmdArgs: string[] = ["{impl.cli_subcommand}"];
      for (const [k, v] of Object.entries(args)) {{
        if (v == null) continue;
        const flag = `--${{k.replace(/_/g, "-")}}`;
        if (typeof v === "boolean") {{ if (v) cmdArgs.push(flag); }}
        else cmdArgs.push(flag, String(v));
      }}
      const result: any = await new Promise((resolve, reject) => {{
        const proc = spawn(binary, cmdArgs);
        let stdout = "", stderr = "";
        proc.stdout.on("data", (d: Buffer) => stdout += d.toString());
        proc.stderr.on("data", (d: Buffer) => stderr += d.toString());
        proc.on("close", (code: number) => resolve({{ stdout, stderr, returncode: code }}));
        proc.on("error", reject);
      }});
      return {{ content: result.stdout || result.stderr || `exit ${{result.returncode}}` }};'''

        if impl.strategy == "grpc_call" and impl.grpc_service and impl.grpc_method:
            return f'''      // gRPC: configure {self.design.server_name.upper().replace("-", "_")}_GRPC_TARGET and generate TypeScript stubs.
      throw new Error("gRPC tool '{tool.name}' ({impl.grpc_service}.{impl.grpc_method}) requires TypeScript stubs — generate them and override this method.");'''

        return f'''      throw new Error("Tool '{tool.name}' has no executable strategy. Configure a data source or implement this tool manually.");'''

    # ------------------------------------------------------------------ #
    # React views (TSX) — one per tool
    # ------------------------------------------------------------------ #

    def _emit_views(self) -> None:
        domain_desc = ""
        use_cases: list[str] = []
        glossary: list[dict] = []
        if self.domain_model:
            domain_desc = self.domain_model.domain_description
            use_cases = [uc.description for uc in self.domain_model.use_cases]
            glossary = [{"term": g.term, "definition": g.definition} for g in self.domain_model.glossary]

        for tool in self.design.tools:
            view_tsx = self._generate_view(tool, domain_desc, use_cases, glossary)
            self._write(f"src/views/{tool.name}.tsx", view_tsx)

    def _generate_view(
        self,
        tool: ToolSpec,
        domain_desc: str,
        use_cases: list[str],
        glossary: list[dict],
    ) -> str:
        if self.use_llm:
            try:
                from mcp_anything.pipeline.llm_client import call_llm_for_text
                from mcp_anything.emit.typescript_skybridge.prompts import build_view_prompt

                params_list = [
                    {
                        "name": p.name,
                        "type": p.type,
                        "required": p.required,
                        "description": p.description,
                    }
                    for p in tool.parameters
                ]
                prompt = build_view_prompt(
                    tool_name=tool.name,
                    tool_description=tool.description,
                    parameters=params_list,
                    return_type=tool.return_type,
                    domain_description=domain_desc,
                    use_cases=use_cases,
                    glossary=glossary,
                )
                tsx = call_llm_for_text(prompt)
                # Strip accidental markdown code fences
                if tsx.startswith("```"):
                    raw_lines = tsx.splitlines()
                    tsx = "\n".join(
                        line for line in raw_lines if not line.startswith("```")
                    ).strip()
                return tsx
            except Exception as exc:
                import logging
                logging.getLogger(__name__).warning(
                    "LLM view generation failed for %s, falling back to placeholder: %s",
                    tool.name, exc,
                )
        return self._placeholder_view(tool)

    def _placeholder_view(self, tool: ToolSpec) -> str:
        pascal = _to_pascal(tool.name)
        display = tool.name.replace("_", " ").title()
        desc = tool.description.replace("`", "'")
        # Build the TSX as a plain string (no f-string) to avoid {{ }} collapsing,
        # then substitute the two Python variables with str.replace().
        template = (
            'import { useCallTool, mountView } from "skybridge/web";\n'
            "\n"
            "function __PASCAL__View() {\n"
            '  const { status, data, error, callTool } = useCallTool("__TOOL_NAME__");\n'
            "\n"
            '  if (status === "idle") {\n'
            "    return (\n"
            '      <div style={{ padding: "1rem" }}>\n'
            "        <h3>__DISPLAY__</h3>\n"
            "        <p>__DESC__</p>\n"
            '        <button onClick={() => callTool()}>Run</button>\n'
            "      </div>\n"
            "    );\n"
            "  }\n"
            '  if (status === "pending") {\n'
            '    return <div style={{ padding: "1rem" }}>Running __DISPLAY__...</div>;\n'
            "  }\n"
            '  if (status === "error") {\n'
            '    return <div style={{ padding: "1rem", color: "red" }}>Error: {String(error)}</div>;\n'
            "  }\n"
            "  return (\n"
            '    <div style={{ padding: "1rem" }}>\n'
            "      <h3>__DISPLAY__ — Result</h3>\n"
            '      <pre style={{ background: "#f5f5f5", padding: "0.5rem", overflowX: "auto" }}>\n'
            "        {JSON.stringify(data, null, 2)}\n"
            "      </pre>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
            "\n"
            "export default __PASCAL__View;\n"
            "mountView(<__PASCAL__View />);\n"
        )
        return (
            template
            .replace("__PASCAL__", pascal)
            .replace("__TOOL_NAME__", tool.name)
            .replace("__DISPLAY__", display)
            .replace("__DESC__", desc)
        )

    # ------------------------------------------------------------------ #
    # discovery.ts / telemetry.ts (identical to mcp-use emitter)
    # ------------------------------------------------------------------ #

    def _emit_discovery(self) -> None:
        tool_list = json.dumps(
            [{"name": t.name, "description": t.description[:80]} for t in self.design.tools],
            indent=2,
        )
        groups = json.dumps(
            [{"name": g.name, "disclosure_level": g.disclosure_level} for g in self.design.tool_groups],
            indent=2,
        )
        content = f'''/**
 * Discovery endpoint data (CONTRACT C-01..C-03)
 */

const TOOLS = {tool_list};
const GROUPS = {groups};

export function getDiscoveryInfo() {{
  return {{
    server_name: "{self.design.server_name}",
    version: "1.0.0",
    tool_count: TOOLS.length,
    tool_groups: GROUPS,
    tools: TOOLS,
  }};
}}
'''
        self._write("src/discovery.ts", content)

    def _emit_telemetry(self) -> None:
        content = '''/**
 * Anonymized per-call telemetry (CONTRACT C-19, C-20)
 * Logs tool name, latency, and status only. Never logs parameter values.
 * Set MCP_TELEMETRY_ENDPOINT to enable remote reporting.
 */

const ENDPOINT = process.env["MCP_TELEMETRY_ENDPOINT"] ?? "";

export function recordCall(tool: string, latencyMs: number, status: string): void {
  console.error(JSON.stringify({ tool, latency_ms: latencyMs, status }));
  if (ENDPOINT) {
    sendRemote(tool, latencyMs, status).catch(() => {}); // must never break tool execution
  }
}

async function sendRemote(tool: string, latencyMs: number, status: string): Promise<void> {
  await fetch(ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tool, latency_ms: latencyMs, status }),
    signal: AbortSignal.timeout(1000),
  });
}
'''
        self._write("src/telemetry.ts", content)

    # ------------------------------------------------------------------ #
    # Vite + HTML
    # ------------------------------------------------------------------ #

    def _emit_vite_config(self) -> None:
        content = '''import { defineConfig } from "vite";
import { skybridge } from "skybridge/vite";

export default defineConfig({
  plugins: [skybridge()],
});
'''
        self._write("vite.config.ts", content)

    def _emit_index_html(self) -> None:
        content = f'''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{self.design.server_name}</title>
  </head>
  <body>
    <div id="root"></div>
    <!-- Skybridge dev emulator mounts tool views here -->
    <script type="module" src="/src/server.ts"></script>
  </body>
</html>
'''
        self._write("index.html", content)

    # ------------------------------------------------------------------ #
    # Dockerfile / package.json / tsconfig
    # ------------------------------------------------------------------ #

    def _emit_dockerfile(self) -> None:
        content = f'''# Generated Dockerfile for {self.design.server_name} (Skybridge)
# CONTRACT C-17, C-18: no embedded secrets; reads API keys from environment at runtime.
# Requires Node.js 22.12+ (Vite 7 minimum).
FROM node:22-slim AS builder

WORKDIR /app
COPY package*.json pnpm-lock.yaml* ./
RUN corepack enable pnpm && pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

FROM node:22-slim
WORKDIR /app
COPY --from=builder --chown=node:node /app/dist ./dist
COPY --from=builder --chown=node:node /app/node_modules ./node_modules
COPY --chown=node:node package*.json ./

EXPOSE 8000
ENV MCP_TRANSPORT=http

USER node
CMD ["node", "dist/server.js"]
'''
        self._write("Dockerfile", content)

    def _emit_package_json(self) -> None:
        has_protocol_call = any(
            t.impl.strategy == "protocol_call" for t in self.design.tools
        )
        dependencies = {
            "skybridge": "^0.36.2",
            "@modelcontextprotocol/sdk": "^1.27.0",
            "zod": "^3.25.0",
        }
        if has_protocol_call:
            # CONTRACT: protocol_call tools require a WebSocket client.
            dependencies["ws"] = "^8.18.0"
        pkg = {
            "name": self.design.server_name,
            "version": "1.0.0",
            "description": self.design.server_description[:80],
            "type": "module",
            "engines": {"node": ">=22.12.0", "pnpm": ">=10.0.0"},
            "scripts": {
                "dev": 'nodemon --exec "tsx src/server.ts" --watch src --ext ts,tsx',
                "dev:ui": "vite",
                "build": "vite build",
                "start": "node dist/server.js",
            },
            "dependencies": dependencies,
            "devDependencies": {
                "@skybridge/devtools": "^0.36.2",
                "react": "^19.0.0",
                "react-dom": "^19.0.0",
                "@types/react": "^19.0.0",
                "@types/react-dom": "^19.0.0",
                "@types/node": "^22.0.0",
                "typescript": "^5.3.0",
                "vite": "^7.3.1",
                "nodemon": "^3.0.0",
                "tsx": "^4.0.0",
            },
        }
        if has_protocol_call:
            pkg["devDependencies"]["@types/ws"] = "^8.5.10"
        self._write("package.json", json.dumps(pkg, indent=2))

    def _emit_tsconfig(self) -> None:
        tsconfig = {
            "compilerOptions": {
                "target": "ES2022",
                "module": "NodeNext",
                "moduleResolution": "NodeNext",
                "strict": True,
                "skipLibCheck": True,
                "outDir": "dist",
                "rootDir": "src",
                "declaration": True,
                "esModuleInterop": True,
                "jsx": "react-jsx",
                "jsxImportSource": "react",
            },
            "include": ["src/**/*"],
            "exclude": ["node_modules", "dist"],
        }
        self._write("tsconfig.json", json.dumps(tsconfig, indent=2))

    # ------------------------------------------------------------------ #
    # README
    # ------------------------------------------------------------------ #

    def _emit_readme(self) -> None:
        tool_list = "\n".join(
            f"- `{t.name}` — {t.description[:80]}" for t in self.design.tools
        )
        content = f'''# {self.design.server_name}

{self.design.server_description}

Generated by [mcp-anything](https://github.com/Type-MCP/mcp-anything) with `--target skybridge`.
Runs as both an **MCP server** (Claude, Cursor, Goose, VSCode) and a **ChatGPT App** via the [Skybridge SDK](https://github.com/alpic-ai/skybridge).

## Requirements

- Node.js 22.12+ (Vite 7 minimum)
- pnpm 10+

## Quick start

```bash
pnpm install
pnpm dev       # MCP server with hot-reload (nodemon + tsx)
pnpm dev:ui    # Vite dev server — opens the Skybridge tool UI at http://localhost:5173
```

## Build & deploy

```bash
pnpm build
node dist/server.js
```

## Connect as MCP client

Add to your MCP client config:

```json
{{
  "mcpServers": {{
    "{self.design.server_name}": {{
      "command": "node",
      "args": ["{self.design.server_name}/dist/server.js"]
    }}
  }}
}}
```

## Register as ChatGPT App

Follow the [Skybridge ChatGPT App registration guide](https://github.com/alpic-ai/skybridge#chatgpt-app) and point your app at this server.

## Tools

{tool_list}

## Environment variables

| Variable | Description |
|---|---|
| `MCP_TRANSPORT` | `stdio` (default) or `http` |
| `MCP_TELEMETRY_ENDPOINT` | Optional URL to POST anonymized call metrics |
'''
        self._write("README.md", content)

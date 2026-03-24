"""Regex-based analyzer for Zustand state management stores in TypeScript/JavaScript.

Extracts store names and action signatures from Zustand store files.
Actions (function-typed properties) become MCP tools; state fields are skipped.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

from mcp_anything.models.analysis import Capability, FileInfo, IPCType, Language, ParameterSpec


# --- Store detection ---
_ZUSTAND_IMPORT_RE = re.compile(r"""from\s+['"]zustand['"]""")
_STORE_VAR_RE = re.compile(
    r"""(?:export\s+)?(?:const|let)\s+(use\w+)\s*(?::\s*\w+)?\s*=\s*create\s*<(\w+)>"""
)

# --- State type extraction ---
# Matches: type SceneState = {  or  interface SceneState {
_TYPE_START_RE = re.compile(r"""^(?:export\s+)?(?:type|interface)\s+(\w+)\s*[={]""")

# --- Action line detection ---
# Matches lines like:  createNode: (node: AnyNode, parentId?: AnyNodeId) => void
_ACTION_LINE_RE = re.compile(
    r"""^\s{0,4}(\w+)\??\s*:\s*\(([^)]*)\)\s*=>"""
)

# --- Parameter parsing ---
_PARAM_RE = re.compile(r"""^(\w+)(\?)?\s*:\s*(.+)$""")


def _ts_type_to_mcp(ts_type: str) -> str:
    """Convert a TypeScript type string to an MCP parameter type."""
    ts_type = ts_type.strip()

    # Remove generic wrappers: Partial<X>, Required<X>, Readonly<X>
    for wrapper in ("Partial", "Required", "Readonly", "NonNullable"):
        if ts_type.startswith(f"{wrapper}<"):
            ts_type = ts_type[len(wrapper) + 1 : -1]
            break

    # Primitives
    lower = ts_type.lower()
    if lower in ("string", "anynode['id']", "anynodeid", "nodeid", "id"):
        return "string"
    if lower in ("number", "int", "float"):
        return "number"
    if lower in ("boolean", "bool"):
        return "boolean"
    if lower in ("any", "unknown", "object"):
        return "object"

    # Arrays
    if ts_type.endswith("[]") or ts_type.startswith("Array<"):
        return "array"

    # Records, Sets, Maps → object
    if ts_type.startswith(("Record<", "Set<", "Map<")):
        return "object"

    # Object literal
    if ts_type.startswith("{"):
        return "object"

    # Union types: pick the first non-null/undefined part
    if "|" in ts_type:
        parts = [p.strip() for p in ts_type.split("|")]
        parts = [p for p in parts if p not in ("null", "undefined")]
        if parts:
            return _ts_type_to_mcp(parts[0])
        return "string"

    # String literals 'a' | 'b' → string
    if ts_type.startswith("'") or ts_type.startswith('"'):
        return "string"

    # Short identifiers that are likely string IDs or simple aliases
    if re.match(r"^[A-Z]\w{0,15}Id$", ts_type):
        return "string"

    # Everything else (complex types, generics) → object
    if "<" in ts_type or ts_type[0].isupper():
        return "object"

    return "string"


def _parse_params(params_str: str) -> list[ParameterSpec]:
    """Parse a TypeScript parameter list string into ParameterSpec objects."""
    if not params_str.strip():
        return []

    # Split by commas, but be careful of nested generics like Record<K, V>
    params: list[str] = []
    depth = 0
    current = ""
    for ch in params_str:
        if ch in "<({[":
            depth += 1
            current += ch
        elif ch in ">)}]":
            depth -= 1
            current += ch
        elif ch == "," and depth == 0:
            params.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip():
        params.append(current.strip())

    specs = []
    for p in params:
        m = _PARAM_RE.match(p.strip())
        if not m:
            continue
        name, optional_mark, ts_type = m.group(1), m.group(2), m.group(3)
        is_optional = bool(optional_mark)
        mcp_type = _ts_type_to_mcp(ts_type)
        specs.append(
            ParameterSpec(
                name=name,
                type=mcp_type,
                description=f"{name} ({ts_type.strip()})",
                required=not is_optional,
            )
        )
    return specs


def _action_description(store_name: str, action_name: str) -> str:
    """Generate a human-readable description from camelCase action name."""
    # Convert camelCase to words
    words = re.sub(r"([A-Z])", r" \1", action_name).strip().split()
    return f"{' '.join(words).capitalize()} in the {store_name} store"


@dataclass
class ZustandAction:
    name: str
    parameters: list[ParameterSpec]
    description: str


@dataclass
class ZustandStore:
    name: str          # e.g. "scene" (from useScene → scene)
    hook_name: str     # e.g. "useScene"
    state_type: str    # e.g. "SceneState"
    actions: list[ZustandAction] = field(default_factory=list)
    source_file: str = ""


@dataclass
class ZustandAnalysisResult:
    stores: list[ZustandStore] = field(default_factory=list)
    framework: str = "zustand"


def _extract_type_block(content: str, type_name: str) -> str | None:
    """Extract the body of a TypeScript type/interface definition."""
    # Find the line starting the type
    lines = content.splitlines()
    start_idx = None
    for i, line in enumerate(lines):
        m = _TYPE_START_RE.match(line)
        if m and m.group(1) == type_name:
            start_idx = i
            break

    if start_idx is None:
        return None

    # Collect until the closing brace (track depth)
    block_lines = []
    depth = 0
    for line in lines[start_idx:]:
        block_lines.append(line)
        depth += line.count("{") - line.count("}")
        if depth <= 0 and block_lines:
            break

    return "\n".join(block_lines)


def _extract_actions(type_block: str, store_name: str) -> list[ZustandAction]:
    """Extract action methods from a Zustand state type block."""
    actions = []
    seen = set()

    for line in type_block.splitlines():
        m = _ACTION_LINE_RE.match(line)
        if not m:
            continue

        action_name = m.group(1)
        params_str = m.group(2)

        # Skip internal/utility actions
        if action_name in ("markDirty", "clearDirty", "setExportScene", "outliner"):
            continue
        if action_name in seen:
            continue
        seen.add(action_name)

        params = _parse_params(params_str)
        actions.append(
            ZustandAction(
                name=action_name,
                parameters=params,
                description=_action_description(store_name, action_name),
            )
        )

    return actions


def analyze_zustand_file(root: Path, fi: FileInfo) -> ZustandAnalysisResult | None:
    """Analyze a TypeScript/JavaScript file for Zustand store definitions."""
    if fi.language not in (Language.TYPESCRIPT, Language.JAVASCRIPT):
        return None

    try:
        content = (root / fi.path).read_text(errors="replace")
    except OSError:
        return None

    if not _ZUSTAND_IMPORT_RE.search(content):
        return None

    stores = []
    for m in _STORE_VAR_RE.finditer(content):
        hook_name = m.group(1)      # e.g. "useScene"
        state_type = m.group(2)     # e.g. "SceneState"

        # Derive store name: useScene → scene, useViewer → viewer
        store_name = hook_name[3:].lower() if hook_name.startswith("use") else hook_name.lower()

        # Extract the state type block
        type_block = _extract_type_block(content, state_type)
        if not type_block:
            continue

        actions = _extract_actions(type_block, store_name)
        if not actions:
            continue

        stores.append(
            ZustandStore(
                name=store_name,
                hook_name=hook_name,
                state_type=state_type,
                actions=actions,
                source_file=fi.path,
            )
        )

    if not stores:
        return None

    return ZustandAnalysisResult(stores=stores)


def detect_zustand_import_path(root: Path, source_file: str, hook_name: str) -> str:
    """Find the npm package import path for a Zustand store hook.

    Walks up from the store file to find the nearest package.json, then
    checks if the hook is exported from that package's index. Returns the
    npm package name (e.g. '@pascal-app/core') if found, otherwise a
    relative path from 'bridge/McpBridge.tsx'.
    """
    import json as _json

    file_path = root / source_file
    current = file_path.parent

    while True:
        pkg_json = current / "package.json"
        if pkg_json.exists():
            try:
                data = _json.loads(pkg_json.read_text(errors="replace"))
                pkg_name = data.get("name", "")
                if pkg_name:
                    # Check if the hook is re-exported from the package's index
                    for idx_rel in (
                        "src/index.ts", "src/index.tsx",
                        "src/index.js", "src/index.jsx",
                        "index.ts", "index.tsx",
                        "index.js", "index.jsx",
                    ):
                        idx_path = current / idx_rel
                        if idx_path.exists():
                            idx_content = idx_path.read_text(errors="replace")
                            if hook_name in idx_content:
                                return pkg_name
            except Exception:
                pass

        parent = current.parent
        if parent == current or current == root:
            break
        current = parent

    # Fallback: relative path from bridge/McpBridge.tsx to the store file
    rel = source_file.removesuffix(".ts").removesuffix(".tsx").removesuffix(".js")
    return f"../../{rel}"


def zustand_results_to_capabilities(
    zustand_results: dict[str, ZustandAnalysisResult],
) -> list[Capability]:
    """Convert ZustandAnalysisResult objects to Capability objects."""
    capabilities = []
    seen = set()

    for _file_path, result in zustand_results.items():
        for store in result.stores:
            for action in store.actions:
                cap_name = f"{store.name}.{action.name}"
                if cap_name in seen:
                    continue
                seen.add(cap_name)

                capabilities.append(
                    Capability(
                        name=cap_name,
                        description=action.description,
                        category="zustand_action",
                        parameters=action.parameters,
                        return_type="object",
                        source_file=store.source_file,
                        source_function=action.name,
                        source_class=store.hook_name,
                        ipc_type=IPCType.PROTOCOL,
                    )
                )

    return capabilities

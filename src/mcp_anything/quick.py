"""One command from a source to a server: `mcp-anything <url | spec file | code folder>`.

The brief that `build` needs is drafted from the source: from the spec's
title, description, tags and operations, or, with a model, written by it from
a summary of the spec. The draft is saved as brief.yaml next to the server,
so it can be edited and rebuilt with `mcp-anything build --brief`.
"""

from __future__ import annotations

import json
import re
import shutil
from collections import OrderedDict
from pathlib import Path

import yaml

SPEC_SUFFIXES = {".json": "openapi", ".yaml": "openapi", ".yml": "openapi", ".proto": "grpc",
                 ".graphql": "graphql", ".gql": "graphql"}
METHODS = ("get", "post", "put", "patch", "delete")
MAX_USE_CASES = 12


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "api"


def locate(source: str, console) -> tuple[Path, str, str]:
    """(path, kind, name) for a URL, a spec file or a code folder. URLs are downloaded first."""
    from mcp_anything.url_fetcher import fetch_url, is_url

    if is_url(source):
        folder, name = fetch_url(source, console)
        specs = [p for p in Path(folder).iterdir() if p.suffix.lower() in SPEC_SUFFIXES]
        if not specs:
            raise ValueError(f"No API spec found at {source}.")
        return specs[0], SPEC_SUFFIXES[specs[0].suffix.lower()], name
    path = Path(source).expanduser().resolve()
    if path.is_dir():
        return path, "codebase", slug(path.name)
    if path.is_file() and path.suffix.lower() in SPEC_SUFFIXES:
        return path, SPEC_SUFFIXES[path.suffix.lower()], slug(path.stem)
    if path.exists():
        raise ValueError(f"{path} is not a folder or a spec ({', '.join(sorted(SPEC_SUFFIXES))}).")
    raise ValueError(f"{source} does not exist.")


# --- drafting the brief --------------------------------------------------------------------


def draft_brief(path: Path, kind: str, name: str, use_model: bool = True, console=None) -> dict:
    """A brief for `build`: deterministic from the source, then improved by the model if one is usable."""
    if kind == "openapi":
        brief = _from_openapi(path, name)
    elif kind == "graphql":
        brief = _from_names(path, name, re.findall(r"^\s*(\w+)\s*(?:\(|:)", _graphql_operations(path.read_text()), re.M),
                            "GraphQL API")
    elif kind == "grpc":
        brief = _from_names(path, name, re.findall(r"rpc\s+(\w+)", path.read_text()), "gRPC service")
    else:
        brief = {
            "server_name": name,
            "domain_description": f"The {name} application, exposed to agents through its own code.",
            "use_cases": [f"Use the main operations of {name}"],
        }
    brief.update(data_source_path=str(path), data_source_kind=kind, backend_target="fastmcp")
    if use_model and kind != "codebase":
        brief = _improve_with_model(brief, path, console)
    return brief


def _load_spec(path: Path) -> dict:
    text = path.read_text()
    try:
        return json.loads(text)
    except ValueError:
        return yaml.safe_load(text) or {}


def _from_openapi(path: Path, name: str) -> dict:
    spec = _load_spec(path)
    info = spec.get("info") or {}
    title = info.get("title") or name
    groups: "OrderedDict[str, list[str]]" = OrderedDict()
    for route, item in (spec.get("paths") or {}).items():
        for method in METHODS:
            operation = (item or {}).get(method)
            if not isinstance(operation, dict):
                continue
            tag = (operation.get("tags") or [route.strip("/").split("/")[0] or "general"])[0]
            summary = (operation.get("summary") or operation.get("operationId") or f"{method.upper()} {route}").strip()
            groups.setdefault(tag, []).append(summary.rstrip("."))
    use_cases = [f"{tag.replace('_', ' ').replace('-', ' ').capitalize()}: {'; '.join(summaries[:6])}"
                 for tag, summaries in groups.items()][:MAX_USE_CASES]
    description = (info.get("description") or "").strip().split("\n\n")[0] or f"The {title}."
    return {
        "server_name": slug(title) if title != name else name,
        "domain_description": description,
        "use_cases": use_cases or [f"Use the {title}"],
        "auth_method": _auth(spec),
    }


def _auth(spec: dict) -> str:
    schemes = ((spec.get("components") or {}).get("securitySchemes") or spec.get("securityDefinitions") or {})
    for scheme in schemes.values():
        kind, flavor = (scheme or {}).get("type", ""), (scheme or {}).get("scheme", "")
        if kind == "http" and flavor == "bearer" or kind == "oauth2":
            return "bearer_token" if kind == "http" else "oauth2"
        if kind == "apiKey":
            return "api_key"
        if kind in ("http", "basic") and flavor in ("basic", ""):
            return "basic"
    return ""


def _graphql_operations(text: str) -> str:
    blocks = re.findall(r"type\s+(?:Query|Mutation)\s*\{(.*?)\}", text, re.S)
    return "\n".join(blocks)


def _from_names(path: Path, name: str, operations: list[str], what: str) -> dict:
    readable = [re.sub(r"(?<!^)(?=[A-Z])", " ", op).replace("_", " ").lower() for op in operations]
    return {
        "server_name": name,
        "domain_description": f"The {name} {what}.",
        "use_cases": [op.capitalize() for op in readable[:MAX_USE_CASES]] or [f"Use the {name} {what}"],
    }


def _improve_with_model(brief: dict, path: Path, console) -> dict:
    """Ask the model for a better description and use cases; keep the draft on any failure."""
    from mcp_anything.pipeline.llm_client import call_llm_for_json

    prompt = (
        "Here is a draft brief for an MCP server that will let AI agents use an API, and an excerpt of the API spec.\n"
        "Rewrite `domain_description` as two or three sentences on what the API is for, and `use_cases` as 5 to 12 "
        "short sentences, each a task an agent would be asked to do with it. Return JSON with exactly those two keys.\n\n"
        f"Draft:\n{json.dumps({k: brief[k] for k in ('domain_description', 'use_cases')}, indent=1)}\n\n"
        f"Spec excerpt:\n{path.read_text()[:6000]}"
    )
    try:
        data = call_llm_for_json(prompt, max_tokens=2000)
    except Exception as exc:  # no model, or a bad answer: the draft is good enough
        if console:
            console.print(f"[dim]Using the drafted brief ({exc.__class__.__name__}).[/dim]")
        return brief
    if isinstance(data, dict) and isinstance(data.get("domain_description"), str) and \
            isinstance(data.get("use_cases"), list) and all(isinstance(u, str) for u in data["use_cases"]) and data["use_cases"]:
        return {**brief, "domain_description": data["domain_description"], "use_cases": data["use_cases"][:MAX_USE_CASES]}
    return brief


def write_brief(brief: dict, path: Path) -> Path:
    path.write_text(yaml.safe_dump(brief, sort_keys=False, allow_unicode=True))
    return path


def keep_brief(brief_file: Path, output_dir: Path) -> Path:
    """Copy the drafted brief next to the generated server, for editing and rebuilding."""
    target = output_dir / "brief.yaml"
    if brief_file.resolve() != target.resolve():
        shutil.copy(brief_file, target)
    return target


__all__ = ["locate", "draft_brief", "write_brief", "keep_brief"]

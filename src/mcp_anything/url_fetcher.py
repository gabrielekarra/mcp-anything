"""Fetch API specs from URLs for generation.

Supports OpenAPI/Swagger (JSON/YAML), GraphQL SDL, and raw spec URLs.
Downloads the spec, detects the type, and saves it to a local directory
so the existing pipeline can process it.
"""

import json
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import yaml

try:
    from urllib.request import urlopen, Request
    from urllib.error import URLError, HTTPError
except ImportError:
    urlopen = None  # type: ignore[assignment]

from rich.console import Console


def is_url(path_str: str) -> bool:
    """Check if a string looks like an HTTP(S) URL."""
    return path_str.startswith("http://") or path_str.startswith("https://")


def _derive_name_from_url(url: str, spec: dict | None = None) -> str:
    """Derive a server name from a URL and optional parsed spec."""
    # Try spec title first
    if spec:
        title = spec.get("info", {}).get("title", "")
        if title:
            name = re.sub(r"[^a-zA-Z0-9]+", "_", title).strip("_").lower()
            # Truncate long names
            if len(name) > 40:
                name = name[:40].rstrip("_")
            if name:
                return name

    # Fall back to hostname
    parsed = urlparse(url)
    hostname = parsed.hostname or "api"
    # Strip common prefixes/suffixes
    name = hostname.replace("www.", "").split(".")[0]
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    return name or "api"


def _detect_and_save(content: str, url: str, target_dir: Path) -> str | None:
    """Detect spec type from content and save with appropriate filename.

    Returns the filename used, or None if the content isn't a recognized spec.
    """
    # Try JSON first
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            if "swagger" in data:
                filename = "swagger.json"
                (target_dir / filename).write_text(content)
                return filename
            if "openapi" in data:
                filename = "openapi.json"
                (target_dir / filename).write_text(content)
                return filename
            if "definitions" in data and "paths" in data:
                # Swagger 2.0 without explicit "swagger" key
                filename = "swagger.json"
                (target_dir / filename).write_text(content)
                return filename
    except (json.JSONDecodeError, ValueError):
        pass

    # Try YAML
    try:
        data = yaml.safe_load(content)
        if isinstance(data, dict):
            if "swagger" in data:
                filename = "swagger.yaml"
                (target_dir / filename).write_text(content)
                return filename
            if "openapi" in data:
                filename = "openapi.yaml"
                (target_dir / filename).write_text(content)
                return filename
    except yaml.YAMLError:
        pass

    # Check for GraphQL SDL
    if re.search(r"\btype\s+(Query|Mutation|Subscription)\b", content):
        filename = "schema.graphql"
        (target_dir / filename).write_text(content)
        return filename

    # Check for protobuf
    if re.search(r"\bsyntax\s*=\s*[\"']proto[23][\"']", content):
        filename = "service.proto"
        (target_dir / filename).write_text(content)
        return filename

    # If URL path hints at the type, save with that extension
    parsed = urlparse(url)
    path_lower = parsed.path.lower()
    if any(ext in path_lower for ext in (".json", ".yaml", ".yml")):
        # Could be an OpenAPI spec without the standard keys at top level
        ext = ".yaml" if ".yaml" in path_lower or ".yml" in path_lower else ".json"
        filename = f"spec{ext}"
        (target_dir / filename).write_text(content)
        return filename

    return None


def fetch_url(url: str, console: Console) -> tuple[Path, str]:
    """Fetch a URL and save the spec to a temporary directory.

    Returns (temp_dir_path, derived_server_name).
    Raises RuntimeError on failure.
    """
    if urlopen is None:
        raise RuntimeError("urllib is not available")

    console.print(f"[cyan]Fetching[/cyan] {url}")

    # Common doc URLs that serve HTML — try to find the raw spec
    actual_url = _resolve_spec_url(url)
    if actual_url != url:
        console.print(f"[dim]  Resolved to {actual_url}[/dim]")

    try:
        req = Request(actual_url, headers={
            "Accept": "application/json, application/yaml, text/yaml, text/plain, */*",
            "User-Agent": "mcp-anything/0.1.1",
        })
        with urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} fetching {actual_url}: {exc.reason}")
    except URLError as exc:
        raise RuntimeError(f"Failed to fetch {actual_url}: {exc.reason}")
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch {actual_url}: {exc}")

    if not content.strip():
        raise RuntimeError(f"Empty response from {actual_url}")

    # Save to temp dir
    temp_dir = Path(tempfile.mkdtemp(prefix="mcp_anything_"))
    filename = _detect_and_save(content, actual_url, temp_dir)

    if not filename:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(
            f"Could not detect spec type from {actual_url}. "
            "Supported: OpenAPI (JSON/YAML), GraphQL SDL, Protobuf."
        )

    console.print(f"[green]Downloaded[/green] {filename} to {temp_dir}")

    # Parse for name derivation
    spec = None
    try:
        spec_content = (temp_dir / filename).read_text()
        if filename.endswith(".json"):
            spec = json.loads(spec_content)
        elif filename.endswith((".yaml", ".yml")):
            spec = yaml.safe_load(spec_content)
    except Exception:
        pass

    name = _derive_name_from_url(url, spec)
    return temp_dir, name


def _resolve_spec_url(url: str) -> str:
    """Try to resolve common API doc URLs to their raw spec endpoint."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")

    # Swagger UI / ReDoc pages → try common spec paths
    doc_patterns = {
        "/docs": "/openapi.json",
        "/swagger-ui": "/v3/api-docs",
        "/swagger-ui.html": "/v3/api-docs",
        "/api-docs": "/api-docs",
        "/redoc": "/openapi.json",
    }

    for pattern, spec_path in doc_patterns.items():
        if path.endswith(pattern):
            base = url[:url.rfind(pattern)]
            return base + spec_path

    # Already looks like a spec URL
    if any(path.endswith(ext) for ext in (".json", ".yaml", ".yml", ".graphql", ".proto")):
        return url

    # Petstore-style: /v2, /v3 endpoints
    if re.search(r"/v\d+/?$", path):
        return url + "/openapi.json"

    return url

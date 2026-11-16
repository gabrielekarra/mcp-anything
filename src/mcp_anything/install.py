"""Add a server to an MCP client's configuration: `mcp-anything install <server-dir> --client cursor`.

Clients and the file each one reads:

    claude-code      ~/.claude.json                         (user scope)
    claude-desktop   Claude's claude_desktop_config.json    (macOS, Windows or Linux location)
    cursor           ~/.cursor/mcp.json
    vscode           .vscode/mcp.json in the current folder  (workspace scope)

The entry is merged into the existing file: other servers are kept, the old
file is backed up once as <file>.bak, and running it twice changes nothing.
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

CLIENTS = ("claude-code", "claude-desktop", "cursor", "vscode")


def config_path(client: str, home: Optional[Path] = None, cwd: Optional[Path] = None, system: Optional[str] = None) -> Path:
    home = Path(home or Path.home())
    system = system or platform.system()
    if client == "claude-code":
        return home / ".claude.json"
    if client == "claude-desktop":
        if system == "Darwin":
            return home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        if system == "Windows":
            return Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "Claude" / "claude_desktop_config.json"
        return home / ".config" / "Claude" / "claude_desktop_config.json"
    if client == "cursor":
        return home / ".cursor" / "mcp.json"
    if client == "vscode":
        return Path(cwd or Path.cwd()) / ".vscode" / "mcp.json"
    raise ValueError(f"Unknown client {client!r}. Known: {', '.join(CLIENTS)}.")


def server_name(folder: Path) -> str:
    """The server's name: its console script in pyproject.toml, or the folder name."""
    pyproject = folder / "pyproject.toml"
    if pyproject.exists():
        match = re.search(r"\[project\.scripts\]\s*\n\s*([\w.-]+)\s*=", pyproject.read_text())
        if match:
            return match.group(1)
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", folder.resolve().name).strip("-") or "mcp-server"


def launch(folder: Path, pip: bool = True) -> dict:
    """How a client should start the server in `folder` over stdio."""
    folder = folder.resolve()
    packages = [p.parent for root in (folder, folder / "src") for p in sorted(root.glob("*/server.py"))
                if (p.parent / "__init__.py").exists()]
    if packages:
        package = packages[0].name
        if pip and (folder / "pyproject.toml").exists():
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-e", str(folder)], check=True)
        return {"command": sys.executable, "args": ["-m", f"{package}.server"]}
    if (folder / "package.json").exists():  # a TypeScript/mcp-use server: it serves over HTTP
        return {"url": "http://localhost:8000/mcp"}
    raise ValueError(f"{folder} does not look like a generated MCP server (no <package>/server.py or package.json).")


def entry_for(client: str, launch_spec: dict) -> dict:
    """The JSON a client expects for one server."""
    if "url" in launch_spec:
        url = launch_spec["url"]
        if client == "claude-desktop":  # Claude Desktop starts only local commands: bridge with mcp-remote
            return {"command": "npx", "args": ["-y", "mcp-remote", url]}
        if client in ("claude-code", "vscode"):
            return {"type": "http", "url": url}
        return {"url": url}
    entry = {"command": launch_spec["command"], "args": launch_spec.get("args", [])}
    if launch_spec.get("env"):
        entry["env"] = launch_spec["env"]
    if client in ("claude-code", "vscode"):
        entry = {"type": "stdio", **entry}
    return entry


def install(client: str, name: str, launch_spec: dict, path: Optional[Path] = None, write: bool = True) -> tuple[Path, dict, bool]:
    """Merge the entry into the client's file. Returns (file, entry, changed)."""
    path = path or config_path(client)
    entry = entry_for(client, launch_spec)
    key = "servers" if client == "vscode" else "mcpServers"
    config = json.loads(path.read_text()) if path.exists() and path.read_text().strip() else {}
    if config.get(key, {}).get(name) == entry:
        return path, entry, False
    if not write:
        return path, entry, True
    if path.exists():
        backup = path.with_name(path.name + ".bak")
        if not backup.exists():
            shutil.copy(path, backup)
    config.setdefault(key, {})[name] = entry
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n")
    return path, entry, True

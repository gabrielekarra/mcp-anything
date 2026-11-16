"""Read the tool list of any MCP server: a command, a URL, a JSON file, or a generated server folder.

Written on the standard library, so grading needs nothing but mcp-anything.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path
from typing import Optional

PROTOCOL = "2025-06-18"


class TargetError(RuntimeError):
    """The target could not be read."""


def load_tools(target: str, timeout: float = 60, env: Optional[dict] = None) -> tuple[list[dict], str]:
    """The tools of `target`, and a short description of where they came from."""
    if target.startswith(("http://", "https://")):
        return HTTPClient(target, timeout).list_tools(), target
    path = Path(target).expanduser()
    if path.is_file() and path.suffix == ".json":
        return tools_from_json(json.loads(path.read_text())), str(path)
    if path.is_dir():
        command, cwd, extra = command_for_folder(path)
        return StdioClient(command, timeout, cwd=cwd, env={**(env or {}), **extra}).list_tools(), str(path)
    return StdioClient(shlex.split(target), timeout, env=env).list_tools(), target


def tools_from_json(data) -> list[dict]:
    """Accept a tools/list result, its JSON-RPC response, or a bare list of tools."""
    if isinstance(data, dict) and "result" in data:
        data = data["result"]
    if isinstance(data, dict) and "tools" in data:
        data = data["tools"]
    if not isinstance(data, list) or not all(isinstance(tool, dict) and "name" in tool for tool in data):
        raise TargetError("The JSON file is not a tools/list result: expected a list of tools with names.")
    return data


def command_for_folder(folder: Path) -> tuple[list[str], Path, dict]:
    """How to start a server from its folder: a generated Python server, or a command in mcp.json."""
    for root in (folder, folder / "src"):
        for package in sorted(root.glob("*/server.py")):
            if (package.parent / "__init__.py").exists():
                env = {"PYTHONPATH": os.pathsep.join(filter(None, [str(root), os.environ.get("PYTHONPATH")]))}
                return [sys.executable, "-m", f"{package.parent.name}.server"], root, env
    config = folder / "mcp.json"
    if config.exists():
        servers = json.loads(config.read_text()).get("mcpServers", {})
        for entry in servers.values():
            if "command" in entry:
                return [entry["command"], *entry.get("args", [])], folder, entry.get("env", {})
    raise TargetError(f"{folder} has no server.py package and no mcp.json command to start.")


class StdioClient:
    def __init__(self, command: list[str], timeout: float = 60, cwd=None, env=None):
        self.command, self.timeout, self.cwd = command, timeout, cwd
        self.env = {**os.environ, **(env or {})}
        self.errors: deque = deque(maxlen=20)

    def list_tools(self) -> list[dict]:
        try:
            process = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, cwd=self.cwd, env=self.env)
        except FileNotFoundError:
            raise TargetError(f"Cannot start `{self.command[0]}`: not installed or not on PATH.") from None
        threading.Thread(target=self._read_errors, args=(process,), daemon=True).start()
        lines: "queue.Queue[Optional[bytes]]" = _line_queue(process)
        try:
            self._send(process, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": PROTOCOL, "capabilities": {}, "clientInfo": {"name": "mcp-anything-grade", "version": "1"}}})
            self._wait(lines, 1)
            self._send(process, {"jsonrpc": "2.0", "method": "notifications/initialized"})
            tools, cursor, request_id = [], None, 2
            while True:
                self._send(process, {"jsonrpc": "2.0", "id": request_id, "method": "tools/list",
                                     "params": {"cursor": cursor} if cursor else {}})
                result = self._wait(lines, request_id)
                tools += result.get("tools", [])
                cursor, request_id = result.get("nextCursor"), request_id + 1
                if not cursor:
                    return tools
        finally:
            process.kill()
            process.wait()

    @staticmethod
    def _send(process, message):
        try:
            process.stdin.write((json.dumps(message) + "\n").encode())
            process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass  # the server exited; _wait reports it with its error output

    def _wait(self, lines, request_id):
        import queue

        while True:
            try:
                line = lines.get(timeout=self.timeout)
            except queue.Empty:
                raise TargetError(f"The server did not answer within {self.timeout:.0f}s{self._stderr()}") from None
            if line is None:
                raise TargetError(f"The server exited before answering{self._stderr()}")
            try:
                message = json.loads(line)
            except ValueError:
                continue  # servers sometimes print other things on stdout
            if message.get("id") == request_id:
                if "error" in message:
                    raise TargetError(f"The server answered with an error: {message['error'].get('message')}")
                return message.get("result") or {}

    def _read_errors(self, process):
        for line in process.stderr:
            self.errors.append(line.decode("utf-8", "replace").rstrip())

    def _stderr(self):
        return (": " + " | ".join(list(self.errors)[-5:])) if self.errors else ""


def _line_queue(process):
    import queue

    lines: queue.Queue = queue.Queue()

    def read():
        for line in process.stdout:
            lines.put(line)
        lines.put(None)

    threading.Thread(target=read, daemon=True).start()
    return lines


class HTTPClient:
    """Streamable HTTP transport: JSON or server-sent events, with the session header."""

    def __init__(self, url: str, timeout: float = 60, headers: Optional[dict] = None):
        self.url, self.timeout, self.headers, self.session = url, timeout, headers or {}, None

    def list_tools(self) -> list[dict]:
        self._request(1, "initialize", {"protocolVersion": PROTOCOL, "capabilities": {},
                                        "clientInfo": {"name": "mcp-anything-grade", "version": "1"}})
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"}, expect=False)
        tools, cursor, request_id = [], None, 2
        while True:
            result = self._request(request_id, "tools/list", {"cursor": cursor} if cursor else {})
            tools += result.get("tools", [])
            cursor, request_id = result.get("nextCursor"), request_id + 1
            if not cursor:
                return tools

    def _request(self, request_id, method, params):
        message = self._post({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        if "error" in message:
            raise TargetError(f"{method}: {message['error'].get('message')}")
        return message.get("result") or {}

    def _post(self, message, expect=True):
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                   "MCP-Protocol-Version": PROTOCOL, **self.headers}
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        request = urllib.request.Request(self.url, json.dumps(message).encode(), headers, method="POST")
        try:
            response = urllib.request.urlopen(request, timeout=self.timeout)
        except urllib.error.HTTPError as error:
            raise TargetError(f"HTTP {error.code} from {self.url}") from None
        except (urllib.error.URLError, OSError) as error:
            raise TargetError(f"Cannot reach {self.url}: {getattr(error, 'reason', error)}") from None
        with response:
            self.session = response.headers.get("Mcp-Session-Id") or self.session
            if not expect:
                return None
            if "text/event-stream" in response.headers.get("Content-Type", ""):
                for line in response:
                    line = line.decode("utf-8", "replace").strip()
                    if line.startswith("data:"):
                        data = json.loads(line[5:])
                        if data.get("id") == message["id"]:
                            return data
                raise TargetError("The event stream ended without an answer.")
            return json.load(response)

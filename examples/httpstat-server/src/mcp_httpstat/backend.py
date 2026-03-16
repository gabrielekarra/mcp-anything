"""CLI backend for httpstat."""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any


class Backend:
    """Communicates with httpstat via command-line interface."""

    def __init__(self) -> None:
        self.codebase_path = Path("/tmp/httpstat")
        self.entry_command = "python httpstat.py"
        self.env: dict[str, str] = {}

    async def run_cli(self, args: list[str]) -> str:
        """Run a CLI command with the given arguments and return stdout."""
        # Build the full command
        entry = self.entry_command
        if entry.startswith("python "):
            script = entry.split(" ", 1)[1]
            cmd = [sys.executable, str(self.codebase_path / script)] + args
        else:
            cmd = [entry] + args

        env = {**os.environ, **self.env}

        # Use cwd only if it's a Python script in a project directory
        cwd = str(self.codebase_path) if entry.startswith("python ") else None

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=cwd,
        )
        stdout, stderr = await proc.communicate()

        output = stdout.decode().strip()
        err_output = stderr.decode().strip()

        if proc.returncode != 0:
            raise RuntimeError(
                f"Command failed (exit {proc.returncode}): {err_output}\n"
                f"Command: {' '.join(cmd)}"
            )

        # Some CLI tools (ffmpeg, curl) write useful output to stderr
        return output or err_output

    async def run_subcommand(self, subcommand: str, args: list[str] | None = None) -> str:
        """Run a CLI subcommand (or just pass args if subcommand is empty)."""
        cmd_args = ([subcommand] if subcommand else []) + (args or [])
        return await self.run_cli(cmd_args)

    async def run_function_as_cli(
        self, source_file: str, function_name: str, **kwargs: Any
    ) -> str:
        """Call a Python function in the target codebase by running it as a subprocess."""
        args_str = ", ".join(
            f"{k}={v!r}" for k, v in kwargs.items() if v is not None
        )
        module_name = source_file.removesuffix(".py").replace("/", ".")
        code = (
            f"import sys; sys.path.insert(0, '.'); "
            f"from {module_name} import {function_name}; "
            f"result = {function_name}({args_str}); "
            f"print(result)"
        )
        # Run python -c directly, not through the app entry point
        cmd = [sys.executable, "-c", code]
        env = {**os.environ, **self.env}

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=str(self.codebase_path),
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode().strip()
            raise RuntimeError(
                f"Function call failed (exit {proc.returncode}): {error_msg}"
            )

        return stdout.decode().strip()

    async def query(self, uri: str) -> str:
        """Query a resource."""
        return await self.run_subcommand("query", ["--uri", uri])

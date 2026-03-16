"""Parse CLI --help output to extract commands and options."""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from mcp_anything.models.analysis import Capability, IPCType, ParameterSpec


def parse_help_text(help_text: str, app_name: str) -> list[Capability]:
    """Parse --help output text into capabilities."""
    if not help_text.strip():
        return []

    capabilities = []

    # Try to detect subcommands section
    subcommands = _extract_subcommands(help_text)
    for name, desc in subcommands:
        capabilities.append(Capability(
            name=name.replace("-", "_"),
            description=desc or f"Run {name} command",
            category="cli_command",
            parameters=[ParameterSpec(
                name="args",
                type="string",
                description=f"Arguments for {name}",
                required=False,
            )],
            ipc_type=IPCType.CLI,
            source_file=app_name,
        ))

    # If no subcommands found, try extracting grouped CLI options as tools
    if not capabilities:
        grouped = _extract_grouped_options(help_text, app_name)
        capabilities.extend(grouped)

    # If still nothing, try extracting individual options as a single run tool
    if not capabilities:
        options = _extract_options(help_text)
        if options:
            capabilities.append(Capability(
                name=f"run_{app_name.replace('-', '_')}",
                description=f"Run {app_name} with the given arguments",
                category="cli_command",
                parameters=[ParameterSpec(
                    name="args",
                    type="string",
                    description=f"Command-line arguments to pass to {app_name}",
                    required=True,
                )] + options[:20],  # Include top options as named params
                ipc_type=IPCType.CLI,
                source_file=app_name,
            ))

    return capabilities


def find_help_files(root: Path) -> list[Path]:
    """Find .txt files in a directory that look like CLI help output."""
    help_files = []
    for f in sorted(root.iterdir()):
        if f.is_file() and f.suffix in (".txt", ".help", ".usage"):
            try:
                content = f.read_text(errors="replace")
                # Heuristic: looks like help output if it has flags or usage patterns
                if (re.search(r"^\s*-\w", content, re.MULTILINE)
                        and len(content.strip()) > 50):
                    help_files.append(f)
            except OSError:
                pass
    return help_files


def _extract_subcommands(help_text: str) -> list[tuple[str, str]]:
    """Extract subcommands from help text.

    Handles common patterns:
    - "Commands:" or "Available commands:" sections
    - Indented lines with "command_name    Description"
    """
    commands: list[tuple[str, str]] = []
    in_commands_section = False

    for line in help_text.split("\n"):
        stripped = line.strip()

        # Detect commands section headers
        if re.match(
            r"^(commands|available commands|subcommands|positional arguments)\s*:?\s*$",
            stripped,
            re.IGNORECASE,
        ):
            in_commands_section = True
            continue

        # End of section: new section header (not commands-related)
        if in_commands_section and stripped and re.match(r"^[A-Z].*:\s*$", stripped):
            if not re.match(
                r"^(commands|available commands|subcommands)\s*:?\s*$",
                stripped,
                re.IGNORECASE,
            ):
                in_commands_section = False
                continue

        if in_commands_section:
            # Parse "  command_name    Description text"
            match = re.match(r"^\s{2,}(\w[\w-]*)\s{2,}(.+)", line)
            if match:
                cmd_name = match.group(1)
                cmd_desc = match.group(2).strip()
                if not cmd_name.startswith("-"):
                    commands.append((cmd_name, cmd_desc))

    return commands


def _extract_grouped_options(help_text: str, app_name: str) -> list[Capability]:
    """Extract CLI options grouped by section headers into separate tool capabilities.

    Handles help formats like ffmpeg where options are grouped under headers:
        Section name:
        -flag value   description
        -flag2        description
    """
    capabilities = []
    current_section = None
    current_options: list[tuple[str, str, str]] = []  # (flag, value_hint, desc)

    for line in help_text.split("\n"):
        stripped = line.strip()

        # Detect section headers: "Section name:" at the start of a line (not indented flags)
        section_match = re.match(r"^([A-Z][A-Za-z /()-]+):$", stripped)
        if section_match:
            # Save previous section
            if current_section and current_options:
                cap = _section_to_capability(current_section, current_options, app_name)
                if cap:
                    capabilities.append(cap)
            current_section = section_match.group(1).strip()
            current_options = []
            continue

        # Parse "-flag value  description" lines (single-dash flags like ffmpeg)
        opt_match = re.match(
            r"^-(\w[\w_]*)"       # flag name
            r"(?:\s+(\w[\w/.]*))??"  # optional value placeholder (non-greedy)
            r"\s{2,}"             # separator (at least 2 spaces)
            r"(.+)$",            # description
            stripped,
        )
        if opt_match and current_section:
            flag = opt_match.group(1)
            value_hint = opt_match.group(2) or ""
            desc = opt_match.group(3).strip()
            current_options.append((flag, value_hint, desc))

    # Final section
    if current_section and current_options:
        cap = _section_to_capability(current_section, current_options, app_name)
        if cap:
            capabilities.append(cap)

    return capabilities


def _section_to_capability(
    section: str,
    options: list[tuple[str, str, str]],
    app_name: str,
) -> Optional[Capability]:
    """Convert a section of CLI options into a Capability."""
    # Clean section name for use as tool name
    section_slug = re.sub(r"[^a-z0-9]+", "_", section.lower()).strip("_")
    if not section_slug:
        return None

    tool_name = f"{app_name.replace('-', '_')}_{section_slug}"

    params = []
    for flag, value_hint, desc in options:
        param_name = flag.replace("-", "_")
        param_type = "boolean"
        if value_hint:
            type_map = {
                "file": "string", "url": "string", "path": "string",
                "device": "string", "name": "string", "fmt": "string",
                "codec": "string", "number": "integer", "bytes": "integer",
                "loglevel": "string", "volume": "integer", "time": "string",
                "bitrate": "string", "size": "string", "mode": "string",
                "standard": "string", "channel": "string", "args": "string",
                "flags": "string", "limit": "integer", "ratio": "string",
            }
            param_type = type_map.get(value_hint.lower(), "string")
        params.append(ParameterSpec(
            name=param_name,
            type=param_type,
            description=desc,
            required=False,
        ))

    return Capability(
        name=tool_name,
        description=f"{section} options for {app_name}",
        category="cli_options",
        parameters=params,
        ipc_type=IPCType.CLI,
        source_file=app_name,
    )


def _extract_options(help_text: str) -> list[ParameterSpec]:
    """Extract options/flags from help text."""
    options = []

    pattern = re.compile(
        r"^\s+"
        r"(?:(-\w),?\s+)?"          # short flag (optional)
        r"(--[\w-]+)"               # long flag (required)
        r"(?:\s+(\w+))?"            # value placeholder (optional)
        r"\s{2,}"                   # separator
        r"(.+?)$",                  # description
        re.MULTILINE,
    )

    for match in pattern.finditer(help_text):
        long_flag = match.group(2)
        value_type = match.group(3)
        description = match.group(4).strip()

        name = long_flag.lstrip("-").replace("-", "_")

        # Determine type
        param_type = "string"
        if value_type:
            type_map = {
                "INT": "integer", "FLOAT": "float", "NUM": "integer",
                "FILE": "string", "PATH": "string", "DIR": "string",
                "URL": "string", "TEXT": "string",
            }
            param_type = type_map.get(value_type.upper(), "string")
        else:
            param_type = "boolean"

        # Check for default values
        default = None
        default_match = re.search(r"\(default[:\s]+([^)]+)\)", description)
        if default_match:
            default = default_match.group(1).strip()

        options.append(ParameterSpec(
            name=name,
            type=param_type,
            description=description,
            required=False,
            default=default,
        ))

    return options


def run_help_command(codebase_path: Path) -> Optional[str]:
    """Try to run --help on a project in the codebase."""
    path = codebase_path.resolve()

    # Check for Go main.go or cmd/
    if (path / "main.go").exists() or (path / "cmd").is_dir():
        output = _try_command(["go", "run", ".", "--help"], cwd=path)
        if output:
            return output

    # Check for Cargo.toml (Rust)
    if (path / "Cargo.toml").exists():
        output = _try_command(["cargo", "run", "--", "--help"], cwd=path, timeout=30)
        if output:
            return output

    # Check for package.json (Node.js)
    pkg_json = path / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text())
            if "bin" in pkg:
                bin_entries = pkg["bin"]
                if isinstance(bin_entries, str):
                    output = _try_command(["node", str(path / bin_entries), "--help"], cwd=path)
                    if output:
                        return output
                elif isinstance(bin_entries, dict):
                    for bin_path in bin_entries.values():
                        output = _try_command(["node", str(path / bin_path), "--help"], cwd=path)
                        if output:
                            return output
        except Exception:
            pass

    return None


def _try_command(cmd: list[str], cwd: Path, timeout: int = 15) -> Optional[str]:
    """Run a command and return stdout+stderr if it produces meaningful output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cwd),
        )
        output = result.stdout or result.stderr
        if output and len(output.strip()) > 20:
            return output.strip()
    except Exception:
        pass
    return None

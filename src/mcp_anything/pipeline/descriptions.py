"""Description overrides for generated MCP tools.

Writes a descriptions.yaml after DESIGN with all tool descriptions.
On --resume, merges user edits back into the design before IMPLEMENT.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from mcp_anything.models.design import ServerDesign


def write_descriptions_file(design: "ServerDesign", path: Path) -> None:
    """Write a descriptions.yaml file from the current design."""
    tools: dict = {}
    for tool in design.tools:
        entry: dict = {"description": tool.description}
        if tool.parameters:
            params = {}
            for p in tool.parameters:
                params[p.name] = {"description": p.description or ""}
            entry["parameters"] = params
        tools[tool.name] = entry

    data = {"tools": tools}
    path.write_text(
        "# Edit tool descriptions below. Run `mcp-anything generate --resume` to apply.\n"
        + yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    )


def merge_description_overrides(design: "ServerDesign", path: Path) -> int:
    """Merge description overrides from descriptions.yaml into the design.

    Returns the number of overrides applied.
    """
    try:
        raw = yaml.safe_load(path.read_text())
    except Exception:
        return 0

    if not isinstance(raw, dict) or "tools" not in raw:
        return 0

    tool_overrides = raw["tools"]
    if not isinstance(tool_overrides, dict):
        return 0

    count = 0
    tool_index = {t.name: t for t in design.tools}

    for tool_name, overrides in tool_overrides.items():
        if tool_name not in tool_index or not isinstance(overrides, dict):
            continue
        tool = tool_index[tool_name]

        if "description" in overrides and overrides["description"] != tool.description:
            tool.description = overrides["description"]
            count += 1

        param_overrides = overrides.get("parameters")
        if isinstance(param_overrides, dict):
            param_index = {p.name: p for p in tool.parameters}
            for param_name, po in param_overrides.items():
                if param_name not in param_index or not isinstance(po, dict):
                    continue
                param = param_index[param_name]
                if "description" in po and po["description"] != param.description:
                    param.description = po["description"]
                    count += 1

    return count

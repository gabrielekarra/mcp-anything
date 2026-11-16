"""LLM-assisted semantic analysis using Claude API."""

from pathlib import Path
from typing import Optional

from mcp_anything.models.analysis import (
    AnalysisResult,
    Capability,
    FileInfo,
    IPCMechanism,
    IPCType,
    Language,
    ParameterSpec,
)


def _build_evidence_prompt(
    app_name: str,
    files: list[FileInfo],
    ipc_mechanisms: list[IPCMechanism],
    code_samples: dict[str, str],
) -> str:
    """Build the prompt for Claude API analysis."""
    file_summary = "\n".join(
        f"  - {f.path} ({f.language.value}, {f.line_count} lines)"
        for f in files[:50]
    )

    ipc_summary = "\n".join(
        f"  - {m.ipc_type.value} (confidence: {m.confidence:.2f}): {', '.join(m.evidence[:5])}"
        for m in ipc_mechanisms
    )

    samples = "\n\n".join(
        f"### {path}\n```\n{code[:2000]}\n```"
        for path, code in list(code_samples.items())[:10]
    )

    return f"""Analyze this application called "{app_name}" and identify its capabilities that could be exposed as MCP (Model Context Protocol) tools.

## Source Files
{file_summary}

## Detected IPC Mechanisms
{ipc_summary}

## Key Source Code Samples
{samples}

## Instructions
Return a JSON object with:
1. "app_description": A one-sentence description of what this application does.
2. "capabilities": An array of capabilities, each with:
   - "name": snake_case function name for the MCP tool
   - "description": What this capability does
   - "category": Grouping category (e.g., "file_ops", "rendering", "modeling")
   - "parameters": Array of {{"name", "type", "description", "required"}}
   - "return_type": The return type (usually "string" or "dict")
   - "source_file": Which file implements this
   - "source_function": The function/method name

Focus on capabilities that:
- Can be invoked programmatically
- Take clear inputs and produce outputs
- Would be useful to an AI assistant

Return ONLY valid JSON, no markdown formatting."""


async def llm_analyze(
    app_name: str,
    root: Path,
    files: list[FileInfo],
    ipc_mechanisms: list[IPCMechanism],
) -> Optional[AnalysisResult]:
    """Use the model (see mcp_anything.llm) to semantically analyze the codebase.

    Returns None if no model is available or the call fails.
    """

    # Gather code samples from entry points and API surfaces
    code_samples: dict[str, str] = {}
    priority_files = [f for f in files if f.is_entry_point or f.is_api_surface]
    if not priority_files:
        priority_files = [f for f in files if f.language == Language.PYTHON][:10]

    for fi in priority_files[:10]:
        try:
            content = (root / fi.path).read_text(errors="replace")
            code_samples[fi.path] = content[:3000]
        except OSError:
            continue

    prompt = _build_evidence_prompt(app_name, files, ipc_mechanisms, code_samples)

    try:
        from mcp_anything.pipeline.llm_client import call_llm_for_json

        data = call_llm_for_json(prompt, max_tokens=4096)

        primary_ipc = None
        if ipc_mechanisms:
            primary_ipc = max(ipc_mechanisms, key=lambda m: m.confidence).ipc_type

        capabilities = []
        for cap_data in data.get("capabilities", []):
            params = [
                ParameterSpec(
                    name=p["name"],
                    type=p.get("type", "string"),
                    description=p.get("description", ""),
                    required=p.get("required", True),
                )
                for p in cap_data.get("parameters", [])
            ]
            capabilities.append(
                Capability(
                    name=cap_data["name"],
                    description=cap_data.get("description", ""),
                    category=cap_data.get("category", "general"),
                    parameters=params,
                    return_type=cap_data.get("return_type", "string"),
                    source_file=cap_data.get("source_file", ""),
                    source_function=cap_data.get("source_function", ""),
                    ipc_type=primary_ipc,
                )
            )

        languages = list({f.language for f in files if f.language != Language.OTHER})

        return AnalysisResult(
            app_name=app_name,
            app_description=data.get("app_description", ""),
            languages=languages,
            files=files,
            ipc_mechanisms=ipc_mechanisms,
            capabilities=capabilities,
            primary_ipc=primary_ipc,
            entry_points=[f.path for f in files if f.is_entry_point],
        )

    except Exception:
        return None

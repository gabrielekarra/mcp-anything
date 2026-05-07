"""LLM prompt templates for Skybridge React view generation."""

from typing import Optional


def build_view_prompt(
    tool_name: str,
    tool_description: str,
    parameters: list[dict],
    return_type: str,
    domain_description: str,
    use_cases: list[str],
    glossary: list[dict],
) -> str:
    params_text = "\n".join(
        f"  - {p['name']} ({p['type']}, {'required' if p.get('required') else 'optional'}): {p.get('description', '')}"
        for p in parameters
        if p.get("name") != "verbose"
    )
    use_cases_text = "\n".join(f"  - {uc}" for uc in use_cases[:5]) if use_cases else "  (none provided)"
    glossary_text = "\n".join(
        f"  - {g['term']}: {g['definition']}" for g in glossary[:10]
    ) if glossary else ""

    return f"""Generate a React TSX view component for a Skybridge MCP tool.

## Tool
- **Name**: {tool_name}
- **Description**: {tool_description}
- **Parameters**:
{params_text or '  (none)'}
- **Return type**: {return_type}

## Domain context
{domain_description or '(not provided)'}

## Relevant use cases
{use_cases_text}

{f'## Glossary{chr(10)}{glossary_text}' if glossary_text else ''}

## Requirements
1. Use ONLY these Skybridge imports from `"skybridge/web"`: `useCallTool`, `useViewState`, `useLayout`, `useDisplayMode`, `mountView`. **Do NOT use `useToolInfo`**.
2. The component must handle all four states: `"idle"`, `"loading"`, `"error"`, and the success state.
3. Show relevant tool parameters and context in the idle state.
4. Display the result in a clear, human-readable way appropriate to the domain.
5. Use inline styles only (no external CSS libraries).
6. Do NOT import React explicitly — Skybridge's Vite plugin handles the JSX transform.
7. `useCallTool` must receive the tool name as a string argument: `useCallTool("{tool_name}")`. It returns `{{ status, data, error, callTool }}`. States are `"idle"`, `"pending"`, `"success"`, `"error"` — NOT "loading". `data` is typed `unknown` — always assign it to a variable typed `any` before use: `const result: any = data`.
8. Call `mountView(<ComponentName />)` as the last statement (JSX element, not the function).
9. Add `export default ComponentName;` before the `mountView` call.
10. Name the component `{_to_pascal(tool_name)}View`.
11. `useLayout()` takes **zero arguments** — do NOT pass a config object to it.
12. `useDisplayMode()` returns a **tuple** `[displayMode, setDisplayMode]` — always destructure it: `const [displayMode] = useDisplayMode();`. Then compare `displayMode` as a string (e.g. `displayMode === "compact"`).

## Output
Return ONLY the complete `.tsx` file contents — no markdown fences, no explanation.
The file must be valid TypeScript JSX.
"""


def _to_pascal(name: str) -> str:
    return "".join(w.capitalize() for w in name.replace("-", "_").split("_"))

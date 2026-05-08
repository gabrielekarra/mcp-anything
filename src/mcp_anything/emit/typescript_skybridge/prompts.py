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
2. The component must handle all four states: `"idle"`, `"pending"`, `"error"`, and the `"success"` state.
3. Show relevant tool parameters and context in the idle state.
4. Display the result in a clear, human-readable way appropriate to the domain.
5. Use inline styles only (no external CSS libraries).
6. Do NOT import React explicitly — Skybridge's Vite plugin handles the JSX transform. You may import specific React types or hooks: `import {{ useState, useMemo }} from "react";` or `import type {{ CSSProperties }} from "react";`.
7. `useCallTool` signature: `useCallTool<TArgs, TResponse>(name: string)`. It returns `{{ status, data, error, callTool }}`. States are `"idle"`, `"pending"`, `"success"`, `"error"`. `callTool(args)` takes the args object directly — do NOT pass a side-effects object as the second argument unless you need callbacks. `data` is typed `unknown` — always assign it: `const result: any = data`.
8. Call `mountView(<ComponentName />)` as the last statement (JSX element, not the function).
9. Add `export default ComponentName;` before the `mountView` call.
10. Name the component `{_to_pascal(tool_name)}View`.
11. `useLayout()` takes **zero arguments** — do NOT pass a config object to it.
12. `useDisplayMode()` returns `[displayMode, setDisplayMode]` where `displayMode` is `"pip" | "inline" | "fullscreen" | "modal"`. **NEVER compare it to `"compact"`** — that value does not exist.
13. `useViewState` signature: `useViewState<T extends object>(defaultState: T)` — it takes **one argument, an object**. Example: `const [state, setState] = useViewState({{ query: "", page: 1 }})`. Access fields as `state.query`. **NEVER call it as `useViewState<string>("key", "default")` — that is wrong.**
14. Only use standard HTML/SVG JSX elements (`div`, `span`, `button`, `input`, `svg`, `path`, etc.). Do NOT invent custom element names like `<triangle>` or `<card>`.

## Output
Return ONLY the complete `.tsx` file contents — no markdown fences, no explanation.
The file must be valid TypeScript JSX.
"""


def _to_pascal(name: str) -> str:
    return "".join(w.capitalize() for w in name.replace("-", "_").split("_"))

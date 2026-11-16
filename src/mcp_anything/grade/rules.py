"""The rules a tool list is graded on.

Every rule is deterministic: the same tools always give the same findings and
the same score, with no model involved. A rule has an id, the most points it
can cost, and the fix to suggest. Rules about single tools cost in proportion
to how many tools they affect (on a square-root curve, so a few problems still
show); rules about the whole server cost a fixed share.
"""

from __future__ import annotations

import difflib
import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass, field

# Verbs that change or destroy state, and verbs that only read.
DESTRUCTIVE = {"delete", "remove", "drop", "destroy", "purge", "erase", "truncate", "revoke", "cancel", "void",
               "terminate", "kill", "reset", "wipe", "uninstall", "archive", "disable", "unpublish", "overwrite"}
READ_ONLY = {"get", "list", "search", "read", "fetch", "find", "describe", "show", "query", "lookup", "count",
             "view", "retrieve", "check", "inspect", "browse"}
CRUD = {"create", "add", "new", "get", "read", "fetch", "retrieve", "update", "edit", "patch", "set", "modify",
        "delete", "remove", "list", "search", "find"}


@dataclass
class Finding:
    rule: str
    message: str
    tools: list[str] = field(default_factory=list)
    share: float = 1.0  # for server-wide rules: how much of the rule's points this costs


@dataclass
class Rule:
    id: str
    title: str
    points: float  # the most this rule can cost
    fix: str
    scope: str = "tool"  # "tool": proportional to affected tools; "server": fixed


RULES = [
    Rule("G01", "Too many tools", 15, "Group related operations into fewer tools, or split the server by domain. "
         "Agents choose worse, and spend more context, the more tools they see.", "server"),
    Rule("G02", "Tool list costs too much context", 15, "Shorten descriptions and schemas, and drop tools agents "
         "rarely need: the whole list is sent with every request.", "server"),
    Rule("G03", "Tools without a description", 40, "Describe what each tool does, when to use it and what it returns."),
    Rule("G04", "Vague descriptions", 15, "Write at least one full sentence that says more than the tool's name."),
    Rule("G05", "Overlong descriptions", 3, "Keep descriptions under about 1,000 characters; move detail to docs."),
    Rule("G06", "Undocumented parameters", 25, "Describe every parameter: format, units, allowed values."),
    Rule("G07", "Parameters without a type", 15, "Give every parameter a JSON type (or enum, anyOf, $ref)."),
    Rule("G08", "Opaque object parameters", 5, "Declare the properties of object parameters, so agents know their shape."),
    Rule("G09", "Inconsistent tool names", 5, "Use one naming style (snake_case is the convention), with names of "
         "at most 64 letters, digits, underscores or hyphens.", "server"),
    Rule("G10", "CRUD operations not grouped", 6, "Consider one manage_<resource>(operation=...) tool where several "
         "tools act on the same resource: fewer, broader tools are easier to choose from."),
    Rule("G11", "Destructive tools without annotations", 10, "Set annotations.destructiveHint = true on tools that "
         "delete or overwrite, so clients can ask before running them."),
    Rule("G12", "Read-only tools without annotations", 3, "Set annotations.readOnlyHint = true on tools that only read."),
    Rule("G13", "Near-duplicate tools", 8, "Merge tools that do the same thing, or make their descriptions say how "
         "they differ."),
    Rule("G14", "Allowed values listed only in prose", 3, "When a description lists the allowed values, put them in "
         "an enum so they are enforced."),
    Rule("G15", "Missing or invalid input schema", 30, "Every tool needs an inputSchema of type object."),
]
BY_ID = {rule.id: rule for rule in RULES}


# --- helpers ----------------------------------------------------------------------------


def words(name: str) -> list[str]:
    """Split snake_case, kebab-case, camelCase and dotted names into lowercase words."""
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return [part for part in re.split(r"[_\-.\s/]+", name.lower()) if part]


def style(name: str) -> str:
    if re.fullmatch(r"[a-z0-9]+(_[a-z0-9]+)*", name):
        return "snake_case" if "_" in name else "single word"
    if re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)+", name):
        return "kebab-case"
    if re.fullmatch(r"[a-z]+([A-Z][a-z0-9]*)+", name):
        return "camelCase"
    if re.fullmatch(r"([A-Z][a-z0-9]*)+", name):
        return "PascalCase"
    return "other"


def schema_of(tool: dict) -> dict:
    schema = tool.get("inputSchema")
    return schema if isinstance(schema, dict) else {}


def parameters(tool: dict) -> dict:
    properties = schema_of(tool).get("properties")
    return properties if isinstance(properties, dict) else {}


def estimated_tokens(tools: list[dict]) -> int:
    """About four characters a token, over what a client sends: name, description, schema."""
    return len(json.dumps([{key: tool.get(key) for key in ("name", "description", "inputSchema")} for tool in tools])) // 4


def _singular(word: str) -> str:
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word


# --- the checks ------------------------------------------------------------------------------


def check(tools: list[dict]) -> list[Finding]:
    findings: list[Finding] = []
    count = len(tools)

    if count > 40:
        findings.append(Finding("G01", f"{count} tools: well past the 20 to 30 that agents handle well."))
    elif count > 25:
        findings.append(Finding("G01", f"{count} tools: more than agents handle comfortably.", share=0.5))

    tokens = estimated_tokens(tools)
    if tokens > 10_000:
        findings.append(Finding("G02", f"The tool list is about {tokens:,} tokens, sent with every request.",
                                share=1.0 if tokens > 25_000 else 0.5))

    def per_tool(rule, message, names):
        if names:
            findings.append(Finding(rule, message.format(n=len(names)), sorted(names)))

    per_tool("G15", "{n} tools have no input schema of type object.",
             [t["name"] for t in tools if schema_of(t).get("type", "object") != "object" or "inputSchema" not in t])

    described = {t["name"]: (t.get("description") or "").strip() for t in tools}
    per_tool("G03", "{n} tools have no description.", [name for name, text in described.items() if not text])
    vague = []
    for name, text in described.items():
        if not text:
            continue
        said = set(words(text))
        if len(text) < 25 or len(said - set(words(name)) - {"the", "a", "an", "of", "to", "for"}) < 2:
            vague.append(name)
    per_tool("G04", "{n} descriptions are too short to tell an agent when to use the tool.", vague)
    per_tool("G05", "{n} descriptions are over 1,000 characters.", [n for n, text in described.items() if len(text) > 1000])

    undocumented, untyped, opaque, prose_enums = [], [], [], []
    for tool in tools:
        for name, spec in parameters(tool).items():
            spec = spec if isinstance(spec, dict) else {}
            label = f"{tool['name']}.{name}"
            if not (spec.get("description") or "").strip():
                undocumented.append(label)
            if not any(key in spec for key in ("type", "enum", "const", "anyOf", "oneOf", "allOf", "$ref")):
                untyped.append(label)
            if spec.get("type") == "object" and not spec.get("properties") and not spec.get("additionalProperties"):
                opaque.append(label)
            text = spec.get("description") or ""
            if spec.get("type") == "string" and "enum" not in spec and re.search(
                    r"(one of|must be|either|allowed values?|possible values?|valid values?)\b|\w+\s*\|\s*\w+\s*\|", text, re.I):
                prose_enums.append(label)
    per_tool("G06", "{n} parameters have no description.", undocumented)
    per_tool("G07", "{n} parameters have no type.", untyped)
    per_tool("G08", "{n} object parameters do not declare their properties.", opaque)
    per_tool("G14", "{n} parameters list their allowed values in prose instead of an enum.", prose_enums)

    styles = defaultdict(list)
    for tool in tools:
        styles[style(tool["name"])].append(tool["name"])
    real_styles = {key for key in styles if key not in ("single word",)}
    bad_names = [t["name"] for t in tools if len(t["name"]) > 64 or not re.fullmatch(r"[A-Za-z0-9_\-.]+", t["name"])]
    if len(real_styles) > 1 or bad_names:
        mix = ", ".join(f"{len(names)} {key}" for key, names in sorted(styles.items()))
        findings.append(Finding("G09", f"Tool names mix styles ({mix})" + (f"; {len(bad_names)} names are invalid or too long" if bad_names else "") + ".",
                                sorted(bad_names)))

    resources = defaultdict(set)
    for tool in tools:
        parts = words(tool["name"])
        if len(parts) >= 2 and parts[0] in CRUD:
            resources[_singular(parts[-1])].add(tool["name"])
    ungrouped = sorted(name for names in resources.values() if len(names) >= 3 for name in names)
    if ungrouped:
        groups = [f"{resource} ({len(names)})" for resource, names in sorted(resources.items()) if len(names) >= 3]
        findings.append(Finding("G10", f"Several tools act on the same resource: {', '.join(groups)}.", ungrouped))

    destructive, read_only = [], []
    for tool in tools:
        verbs = set(words(tool["name"])[:2])
        annotations = tool.get("annotations") or {}
        if verbs & DESTRUCTIVE and annotations.get("destructiveHint") is not True:
            destructive.append(tool["name"])
        if verbs & READ_ONLY and not verbs & DESTRUCTIVE and annotations.get("readOnlyHint") is not True:
            read_only.append(tool["name"])
    per_tool("G11", "{n} tools that delete or overwrite have no destructiveHint.", destructive)
    per_tool("G12", "{n} read-only tools have no readOnlyHint.", read_only)

    duplicates = set()
    items = [(name, text.lower()) for name, text in described.items() if len(text) >= 25]
    for index, (name, text) in enumerate(items):
        for other, other_text in items[index + 1:]:
            if text == other_text or difflib.SequenceMatcher(None, text, other_text).quick_ratio() > 0.97 and \
                    difflib.SequenceMatcher(None, text, other_text).ratio() > 0.95:
                duplicates.update((name, other))
    per_tool("G13", "{n} tools have the same or nearly the same description as another.", sorted(duplicates))
    return findings


def penalty(finding: Finding, tool_count: int) -> float:
    rule = BY_ID[finding.rule]
    if rule.scope == "server":
        return rule.points * finding.share
    affected = len({label.split(".")[0] for label in finding.tools}) if finding.tools else 1
    return rule.points * min(1.0, math.sqrt(affected / max(1, tool_count)))

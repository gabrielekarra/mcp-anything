"""Issue #16 (reproducible comparisons) and issue #24 (the README is accurate)."""

import re
import shlex
from pathlib import Path

from mcp_anything.cli import COMMANDS, build_parser

ROOT = Path(__file__).parent.parent
DOCS = [ROOT / "README.md", ROOT / "examples" / "README.md"]
UNVERIFIABLE = ["took months", "| months", "~30 seconds", "~6 seconds", "would have taken a team"]


def test_no_unverifiable_claims():
    for path in DOCS:
        text = path.read_text().lower()
        for phrase in UNVERIFIABLE:
            assert phrase not in text, f"{path.name}: {phrase!r}"


def test_readme_comparisons_are_sourced():
    """A table comparing with another project's server must name the command and date that produced it."""
    for path in DOCS:
        lines = path.read_text().splitlines()
        for index, line in enumerate(lines):
            numbers = re.search(r"\d", line) and not re.fullmatch(r"[|\s`\w-]*", line)
            if line.startswith("|") and re.search(r"\bofficial\b", line, re.I) and "|---" not in line and numbers:
                after = "\n".join(lines[index:index + 30])
                assert re.search(r"Measured on \d{4}-\d{2}-\d{2} with `mcp-anything", after), f"{path.name}: {line}"


def test_readme_commands_exist():
    parser = build_parser()
    subparsers = next(a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction").choices
    text = (ROOT / "README.md").read_text()
    blocks = re.findall(r"```(?:bash)?\n(.*?)```", text, re.S)
    commands = [line.split("#")[0].strip() for block in blocks for line in block.splitlines()
                if line.strip().startswith("mcp-anything ")]
    assert len(commands) > 10
    for command in commands:
        words = shlex.split(command)[1:]
        sub = words[0] if words[0] in COMMANDS else "quick"  # mcp-anything <source>
        assert sub in subparsers, command
        known = {option for action in subparsers[sub]._actions for option in action.option_strings}
        for word in words:
            if word.startswith("--"):
                assert word.split("=")[0] in known, f"{command}: {word}"


def test_readme_links_resolve():
    text = re.sub(r"<!--.*?-->", "", (ROOT / "README.md").read_text(), flags=re.S)
    for link in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", text):
        if not link.startswith(("http://", "https://", "mailto:")):
            assert (ROOT / link).exists(), link
    for anchor in re.findall(r"\]\(#([^)]+)\)", text):
        headings = {re.sub(r"[^a-z0-9 -]", "", h.lower()).strip().replace(" ", "-")
                    for h in re.findall(r"^#+ (.+)$", text, re.M)}
        assert anchor in headings, anchor

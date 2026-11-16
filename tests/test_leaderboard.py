"""Issue #22: the leaderboard script."""

import importlib.util
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "fixtures" / "leaderboard"
spec = importlib.util.spec_from_file_location("leaderboard", ROOT / "scripts" / "leaderboard.py")
leaderboard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(leaderboard)


def test_leaderboard_from_recorded_tool_lists(tmp_path):
    out = tmp_path / "board.md"
    leaderboard.main([str(FIXTURES / "servers.yaml"), "-o", str(out), "--date", "2026-11-16", "--timeout", "5"])
    text = out.read_text()
    assert "Graded on 2026-11-16 with mcp-anything" in text
    rows = [line for line in text.splitlines() if line.startswith("| 1 ") or line.startswith("| 2 ")]
    assert rows[0].startswith("| 1 | [Good server](https://example.com/good) | A | 100 | 3 |")
    assert rows[1].startswith("| 2 | [Sloppy server](https://example.com/sloppy) | F |")
    saved = json.loads(out.with_suffix(".json").read_text())
    assert {row["name"] for row in saved} == {"Good server", "Sloppy server", "Needs a token", "Not installed"}


def test_unreachable_server_is_reported(tmp_path):
    out = tmp_path / "board.md"
    leaderboard.main([str(FIXTURES / "servers.yaml"), "-o", str(out), "--timeout", "5"])
    text = out.read_text()
    assert "- Needs a token: needs NO_SUCH_TOKEN_FOR_TESTS" in text
    assert "- Not installed: Cannot start `definitely-not-a-command`" in text


def test_server_list_is_complete():
    for entry in yaml.safe_load((ROOT / "scripts" / "servers.yaml").read_text())["servers"]:
        assert entry["name"] and entry["source"].startswith("https://") and ("target" in entry or "tools" in entry)

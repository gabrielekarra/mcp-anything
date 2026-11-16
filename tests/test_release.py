"""Issue #14 (CI and releases) and issue #17 (a lighter repository)."""

import importlib.metadata
import re
from pathlib import Path

import yaml

import mcp_anything

ROOT = Path(__file__).parent.parent


def test_version_is_single_sourced():
    assert importlib.metadata.version("mcp-anything") == mcp_anything.__version__
    project = (ROOT / "pyproject.toml").read_text().split("[project.urls]")[0]
    assert 'dynamic = ["version"]' in project and not re.search(r"^version\s*=", project, re.M)


def test_workflows_are_valid():
    tests = yaml.safe_load((ROOT / ".github/workflows/tests.yml").read_text())
    matrix = tests["jobs"]["pytest"]["strategy"]["matrix"]
    assert set(matrix["os"]) == {"ubuntu-latest", "macos-latest"}
    assert matrix["python-version"] == ["3.10", "3.11", "3.12", "3.13"]
    assert any("not realworld" in step.get("run", "") for step in tests["jobs"]["pytest"]["steps"])

    release = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text())
    triggers = release.get("on") or release.get(True)  # YAML reads a bare `on` key as True
    assert triggers == {"push": {"tags": ["v*"]}}
    assert release["jobs"]["publish"]["permissions"] == {"id-token": "write"}
    assert any("does not match version" in step.get("run", "") for step in release["jobs"]["build"]["steps"])


def test_banner_is_small():
    banners = [path for path in ROOT.glob("banner.*")]
    assert banners and all(path.stat().st_size < 500_000 for path in banners)
    readme = (ROOT / "README.md").read_text()
    assert any(f"]({path.name})" in readme for path in banners)

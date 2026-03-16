"""Tests for the implement and package phases."""

from unittest.mock import MagicMock, patch

from mcp_anything.pipeline.package import PackagePhase


class TestInstallDependencies:
    def test_no_install_hint_no_error(self):
        """When there's no install hint, target install is skipped."""
        phase = PackagePhase()
        ctx = MagicMock()
        ctx.manifest.design.target_install_hint = ""
        ctx.console.print = MagicMock()

        errors = phase._install_dependencies(ctx, MagicMock())
        # Should only try to install the generated server, not the target
        target_calls = [
            c for c in ctx.console.print.call_args_list
            if "Installing target" in str(c)
        ]
        assert len(target_calls) == 0

    def test_install_handles_subprocess_error(self):
        """Install errors are returned as warnings, not raised."""
        phase = PackagePhase()
        ctx = MagicMock()
        ctx.manifest.design.target_install_hint = "pip install -e /nonexistent"
        ctx.console.print = MagicMock()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="not found")
            errors = phase._install_dependencies(ctx, MagicMock())

        # Should have errors but not raise
        assert len(errors) >= 1

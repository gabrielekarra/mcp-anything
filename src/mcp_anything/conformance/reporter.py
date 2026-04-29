"""CI-friendly conformance report formatting."""

from mcp_anything.models.validation import ConformanceReport


class ConformanceReporter:
    @staticmethod
    def to_ci_output(report: ConformanceReport) -> str:
        lines = [
            f"Conformance Report — {report.server_name} ({report.backend_target})",
            f"  Eval coverage: {report.coverage_ratio:.1%} "
            f"({'PASS' if report.coverage_ratio >= report.threshold else 'FAIL'}, "
            f"threshold: {report.threshold:.0%})",
        ]

        if report.contract_checks:
            failed = [c for c in report.contract_checks if not c.passed]
            passed_count = len(report.contract_checks) - len(failed)
            lines.append(
                f"  Contract items: {passed_count}/{len(report.contract_checks)} passed"
            )
            for c in failed:
                reason = f" — {c.reason}" if c.reason else ""
                lines.append(f"    FAIL {c.id}{reason}")

        status = "PASSED" if report.passed else "FAILED"
        lines.append(f"Overall: {status}")
        return "\n".join(lines)

    @staticmethod
    def to_github_annotations(report: ConformanceReport) -> str:
        """Emit GitHub Actions annotation format for failed items."""
        lines = []
        for c in report.contract_checks:
            if not c.passed:
                reason = c.reason or "contract item failed"
                lines.append(f"::error title=Contract {c.id}::{reason}")
        if report.coverage_ratio < report.threshold:
            lines.append(
                f"::error title=Coverage::"
                f"Eval coverage {report.coverage_ratio:.1%} below threshold {report.threshold:.0%}"
            )
        return "\n".join(lines)

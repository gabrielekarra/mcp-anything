"""Tests for conformance parity assertion."""

import pytest

from mcp_anything.conformance.parity import ConformanceParity, ConformanceParityError
from mcp_anything.conformance.reporter import ConformanceReporter
from mcp_anything.models.validation import ConformanceReport, ContractCheckResult, EvalResult


def _make_report(results: dict[str, bool], backend: str = "fastmcp") -> ConformanceReport:
    report = ConformanceReport(
        server_name="test",
        backend_target=backend,
        threshold=0.80,
        results=[EvalResult(case_id=k, passed=v) for k, v in results.items()],
    )
    report.compute_coverage()
    return report


def test_parity_passes_when_same():
    py = _make_report({"ec-001": True, "ec-002": True, "ec-003": False}, "fastmcp")
    ts = _make_report({"ec-001": True, "ec-002": True, "ec-003": False}, "mcp-use")
    ConformanceParity.assert_parity(py, ts)  # should not raise


def test_parity_fails_on_divergence():
    py = _make_report({"ec-001": True, "ec-002": False}, "fastmcp")
    ts = _make_report({"ec-001": True, "ec-002": True}, "mcp-use")
    with pytest.raises(ConformanceParityError) as exc_info:
        ConformanceParity.assert_parity(py, ts)
    assert "ec-002" in str(exc_info.value)


def test_parity_fails_on_multiple_divergences():
    py = _make_report({"ec-001": True, "ec-002": False, "ec-003": True}, "fastmcp")
    ts = _make_report({"ec-001": False, "ec-002": True, "ec-003": True}, "mcp-use")
    with pytest.raises(ConformanceParityError) as exc_info:
        ConformanceParity.assert_parity(py, ts)
    err = exc_info.value
    assert len(err.divergences) == 2


def test_coverage_ratio():
    report = _make_report({"ec-001": True, "ec-002": True, "ec-003": False, "ec-004": False})
    assert report.coverage_ratio == 0.5
    assert not report.passed  # below 0.80 threshold


def test_coverage_passes():
    results = {f"ec-{i:03d}": True for i in range(9)}
    results["ec-010"] = False
    report = _make_report(results)
    assert report.coverage_ratio == 0.9
    assert report.passed


def test_reporter_ci_output():
    report = ConformanceReport(
        server_name="test",
        backend_target="fastmcp",
        threshold=0.80,
        contract_checks=[
            ContractCheckResult(id="C-01", passed=True),
            ContractCheckResult(id="C-05", passed=False, reason="Tool 'foo' description too short"),
        ],
        coverage_ratio=0.85,
        passed=True,
    )
    output = ConformanceReporter.to_ci_output(report)
    assert "C-05" in output
    assert "PASSED" in output or "FAILED" in output


def test_reporter_github_annotations():
    report = ConformanceReport(
        server_name="test",
        backend_target="fastmcp",
        contract_checks=[
            ContractCheckResult(id="C-17", passed=False, reason="Dockerfile not found"),
        ],
        coverage_ratio=0.5,
        threshold=0.80,
        passed=False,
    )
    output = ConformanceReporter.to_github_annotations(report)
    assert "::error" in output
    assert "C-17" in output
    assert "Coverage" in output

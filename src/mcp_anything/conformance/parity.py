"""Parity assertion between Python and TypeScript conformance reports."""

from dataclasses import dataclass

from mcp_anything.models.validation import ConformanceReport


@dataclass
class ParityDivergence:
    case_id: str
    python_passed: bool
    typescript_passed: bool


class ConformanceParityError(Exception):
    def __init__(self, divergences: list[ParityDivergence]) -> None:
        self.divergences = divergences
        lines = [f"Conformance parity FAILED — {len(divergences)} divergent case(s):"]
        for d in divergences:
            py = "PASS" if d.python_passed else "FAIL"
            ts = "PASS" if d.typescript_passed else "FAIL"
            lines.append(f"  {d.case_id}: Python={py}, TypeScript={ts}")
        super().__init__("\n".join(lines))


class ConformanceParity:
    @staticmethod
    def assert_parity(
        py_report: ConformanceReport,
        ts_report: ConformanceReport,
    ) -> None:
        """Raise ConformanceParityError if the two reports disagree on any eval case."""
        py_map = {r.case_id: r.passed for r in py_report.results}
        ts_map = {r.case_id: r.passed for r in ts_report.results}

        all_case_ids = set(py_map) | set(ts_map)
        divergences = []
        for case_id in sorted(all_case_ids):
            py_passed = py_map.get(case_id, False)
            ts_passed = ts_map.get(case_id, False)
            if py_passed != ts_passed:
                divergences.append(
                    ParityDivergence(
                        case_id=case_id,
                        python_passed=py_passed,
                        typescript_passed=ts_passed,
                    )
                )

        if divergences:
            raise ConformanceParityError(divergences)

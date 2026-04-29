"""Models for the validation harness (Phase 5) and conformance reporting."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class EvalCase(BaseModel):
    id: str
    brief_item_id: str
    tool_name: str
    input_params: dict = Field(default_factory=dict)
    expected_output_pattern: str = ""  # regex or JSONPath assertion
    expected_error: Optional[str] = None
    case_type: Literal["happy_path", "edge_case", "expected_error"] = "happy_path"


class EvalResult(BaseModel):
    case_id: str
    passed: bool
    actual_output: Optional[str] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class ContractCheckResult(BaseModel):
    id: str  # C-01 .. C-29
    passed: bool
    reason: Optional[str] = None


class ConformanceReport(BaseModel):
    server_name: str
    backend_target: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    eval_cases: list[EvalCase] = Field(default_factory=list)
    results: list[EvalResult] = Field(default_factory=list)
    coverage_ratio: float = 0.0
    threshold: float = 0.80
    passed: bool = False
    contract_checks: list[ContractCheckResult] = Field(default_factory=list)

    def compute_coverage(self) -> None:
        if not self.results:
            self.coverage_ratio = 0.0
        else:
            self.coverage_ratio = sum(1 for r in self.results if r.passed) / len(self.results)
        self.passed = self.coverage_ratio >= self.threshold

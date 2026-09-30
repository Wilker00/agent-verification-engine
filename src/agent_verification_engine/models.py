from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AgentAction:
    step: str
    kind: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ExecutionStep:
    index: int
    action: str
    tool: str | None = None
    result_summary: str | None = None
    success: bool = True
    file_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChangeArtifact:
    file_path: str
    status: str
    summary: str = ""
    risk: str = "medium"


@dataclass
class TestResult:
    name: str
    passed: bool
    attempt: int = 1


@dataclass
class VerificationFinding:
    id: str
    type: str
    subject: str
    severity: str
    evidence: list[str]
    reason: str
    review_priority: int = 0
    status: str = "open"


@dataclass
class VerificationReport:
    requirement: str
    original_plan: list[str] = field(default_factory=list)
    actual_actions: list[str] = field(default_factory=list)
    divergence_points: list[str] = field(default_factory=list)
    files_changed: list[ChangeArtifact] = field(default_factory=list)
    unexpected_changes: list[str] = field(default_factory=list)
    review_hotspots: list[VerificationFinding] = field(default_factory=list)
    verification_checklist: dict[str, str] = field(default_factory=dict)
    verification_status: str = "needs_review"


@dataclass
class AgentSession:
    session_id: str
    requirement: str
    planned_steps: list[str] = field(default_factory=list)
    planned_files: list[str] = field(default_factory=list)
    actual_steps: list[ExecutionStep] = field(default_factory=list)
    files_changed: list[ChangeArtifact] = field(default_factory=list)
    test_results: list[TestResult] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    verification_report: VerificationReport | None = None

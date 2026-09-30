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
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChangeArtifact:
    file_path: str
    status: str
    summary: str
    risk: str = "medium"


@dataclass
class VerificationReport:
    requirement: str
    original_plan: list[str] = field(default_factory=list)
    actual_actions: list[str] = field(default_factory=list)
    divergence_points: list[str] = field(default_factory=list)
    files_changed: list[ChangeArtifact] = field(default_factory=list)
    unexpected_changes: list[str] = field(default_factory=list)
    review_hotspots: list[str] = field(default_factory=list)
    verification_status: str = "needs_review"
    confidence: float = 0.0


@dataclass
class AgentSession:
    session_id: str
    requirement: str
    planned_steps: list[str] = field(default_factory=list)
    actual_steps: list[ExecutionStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    verification_report: VerificationReport | None = None

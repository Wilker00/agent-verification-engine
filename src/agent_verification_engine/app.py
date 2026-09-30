from __future__ import annotations

from typing import Iterable

from .models import AgentSession, ChangeArtifact, VerificationReport


def summarize_session(session: AgentSession) -> VerificationReport:
    """Create a concise human-readable verification artifact for a coding-agent session."""

    actual_actions = [step.action for step in session.actual_steps]
    divergence_points: list[str] = []

    if session.planned_steps:
        for planned in session.planned_steps:
            if planned not in actual_actions:
                divergence_points.append(f"Planned step not observed in execution: {planned}")

    unexpected_changes: list[str] = []
    review_hotspots: list[str] = []

    files_changed = [
        ChangeArtifact(
            file_path="unknown",
            status="modified",
            summary="Placeholder artifact generated from trace.",
            risk="medium",
        )
    ]

    if divergence_points:
        review_hotspots.append("Trajectory divergence")
        unexpected_changes.extend(divergence_points)

    if not review_hotspots:
        review_hotspots.append("No obvious divergence detected")

    confidence = 0.5
    if not divergence_points:
        confidence = 0.8

    return VerificationReport(
        requirement=session.requirement,
        original_plan=session.planned_steps,
        actual_actions=actual_actions,
        divergence_points=divergence_points,
        files_changed=files_changed,
        unexpected_changes=unexpected_changes,
        review_hotspots=review_hotspots,
        verification_status="needs_review" if divergence_points else "likely_ok",
        confidence=confidence,
    )


def summarize_sessions(sessions: Iterable[AgentSession]) -> list[VerificationReport]:
    return [summarize_session(session) for session in sessions]

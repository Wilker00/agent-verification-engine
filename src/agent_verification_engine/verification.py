from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from difflib import SequenceMatcher
from pathlib import PurePath
from typing import Any

from .models import (
    AgentSession,
    ChangeArtifact,
    ExecutionStep,
    TestResult,
    VerificationFinding,
    VerificationReport,
)

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}
FINDING_TYPE_ORDER = {
    "policy_violation": 6,
    "unresolved_test_failure": 5,
    "failed_action": 4,
    "unexplained_change": 3,
    "recovered_test_failure": 2,
    "missing_plan_step": 1,
    "unplanned_step": 0,
}
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def session_from_dict(payload: dict[str, Any]) -> AgentSession:
    """Build a session from the plain JSON shape used by the fixtures and API."""

    steps = [
        ExecutionStep(
            index=index,
            action=step.get("action", "unknown"),
            tool=step.get("tool"),
            result_summary=step.get("result_summary"),
            success=step.get("success", True),
            file_path=step.get("file_path"),
            metadata=step.get("metadata") or {},
        )
        for index, step in enumerate(payload.get("actual_steps") or [])
    ]
    files = [
        ChangeArtifact(
            file_path=item["file_path"],
            status=item.get("status", "modified"),
            summary=item.get("summary", ""),
            risk=item.get("risk", "medium"),
        )
        for item in payload.get("files_changed") or []
    ]
    tests = [
        TestResult(
            name=item["name"],
            passed=bool(item["passed"]),
            attempt=int(item.get("attempt", 1)),
        )
        for item in payload.get("test_results") or []
    ]
    return AgentSession(
        session_id=payload["session_id"],
        requirement=payload["requirement"],
        planned_steps=list(payload.get("planned_steps") or []),
        planned_files=list(payload.get("planned_files") or []),
        actual_steps=steps,
        files_changed=files,
        test_results=tests,
    )


def _finding_from_dict(payload: dict[str, Any] | str, index: int) -> VerificationFinding:
    if isinstance(payload, str):
        return VerificationFinding(
            id=_finding_id("legacy_hotspot", payload),
            type="legacy_hotspot",
            subject=payload,
            severity="medium",
            evidence=[payload],
            reason="Imported from a report produced by an older schema.",
            review_priority=index + 1,
        )
    return VerificationFinding(
        id=payload.get("id") or _finding_id(payload.get("type", "finding"), payload.get("subject", "")),
        type=payload.get("type", "finding"),
        subject=payload.get("subject", ""),
        severity=payload.get("severity", "medium"),
        evidence=list(payload.get("evidence") or []),
        reason=payload.get("reason", ""),
        review_priority=int(payload.get("review_priority", index + 1)),
        status=payload.get("status", "open"),
    )


def report_from_dict(payload: dict[str, Any]) -> VerificationReport:
    files = [
        ChangeArtifact(
            file_path=item["file_path"],
            status=item.get("status", "modified"),
            summary=item.get("summary", ""),
            risk=item.get("risk", "medium"),
        )
        for item in payload.get("files_changed") or []
    ]
    hotspots = [
        _finding_from_dict(item, index)
        for index, item in enumerate(payload.get("review_hotspots") or [])
    ]
    return VerificationReport(
        requirement=payload.get("requirement", ""),
        original_plan=list(payload.get("original_plan") or []),
        actual_actions=list(payload.get("actual_actions") or []),
        divergence_points=list(payload.get("divergence_points") or []),
        files_changed=files,
        unexpected_changes=list(payload.get("unexpected_changes") or []),
        review_hotspots=hotspots,
        verification_checklist=dict(payload.get("verification_checklist") or {}),
        verification_status=payload.get("verification_status", "needs_review"),
    )


def report_to_dict(report: VerificationReport) -> dict[str, Any]:
    return {
        "requirement": report.requirement,
        "original_plan": report.original_plan,
        "actual_actions": report.actual_actions,
        "divergence_points": report.divergence_points,
        "files_changed": [
            {
                "file_path": change.file_path,
                "status": change.status,
                "summary": change.summary,
                "risk": change.risk,
            }
            for change in report.files_changed
        ],
        "unexpected_changes": report.unexpected_changes,
        "review_hotspots": [
            {
                "id": finding.id,
                "type": finding.type,
                "subject": finding.subject,
                "severity": finding.severity,
                "evidence": finding.evidence,
                "reason": finding.reason,
                "review_priority": finding.review_priority,
                "status": finding.status,
            }
            for finding in report.review_hotspots
        ],
        "verification_checklist": report.verification_checklist,
        "verification_status": report.verification_status,
    }


def _collected_changes(session: AgentSession) -> list[ChangeArtifact]:
    changes = list(session.files_changed)
    known = {change.file_path for change in changes}
    for step in session.actual_steps:
        if step.success and step.file_path and step.file_path not in known:
            changes.append(
                ChangeArtifact(
                    file_path=step.file_path,
                    status="modified",
                    summary=step.action,
                )
            )
            known.add(step.file_path)
    return changes


def _normalized_tokens(value: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(value.lower()))


def _step_similarity(left: str, right: str) -> float:
    left_normalized = " ".join(TOKEN_PATTERN.findall(left.lower()))
    right_normalized = " ".join(TOKEN_PATTERN.findall(right.lower()))
    if not left_normalized or not right_normalized:
        return 0.0
    left_tokens = set(left_normalized.split())
    right_tokens = set(right_normalized.split())
    token_score = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
    sequence_score = SequenceMatcher(None, left_normalized, right_normalized).ratio()
    return max(token_score, sequence_score)


def _plan_divergences(session: AgentSession) -> tuple[list[str], list[str]]:
    unmatched_actual = set(range(len(session.actual_steps)))
    missing_steps: list[str] = []
    for planned_step in session.planned_steps:
        matches = [
            (
                index,
                max(
                    _step_similarity(planned_step, session.actual_steps[index].action),
                    0.99
                    if session.actual_steps[index].metadata.get("plan_step") == planned_step
                    else 0.0,
                ),
            )
            for index in unmatched_actual
        ]
        if not matches:
            missing_steps.append(planned_step)
            continue
        best_index, score = max(matches, key=lambda item: item[1])
        if score < 0.72:
            missing_steps.append(planned_step)
            continue
        unmatched_actual.remove(best_index)

    unplanned_actions = [
        session.actual_steps[index].action
        for index in sorted(unmatched_actual)
        if not session.actual_steps[index].action.lower().startswith("retry ")
        and session.actual_steps[index].metadata.get("plan_step") not in session.planned_steps
        and not (
            session.actual_steps[index].metadata.get("source") == "openshell"
            and not session.actual_steps[index].success
        )
    ]
    return missing_steps, unplanned_actions


def _finding_id(finding_type: str, subject: str) -> str:
    digest = hashlib.blake2s(f"{finding_type}:{subject}".encode(), digest_size=5).hexdigest()
    return f"{finding_type}-{digest}"


def _finding(
    finding_type: str,
    subject: str,
    severity: str,
    evidence: list[str],
    reason: str,
) -> VerificationFinding:
    return VerificationFinding(
        id=_finding_id(finding_type, subject),
        type=finding_type,
        subject=subject,
        severity=severity,
        evidence=evidence,
        reason=reason,
    )


def _path_is_explained(session: AgentSession, file_path: str) -> bool:
    normalized_path = file_path.lower()
    if normalized_path in {path.lower() for path in session.planned_files}:
        return True
    basename = PurePath(normalized_path).name
    if normalized_path in session.requirement.lower() or basename in session.requirement.lower():
        return True
    file_actions = [
        step.action
        for step in session.actual_steps
        if step.file_path and step.file_path.lower() == normalized_path
    ]
    return any(
        _step_similarity(action, planned_step) >= 0.72
        for action in file_actions
        for planned_step in session.planned_steps
    )


def _test_findings(session: AgentSession) -> list[VerificationFinding]:
    by_name: dict[str, list[TestResult]] = {}
    for result in session.test_results:
        by_name.setdefault(result.name, []).append(result)

    findings: list[VerificationFinding] = []
    for name, results in by_name.items():
        attempts = sorted(results, key=lambda result: result.attempt)
        failed_attempts = [result.attempt for result in attempts if not result.passed]
        if not failed_attempts:
            continue
        latest = attempts[-1]
        if latest.passed:
            findings.append(
                _finding(
                    "recovered_test_failure",
                    name,
                    "medium",
                    [
                        f"Failed attempt(s): {', '.join(map(str, failed_attempts))}",
                        f"Latest attempt {latest.attempt} passed",
                    ],
                    "A test failed before passing, so the corrective change deserves targeted review.",
                )
            )
        else:
            findings.append(
                _finding(
                    "unresolved_test_failure",
                    name,
                    "critical",
                    [f"Latest attempt {latest.attempt} failed"],
                    "The latest recorded result is failing, so approval is blocked.",
                )
            )
    return findings


def _rank_findings(findings: list[VerificationFinding]) -> list[VerificationFinding]:
    findings.sort(
        key=lambda finding: (
            -SEVERITY_ORDER.get(finding.severity, 0),
            -FINDING_TYPE_ORDER.get(finding.type, 0),
            finding.subject.lower(),
        )
    )
    for priority, finding in enumerate(findings, start=1):
        finding.review_priority = priority
    return findings


def summarize_session(session: AgentSession) -> VerificationReport:
    """Turn a plain session into an evidence-backed approval judgment."""

    actual_actions = [step.action for step in session.actual_steps]
    missing_steps, unplanned_actions = _plan_divergences(session)
    divergence_points = [
        *(f"Planned step not observed in execution: {step}" for step in missing_steps),
        *(f"Unplanned step observed in execution: {action}" for action in unplanned_actions),
    ]

    findings = [
        *(
            _finding(
                "missing_plan_step",
                step,
                "medium",
                [f"Planned: {step}", "No sufficiently similar execution step was observed"],
                "A promised step appears to be missing from the recorded execution.",
            )
            for step in missing_steps
        ),
        *(
            _finding(
                "unplanned_step",
                action,
                "low",
                [f"Observed: {action}", "No sufficiently similar plan step was found"],
                "The execution included work that was not represented in the original plan.",
            )
            for action in unplanned_actions
        ),
    ]

    changes = _collected_changes(session)
    unexpected_changes: list[str] = []
    annotated: list[ChangeArtifact] = []
    for change in changes:
        explained = _path_is_explained(session, change.file_path)
        if not explained and change.file_path not in unexpected_changes:
            unexpected_changes.append(change.file_path)
            related_actions = [
                step.action
                for step in session.actual_steps
                if step.file_path == change.file_path
            ]
            findings.append(
                _finding(
                    "unexplained_change",
                    change.file_path,
                    "high",
                    [
                        "File is absent from planned_files and the requirement",
                        *(f"Associated action: {action}" for action in related_actions),
                        *( [f"Change summary: {change.summary}"] if change.summary else [] ),
                    ],
                    "The trace does not connect this changed file to the requested or planned work.",
                )
            )
        annotated.append(
            ChangeArtifact(
                file_path=change.file_path,
                status=change.status,
                summary=change.summary,
                risk="high" if not explained else change.risk,
            )
        )

    findings.extend(_test_findings(session))
    test_names = {result.name for result in session.test_results}
    for step in session.actual_steps:
        associated_tests = step.metadata.get("test_names") or [step.metadata.get("test_name")]
        if isinstance(associated_tests, str):
            associated_tests = [associated_tests]
        has_test_evidence = bool(test_names.intersection(test for test in associated_tests if test))
        if step.success or has_test_evidence or step.tool == "test" and test_names:
            continue
        if step.metadata.get("source") == "openshell":
            findings.append(
                _finding(
                    "policy_violation",
                    step.file_path or step.action,
                    "critical",
                    [
                        f"OpenShell decision: {step.metadata.get('decision', 'blocked')}",
                        step.result_summary or step.action,
                    ],
                    "The runtime safety boundary rejected this action, so approval is blocked.",
                )
            )
            continue
        findings.append(
            _finding(
                "failed_action",
                step.action,
                "high",
                [step.result_summary or "The execution step reported success=false"],
                "A failed action has no recorded recovery signal.",
            )
        )

    ranked_findings = _rank_findings(findings)
    policy_blocked = any(finding.type == "policy_violation" for finding in ranked_findings)
    tests_blocked = any(finding.type == "unresolved_test_failure" for finding in ranked_findings)
    execution_blocked = any(finding.type == "failed_action" for finding in ranked_findings)
    blocking = policy_blocked or tests_blocked or execution_blocked
    checklist = {
        "plan_alignment": "review" if missing_steps or unplanned_actions else "pass",
        "scope_alignment": "review" if unexpected_changes else "pass",
        "tests": "blocked" if tests_blocked else "pass",
        "runtime_policy": "blocked" if policy_blocked else "pass",
        "execution": "blocked" if execution_blocked else "pass",
    }

    return VerificationReport(
        requirement=session.requirement,
        original_plan=list(session.planned_steps),
        actual_actions=actual_actions,
        divergence_points=divergence_points,
        files_changed=annotated,
        unexpected_changes=unexpected_changes,
        review_hotspots=ranked_findings,
        verification_checklist=checklist,
        verification_status=(
            "blocked" if blocking else "needs_review" if ranked_findings else "likely_ok"
        ),
    )


def summarize_sessions(sessions: Iterable[AgentSession]) -> list[VerificationReport]:
    return [summarize_session(session) for session in sessions]


def review_again(previous: VerificationReport, current: VerificationReport) -> list[str]:
    """Files changed again after an earlier report, which must be reviewed again."""

    already_reviewed = {change.file_path for change in previous.files_changed}
    return [
        change.file_path
        for change in current.files_changed
        if change.file_path in already_reviewed
    ]

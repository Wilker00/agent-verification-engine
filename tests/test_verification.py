from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from agent_verification_engine.app import app
from agent_verification_engine.verification import (
    report_to_dict,
    review_again,
    session_from_dict,
    summarize_session,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
TRACE_KEYS = {
    "tokens",
    "spans",
    "gantt",
    "timing",
    "intermediate_steps",
    "workflow_output",
    "confidence",
}


def load_example(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def test_unplanned_file_is_unexplained_and_ranked_first() -> None:
    report = summarize_session(session_from_dict(load_example("unplanned-file.json")))

    assert report.unexpected_changes == ["session.py"]
    finding = report.review_hotspots[0]
    assert finding.type == "unexplained_change"
    assert finding.subject == "session.py"
    assert finding.severity == "high"
    assert finding.evidence
    assert finding.review_priority == 1
    assert any(point.startswith("Unplanned step observed") for point in report.divergence_points)
    assert "unknown" not in {change.file_path for change in report.files_changed}
    assert TRACE_KEYS.isdisjoint(report_to_dict(report))


def test_recovered_test_is_ranked_for_targeted_review() -> None:
    report = summarize_session(session_from_dict(load_example("failed-then-retried.json")))

    finding = report.review_hotspots[0]
    assert finding.type == "recovered_test_failure"
    assert finding.subject == "test_password_reset"
    assert finding.reason
    assert "login.py" not in report.unexpected_changes
    assert report.verification_checklist["tests"] == "pass"
    assert report.verification_status == "needs_review"


def test_correction_lists_overlapping_file_for_rereview() -> None:
    previous = summarize_session(session_from_dict(load_example("unplanned-file.json")))
    current = summarize_session(session_from_dict(load_example("failed-then-retried.json")))

    assert review_again(previous, current) == ["login.py"]


def test_analyze_returns_structured_judgment_and_rereview() -> None:
    previous = report_to_dict(summarize_session(session_from_dict(load_example("unplanned-file.json"))))
    payload = load_example("failed-then-retried.json")
    payload["previous_report"] = previous

    response = TestClient(app).post("/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["unexpected_changes"] == []
    assert body["review_hotspots"][0]["subject"] == "test_password_reset"
    assert body["review_hotspots"][0]["id"].startswith("recovered_test_failure-")
    assert body["review_again"] == ["login.py"]
    assert body["verification_checklist"]["scope_alignment"] == "pass"
    assert TRACE_KEYS.isdisjoint(body)


def test_similar_wording_counts_as_observed_plan_step() -> None:
    payload = {
        "session_id": "similar-plan-step",
        "requirement": "Run authentication tests",
        "planned_steps": ["Run the authentication test suite"],
        "actual_steps": [{"action": "Ran authentication test suite"}],
    }

    report = summarize_session(session_from_dict(payload))

    assert report.divergence_points == []
    assert report.review_hotspots == []
    assert report.verification_status == "likely_ok"


def test_latest_failed_test_blocks_approval() -> None:
    payload = {
        "session_id": "failed-test",
        "requirement": "Fix authentication",
        "planned_steps": ["Run auth tests"],
        "actual_steps": [{"action": "Run auth tests", "tool": "test", "success": False}],
        "test_results": [{"name": "test_auth", "passed": False, "attempt": 1}],
    }

    report = summarize_session(session_from_dict(payload))

    assert report.review_hotspots[0].type == "unresolved_test_failure"
    assert report.review_hotspots[0].severity == "critical"
    assert report.verification_checklist["tests"] == "blocked"
    assert report.verification_status == "blocked"


def test_finding_ids_are_stable() -> None:
    session = session_from_dict(load_example("unplanned-file.json"))

    first = summarize_session(session)
    second = summarize_session(session)

    assert [finding.id for finding in first.review_hotspots] == [
        finding.id for finding in second.review_hotspots
    ]

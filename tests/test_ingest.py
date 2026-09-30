from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from agent_verification_engine.app import app
from agent_verification_engine.cli import main
from agent_verification_engine.ingest import detect_trace_format, session_from_payload
from agent_verification_engine.verification import summarize_session

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def load_example(name: str):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def test_detects_supported_trace_formats() -> None:
    assert detect_trace_format(load_example("unplanned-file.json")) == "generic"
    assert detect_trace_format(load_example("nemo-workflow-output.json")) == "nemo"
    assert detect_trace_format(load_example("otel-trace.json")) == "otel"


def test_nemo_and_openshell_events_become_ranked_findings() -> None:
    session = session_from_payload(load_example("nemo-workflow-output.json"))

    report = summarize_session(session)

    assert session.session_id == "nemo-auth-review"
    assert [step.metadata["source"] for step in session.actual_steps[:3]] == ["nemo"] * 3
    assert report.review_hotspots[0].type == "policy_violation"
    assert report.review_hotspots[0].subject == ".env"
    assert report.unexpected_changes == []
    assert report.divergence_points == []
    assert report.verification_checklist["tests"] == "pass"
    assert report.verification_checklist["runtime_policy"] == "blocked"
    assert report.verification_status == "blocked"


def test_otel_trace_maps_to_clean_session() -> None:
    session = session_from_payload(load_example("otel-trace.json"))

    report = summarize_session(session)

    assert session.actual_steps[0].metadata["source"] == "otel"
    assert session.actual_steps[0].file_path == "login.py"
    assert report.review_hotspots == []
    assert report.verification_status == "likely_ok"


def test_batch_endpoint_analyzes_multiple_generic_sessions() -> None:
    payload = [
        load_example("unplanned-file.json"),
        load_example("failed-then-retried.json"),
    ]

    response = TestClient(app).post("/batch", json=payload)

    assert response.status_code == 200
    assert response.json()["count"] == 2
    assert len(response.json()["reports"]) == 2


def test_analyze_rejects_multi_session_input() -> None:
    response = TestClient(app).post("/analyze", json=load_example("nemo-workflow-output.json") * 2)

    assert response.status_code == 422
    assert "use batch analysis" in response.json()["detail"]


def test_cli_analyzes_trace_as_json(capsys) -> None:
    exit_code = main(["analyze", str(EXAMPLES / "otel-trace.json"), "--format", "json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out)["verification_status"] == "likely_ok"


def test_cli_reports_unknown_trace_shape(tmp_path: Path, capsys) -> None:
    trace_path = tmp_path / "unknown.json"
    trace_path.write_text('{"message": "not a trace"}', encoding="utf-8")

    exit_code = main(["analyze", str(trace_path)])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Unsupported trace shape" in captured.err


def test_real_session_matches_recorded_ground_truth() -> None:
    report = summarize_session(session_from_payload(load_example("real-session.json")))
    expected = load_example("real-session.expected.json")
    observed = {(finding.type, finding.subject) for finding in report.review_hotspots}

    assert {
        (finding["type"], finding["subject"])
        for finding in expected["must_find"]
    }.issubset(observed)
    assert not {
        finding.type for finding in report.review_hotspots
    }.intersection(finding["type"] for finding in expected["must_not_find"])
    assert report.divergence_points == []

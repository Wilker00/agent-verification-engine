from __future__ import annotations

from typing import Annotated, Any

from fastapi import Body, FastAPI, HTTPException, Query

from .ingest import (
    TraceFormat,
    TraceFormatError,
    session_from_payload,
    sessions_from_payload,
)
from .verification import (
    report_from_dict,
    report_to_dict,
    review_again,
    summarize_session,
)

app = FastAPI(title="Agent Verification Engine")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/formats")
def formats() -> dict[str, list[str]]:
    return {"formats": ["generic", "nemo", "otel"]}


@app.post("/analyze")
def analyze(
    payload: Annotated[Any, Body()],
    source: Annotated[TraceFormat, Query()] = "auto",
) -> dict[str, Any]:
    try:
        session = session_from_payload(payload, source)
    except (TraceFormatError, KeyError, TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    report = summarize_session(session)
    response = report_to_dict(report)
    if isinstance(payload, dict) and payload.get("previous_report") is not None:
        response["review_again"] = review_again(report_from_dict(payload["previous_report"]), report)
    return response


@app.post("/batch")
def batch(
    payload: Annotated[Any, Body()],
    source: Annotated[TraceFormat, Query()] = "auto",
) -> dict[str, Any]:
    try:
        sessions = sessions_from_payload(payload, source)
    except (TraceFormatError, KeyError, TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    reports = [report_to_dict(summarize_session(session)) for session in sessions]
    return {"count": len(reports), "reports": reports}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("agent_verification_engine.app:app", host="0.0.0.0", port=8000, reload=True)

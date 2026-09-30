from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from .models import AgentSession
from .verification import summarize_session

app = FastAPI(title="Agent Verification Engine")


class AnalyzeRequest(BaseModel):
    session_id: str
    requirement: str
    planned_steps: list[str]
    actual_steps: list[dict]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    session = AgentSession(
        session_id=request.session_id,
        requirement=request.requirement,
        planned_steps=request.planned_steps,
        actual_steps=[],
    )

    for index, step in enumerate(request.actual_steps):
        session.actual_steps.append(
            __import__("agent_verification_engine.models", fromlist=["ExecutionStep"]).ExecutionStep(
                index=index,
                action=step.get("action", "unknown"),
                tool=step.get("tool"),
                result_summary=step.get("result_summary"),
                success=step.get("success", True),
                metadata=step.get("metadata", {}),
            )
        )

    report = summarize_session(session)
    return report.__dict__


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("agent_verification_engine.app:app", host="0.0.0.0", port=8000, reload=True)

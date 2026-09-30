# Agent Verification Engine

Agent Verification Engine turns coding-agent sessions into evidence-backed review findings: what diverged from the plan, what changed without explanation, and what a human should inspect first.

## Quick start

```bash
python -m venv .venv
pip install -e ".[dev]"
pytest
agent-verify analyze examples/unplanned-file.json
agent-verify serve
```

The API starts on `http://localhost:8000`. Submit one trace to `POST /analyze` or multiple sessions to `POST /batch`. The CLI and API automatically detect generic session JSON, NeMo `workflow_output.json`, and OpenTelemetry JSON. OpenShell audit events can be attached as `openshell_events`.

Use JSON output for automation:

```bash
agent-verify analyze examples/nemo-workflow-output.json --format json
```

## Current scope

- Generic JSON session ingestion
- Plan-versus-actual findings
- Unexplained file-change findings
- Test-failure and recovery findings
- Evidence-backed, risk-ranked review order
- Re-review detection across correction runs
- NeMo, OpenTelemetry, and OpenShell-aware normalization
- Batch API and local CLI

See `PROJECT_PLAN.md` for product scope, `docs/architecture.md` for the technical design, `docs/deployment.md` for the container and Nebius path, and `docs/validation-results.md` for the first real-session evaluation.

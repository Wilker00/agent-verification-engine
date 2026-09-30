# Architecture

## Goal

Turn an autonomous coding-agent run into a compact approval artifact that tells a developer what requires review and why.

## Data flow

1. **Ingest** normalizes generic session JSON, NeMo workflow output, OTel spans, and attached OpenShell events into `AgentSession`.
2. **Reconstruction** compares planned work with observed actions, file changes, and test attempts.
3. **Verification** emits structured findings with severity, evidence, reason, review priority, and review status.
4. **Presentation** exposes the same report through the CLI and FastAPI. IDE and web interfaces are deferred.

## Core models

- `AgentSession`: requirement, planned steps and files, actual steps, changed files, and tests.
- `VerificationFinding`: one reviewable judgment with supporting evidence.
- `VerificationReport`: ordered findings plus compatibility summaries and checklist state.

## Design constraints

- Deterministic heuristics first; no uncalibrated model confidence.
- Every hotspot must explain why it exists.
- Integrations map into the core model and do not leak vendor trace formats into the report.
- The report prioritizes approval decisions rather than replaying the raw trace.
- Source adapters remain optional and do not import NeMo, OTel, or Nebius packages on the analysis path.

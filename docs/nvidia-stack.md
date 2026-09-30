# Architecture

## Goal

Turn an autonomous coding agent run into a verification artifact that a developer can trust quickly.

## Core problem

Autonomous coding agents generate lots of intermediate behavior: tool calls, file edits, shell commands, diff changes, test runs, retries, and reasoning. The true bottleneck is not only generation but the human work required to answer:

- Did the agent follow the requirement?
- What changed unexpectedly?
- Where did the plan diverge?
- Which parts of the output are high-risk and deserve review?

## Proposed architecture

### 1. Capture layer

This layer records raw execution from the agent runtime.

Relevant technologies:

- NVIDIA NeMo Agent Toolkit
- W&B Weave
- OpenTelemetry
- OpenShell runtime boundaries

Signals captured:

- requirement or goal
- action sequence
- file diffs
- tool invocations
- test results
- error traces
- retries and fallback decisions

### 2. Reconstruction layer

The raw trace is transformed into an execution timeline.

Generated objects include:

- `planned_steps`
- `actual_steps`
- `requirements_summary`
- `diff_summary`
- `unexpected_changes`
- `risk_flags`
- `review_hotspots`

### 3. Verification layer

This stage produces a concise report for a human reviewer.

Key outputs:

- plan vs actual divergence
- risk-scored file-level review hotspots
- tests and validation summary
- follow-up questions for human review
- merge confidence summary

### 4. Review UI / CLI

This may later become a web dashboard or CLI report. The initial MVP focuses on a structured terminal or API response with actionable summaries.

## Data model

The core objects are intentionally simple:

- `AgentSession`
- `ExecutionStep`
- `PlanItem`
- `ChangeArtifact`
- `VerificationReport`

## Why this aligns with NVIDIA

This project fits NVIDIA's open ecosystem because it uses the pieces that matter most for traceability, safe execution, and evidence-backed agent behavior:

- NeMo Agent Toolkit for orchestration
- OpenShell for safe runtime boundaries
- Weave / OTel for telemetry and traces
- Skills / SkillSpector for structured skill and validation layers

## Next implementation focus

Build a Python-first MVP that takes a session trace in JSON-like structure and emits a verification report with:

- requirement coverage
- expected vs actual file changes
- divergence points
- review hotspots
- estimated confidence

# NVIDIA stack for this project

This repository is designed around the NVIDIA open-source stack most relevant to autonomous coding-agent verification.

## Primary stack

### 1. NeMo Agent Toolkit

Purpose: orchestration, planning, multi-agent execution, tool use, and workflow observability.

Why it helps here:

- captures multi-step agent execution
- supports structured workflow execution
- provides a natural hook for tracing and evaluation

### 2. OpenShell

Purpose: a safe runtime boundary for autonomous agents.

Why it helps here:

- limits agent action scope
- reduces unintended side effects
- helps produce evidence-based execution auditing

### 3. W&B Weave / OpenTelemetry

Purpose: trace export and runtime observability.

Why it helps here:

- produces rich trace timelines
- captures tool calls, errors, retries, and timing
- provides a path to real-time debugging and replayability

### 4. NVIDIA Skills

Purpose: reusable capabilities for agents.

Why it helps here:

- divide agent functions into shareable, inspectable skills
- allows validation and packaging of review-related actions

### 5. SkillSpector

Purpose: detects risky agent behavior and unsafe actions.

Why it helps here:

- guards review/verification flows
- validates skill behavior before executing potentially sensitive actions

### 6. NIM / TensorRT-LLM

Purpose: optional local or hosted inference support.

Why it helps here:

- enables private or GPU-backed model serving
- useful if the project evolves into a hosted agent verification service

## Recommended project usage

For the MVP, we should use the stack in this order:

1. NeMo Agent Toolkit for orchestration
2. W&B Weave / OTel for instrumentation
3. OpenShell for secure execution boundary
4. Skills for reusable review/execution capabilities
5. NIM / TensorRT-LLM if we need managed inference

This combination supports the real problem: helping developers understand, diagnose, and verify autonomous coding work rather than just observing raw logs.

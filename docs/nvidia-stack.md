# NVIDIA Stack

NVIDIA components are inputs and deployment options, not the product itself.

## Integration points

- **NeMo Agent Toolkit:** `workflow_output.json` entries and intermediate end events map into `AgentSession`.
- **OpenShell:** attached audit events become execution steps; denied actions become blocking policy findings.
- **OpenTelemetry:** OTLP JSON spans map into execution steps. Direct Weave export remains deferred because OTel provides the shared interchange path.
- **SkillSpector:** inform risk labels only if it improves finding quality.
- **NIM / TensorRT-LLM:** optional serving path if a model-backed judgment is later justified.
- **Nebius AI Cloud:** the container is ready for Registry and Container VM deployment; provisioning remains an operator action.

The generic JSON path remains canonical. The demo must still communicate value when vendor names and raw trace viewers are removed.

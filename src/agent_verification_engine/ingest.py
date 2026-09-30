from __future__ import annotations

import json
from typing import Any, Literal

from .models import AgentSession
from .verification import session_from_dict

TraceFormat = Literal["auto", "generic", "nemo", "otel"]


class TraceFormatError(ValueError):
    pass


def detect_trace_format(payload: Any) -> str:
    if isinstance(payload, list):
        if not payload:
            raise TraceFormatError("Cannot detect the format of an empty trace list.")
        first = payload[0]
        if isinstance(first, dict) and ("intermediate_steps" in first or "question" in first):
            return "nemo"
        if isinstance(first, dict) and "session_id" in first:
            return "generic"
    if isinstance(payload, dict):
        if "resourceSpans" in payload:
            return "otel"
        if "workflow_output" in payload or "intermediate_steps" in payload:
            return "nemo"
        if "session_id" in payload and "requirement" in payload:
            return "generic"
    raise TraceFormatError("Unsupported trace shape; specify a source or provide a recognized trace.")


def sessions_from_payload(payload: Any, source: TraceFormat = "auto") -> list[AgentSession]:
    detected = detect_trace_format(payload) if source == "auto" else source
    if detected == "generic":
        items = payload if isinstance(payload, list) else [payload]
        return [session_from_dict(_attach_openshell_steps(item)) for item in items]
    if detected == "nemo":
        return [_nemo_session(item) for item in _nemo_items(payload)]
    if detected == "otel":
        if not isinstance(payload, dict):
            raise TraceFormatError("OTel input must be a JSON object.")
        return [_otel_session(payload)]
    raise TraceFormatError(f"Unsupported trace source: {detected}")


def session_from_payload(payload: Any, source: TraceFormat = "auto") -> AgentSession:
    sessions = sessions_from_payload(payload, source)
    if len(sessions) != 1:
        raise TraceFormatError(f"Expected one session but found {len(sessions)}; use batch analysis.")
    return sessions[0]


def _nemo_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and "workflow_output" in payload:
        payload = payload["workflow_output"]
    items = payload if isinstance(payload, list) else [payload]
    if not all(isinstance(item, dict) for item in items):
        raise TraceFormatError("NeMo workflow output must contain JSON objects.")
    return items


def _json_object(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _event_parts(raw_step: dict[str, Any]) -> tuple[str, str, dict[str, Any], Any]:
    payload = _json_object(raw_step.get("payload"))
    if not isinstance(payload, dict):
        payload = raw_step
    event_type = str(payload.get("event_type") or raw_step.get("type") or "STEP")
    name = str(payload.get("name") or raw_step.get("name") or event_type)
    metadata = payload.get("metadata") or raw_step.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {"raw_metadata": metadata}
    data = _json_object(payload.get("data") or raw_step.get("data") or {})
    return event_type, name, metadata, data


def _mapping_value(value: Any, *keys: str) -> Any:
    if not isinstance(value, dict):
        return None
    for key in keys:
        if value.get(key) is not None:
            return value[key]
    return None


def _event_to_step(raw_step: dict[str, Any]) -> dict[str, Any] | None:
    event_type, name, metadata, data = _event_parts(raw_step)
    if event_type.endswith("_START") or event_type in {"LLM_NEW_TOKEN", "SPAN_CHUNK"}:
        return None
    event_input = _mapping_value(data, "input", "arguments", "parameters")
    event_output = _mapping_value(data, "output", "result")
    action = metadata.get("action") or name
    if event_input and action == name:
        action = f"{name}: {_summary(event_input)}"
    status = str(metadata.get("status", "")).lower()
    success = bool(metadata.get("success", status not in {"blocked", "denied", "error", "failed"}))
    file_path = (
        metadata.get("file_path")
        or metadata.get("path")
        or _mapping_value(event_input, "file_path", "path", "filename")
    )
    return {
        "action": str(action),
        "tool": name if "TOOL" in event_type else metadata.get("tool"),
        "result_summary": _summary(event_output) if event_output is not None else None,
        "success": success,
        "file_path": str(file_path) if file_path else None,
        "metadata": {"source": "nemo", "event_type": event_type, **metadata},
    }


def _expected_step(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        _, name, metadata, data = _event_parts(value)
        return str(metadata.get("action") or _mapping_value(data, "input") or name)
    return str(value)


def _nemo_session(item: dict[str, Any]) -> AgentSession:
    actual_steps = [
        step
        for raw_step in item.get("intermediate_steps") or []
        if isinstance(raw_step, dict) and (step := _event_to_step(raw_step)) is not None
    ]
    normalized = {
        "session_id": str(item.get("session_id") or item.get("id") or "nemo-session"),
        "requirement": str(item.get("requirement") or item.get("question") or item.get("input") or ""),
        "planned_steps": list(item.get("planned_steps") or [])
        or [_expected_step(step) for step in item.get("expected_intermediate_steps") or []],
        "planned_files": list(item.get("planned_files") or []),
        "actual_steps": actual_steps,
        "files_changed": list(item.get("files_changed") or []),
        "test_results": list(item.get("test_results") or []),
        "openshell_events": list(item.get("openshell_events") or []),
    }
    return session_from_dict(_attach_openshell_steps(normalized))


def _otel_attributes(attributes: list[dict[str, Any]] | None) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for attribute in attributes or []:
        key = attribute.get("key")
        value = attribute.get("value", {})
        if not key or not isinstance(value, dict):
            continue
        parsed[key] = next(
            (item for name, item in value.items() if name.endswith("Value")),
            None,
        )
    return parsed


def _otel_session(payload: dict[str, Any]) -> AgentSession:
    spans: list[dict[str, Any]] = []
    for resource_span in payload.get("resourceSpans") or []:
        for scope_span in resource_span.get("scopeSpans") or []:
            spans.extend(scope_span.get("spans") or [])

    actual_steps: list[dict[str, Any]] = []
    discovered_requirement = payload.get("requirement")
    for span in spans:
        attributes = _otel_attributes(span.get("attributes"))
        discovered_requirement = discovered_requirement or attributes.get("agent.requirement")
        status = span.get("status") or {}
        status_code = str(status.get("code") or status.get("statusCode") or "").upper()
        actual_steps.append(
            {
                "action": str(attributes.get("agent.action") or span.get("name") or "span"),
                "tool": attributes.get("tool.name") or attributes.get("gen_ai.tool.name"),
                "result_summary": attributes.get("agent.result") or status.get("message"),
                "success": status_code not in {"STATUS_CODE_ERROR", "ERROR", "2"},
                "file_path": attributes.get("file.path") or attributes.get("code.filepath"),
                "metadata": {
                    "source": "otel",
                    "trace_id": span.get("traceId"),
                    "span_id": span.get("spanId"),
                    **attributes,
                },
            }
        )

    normalized = {
        "session_id": str(payload.get("session_id") or _first_value(spans, "traceId") or "otel-session"),
        "requirement": str(discovered_requirement or ""),
        "planned_steps": list(payload.get("planned_steps") or []),
        "planned_files": list(payload.get("planned_files") or []),
        "actual_steps": actual_steps,
        "files_changed": list(payload.get("files_changed") or []),
        "test_results": list(payload.get("test_results") or []),
        "openshell_events": list(payload.get("openshell_events") or []),
    }
    return session_from_dict(_attach_openshell_steps(normalized))


def _first_value(items: list[dict[str, Any]], key: str) -> Any:
    return next((item[key] for item in items if item.get(key)), None)


def _attach_openshell_steps(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    actual_steps = list(normalized.get("actual_steps") or [])
    for event in normalized.get("openshell_events") or []:
        if not isinstance(event, dict):
            continue
        decision = str(event.get("decision") or event.get("status") or "allowed").lower()
        subject = event.get("command") or event.get("path") or event.get("action") or "sandbox action"
        actual_steps.append(
            {
                "action": str(event.get("action") or f"OpenShell {decision}: {subject}"),
                "tool": str(event.get("tool") or event.get("kind") or "openshell"),
                "result_summary": event.get("reason"),
                "success": decision not in {"blocked", "denied", "rejected"},
                "file_path": event.get("file_path") or event.get("path"),
                "metadata": {"source": "openshell", "decision": decision, **event},
            }
        )
    normalized["actual_steps"] = actual_steps
    return normalized


def _summary(value: Any, limit: int = 240) -> str:
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, sort_keys=True, default=str)
    return text if len(text) <= limit else f"{text[: limit - 3]}..."

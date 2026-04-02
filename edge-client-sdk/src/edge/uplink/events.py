from __future__ import annotations

import uuid

from edge.context.models import (
    BatchEdgeEventsRequest,
    DeviationEvent,
    EdgeEventEnvelope,
    InterventionTrigger,
    TaskContextFrame,
    TaskNodeProgress,
    TodoNode,
)
from edge.context.runtime import utc_now_iso


def build_task_progress_event(
    session_id: str,
    node: TodoNode,
    *,
    media_object_ids: list[str] | None = None,
    observed_at: str | None = None,
    event_id: str | None = None,
) -> TaskNodeProgress:
    return TaskNodeProgress(
        event_id=event_id or f"evt_progress_{node.todo_id}",
        session_id=session_id,
        task_node_id=node.todo_id,
        title=node.title,
        module_title=node.module_title,
        module_summary=node.module_summary,
        cycle_id=node.cycle_id,
        event_kind=node.event_kind,
        status=node.status,
        expected_objects=node.expected_objects,
        matched_objects=node.matched_objects,
        missing_objects=node.missing_objects,
        start_sec=node.start_sec,
        end_sec=node.end_sec,
        duration_sec=node.duration_sec,
        match_score=node.match_score,
        hit_windows=node.hit_windows,
        evidence_frames=node.evidence_frames,
        evidence_timestamps_sec=node.evidence_timestamps_sec,
        summary_metrics=node.summary_metrics,
        media_object_ids=list(media_object_ids or node.media_object_ids),
        notes=node.notes,
        observed_at=observed_at or utc_now_iso(),
    )


def build_deviation_event(
    session_id: str,
    *,
    deviation_type: str,
    severity: str,
    summary: str,
    task_node_id: str | None = None,
    description: str = "",
    confidence: float | None = None,
    recommended_action: str = "",
    related_event_ids: list[str] | None = None,
    media_object_ids: list[str] | None = None,
    metrics: dict[str, float] | None = None,
    observed_at: str | None = None,
    event_id: str | None = None,
) -> DeviationEvent:
    return DeviationEvent(
        event_id=event_id or f"evt_deviation_{uuid.uuid4().hex[:10]}",
        session_id=session_id,
        task_node_id=task_node_id,
        deviation_type=deviation_type,
        severity=severity,
        summary=summary,
        description=description,
        confidence=confidence,
        recommended_action=recommended_action,
        related_event_ids=list(related_event_ids or []),
        media_object_ids=list(media_object_ids or []),
        metrics=dict(metrics or {}),
        observed_at=observed_at or utc_now_iso(),
    )


def build_intervention_trigger(
    session_id: str,
    *,
    reason: str,
    trigger_type: str = "manual_review",
    severity: str = "warning",
    target_scope: str = "teacher_console",
    source_event_ids: list[str] | None = None,
    acknowledgement_required: bool = True,
    created_at: str | None = None,
    trigger_id: str | None = None,
) -> InterventionTrigger:
    return InterventionTrigger(
        trigger_id=trigger_id or f"trg_{uuid.uuid4().hex[:10]}",
        session_id=session_id,
        trigger_type=trigger_type,
        reason=reason,
        severity=severity,
        target_scope=target_scope,
        source_event_ids=list(source_event_ids or []),
        acknowledgement_required=acknowledgement_required,
        created_at=created_at or utc_now_iso(),
    )


def wrap_edge_event(
    payload: TaskContextFrame | TaskNodeProgress | DeviationEvent | InterventionTrigger,
    *,
    produced_at: str | None = None,
    event_id: str | None = None,
) -> EdgeEventEnvelope:
    if isinstance(payload, TaskContextFrame):
        event_type = "task_context_frame"
        envelope_event_id = event_id or payload.frame_id
    elif isinstance(payload, TaskNodeProgress):
        event_type = "task_node_progress"
        envelope_event_id = event_id or payload.event_id
    elif isinstance(payload, DeviationEvent):
        event_type = "deviation_event"
        envelope_event_id = event_id or payload.event_id
    else:
        event_type = "intervention_trigger"
        envelope_event_id = event_id or payload.trigger_id

    return EdgeEventEnvelope(
        event_type=event_type,
        event_id=envelope_event_id,
        produced_at=produced_at or utc_now_iso(),
        payload=payload.model_dump(mode="json", exclude_none=True),
    )


def build_edge_event_batch(
    events: list[TaskContextFrame | TaskNodeProgress | DeviationEvent | InterventionTrigger | EdgeEventEnvelope],
) -> BatchEdgeEventsRequest:
    wrapped: list[EdgeEventEnvelope] = []
    for event in events:
        if isinstance(event, EdgeEventEnvelope):
            wrapped.append(event)
        else:
            wrapped.append(wrap_edge_event(event))
    return BatchEdgeEventsRequest(events=wrapped)

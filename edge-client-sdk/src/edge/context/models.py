from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


TaskStatus = Literal["completed", "partial", "missing"]
EdgeEventType = Literal[
    "task_context_frame",
    "task_node_progress",
    "deviation_event",
    "intervention_trigger",
]
DeviationType = Literal[
    "object_missing",
    "order_mismatch",
    "timeout",
    "placement_error",
    "safety_attention",
    "quality_risk",
]
DeviationSeverity = Literal["info", "warning", "critical"]
InterventionType = Literal["manual_review", "teacher_takeover", "remote_reset", "safety_pause"]
InterventionSeverity = Literal["warning", "critical"]
InterventionTargetScope = Literal["teacher_console", "edge_robot"]


class Detection(BaseModel):
    label: str
    confidence: float
    bbox: list[float] = Field(default_factory=list)


class FrameObservation(BaseModel):
    frame_index: int
    timestamp_sec: float
    detections: list[Detection] = Field(default_factory=list)
    label_counts: dict[str, int] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)


class SignalRule(BaseModel):
    metric: str
    op: Literal["gte", "lte", "between"] = "gte"
    value: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    weight: float = 1.0


class SignalObservation(BaseModel):
    frame_index: int
    timestamp_sec: float
    metrics: dict[str, float] = Field(default_factory=dict)


class TodoItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    title: str
    description: str = ""
    expected_objects: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    success_threshold: float = 0.5
    min_hits: int = 2
    min_duration_sec: float = 1.0
    search_start_sec: float | None = None
    search_end_sec: float | None = None
    fixed_start_sec: float | None = None
    fixed_end_sec: float | None = None
    pre_padding_sec: float = 1.5
    post_padding_sec: float = 1.5
    module_title: str | None = None
    module_summary: str = ""
    cycle_id: int | None = None
    event_kind: str | None = None
    signal_rules: list[SignalRule] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TodoPlan(BaseModel):
    model_config = ConfigDict(extra="allow")

    job_id: str = "unknown-job"
    title: str | None = None
    description: str = ""
    robot_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    items: list[TodoItem] = Field(default_factory=list)


class TimelineWindow(BaseModel):
    index: int
    start_sec: float
    end_sec: float
    label_counts: dict[str, int] = Field(default_factory=dict)
    dominant_objects: list[str] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)
    states: list[str] = Field(default_factory=list)
    matched_todo_ids: list[str] = Field(default_factory=list)


class TodoNode(BaseModel):
    todo_id: str
    title: str
    module_title: str | None = None
    module_summary: str = ""
    cycle_id: int | None = None
    event_kind: str | None = None
    status: TaskStatus
    expected_objects: list[str] = Field(default_factory=list)
    matched_objects: list[str] = Field(default_factory=list)
    missing_objects: list[str] = Field(default_factory=list)
    start_sec: float | None = None
    end_sec: float | None = None
    duration_sec: float = 0.0
    match_score: float = 0.0
    hit_windows: int = 0
    evidence_frames: list[int] = Field(default_factory=list)
    evidence_timestamps_sec: list[float] = Field(default_factory=list)
    summary_metrics: dict[str, float] = Field(default_factory=dict)
    media_object_ids: list[str] = Field(default_factory=list)
    notes: str = ""


class LiveMonitorConfig(BaseModel):
    expected_left_part_count: int = 1
    expected_right_part_count: int = 1
    left_zone_ratio: float = 0.4
    part_labels: list[str] = Field(default_factory=lambda: ["part", "component", "cylinder", "bottle"])
    use_color_fallback: bool = True
    yellow_h_min: int = 15
    yellow_h_max: int = 45
    yellow_s_min: int = 50
    yellow_v_min: int = 60
    contour_min_area_ratio: float = 0.00025


class TaskContextFrame(BaseModel):
    frame_id: str
    session_id: str
    site_id: str
    robot_id: str
    stream_id: str | None = None
    timestamp: str
    frame_index: int
    state: str
    message: str = ""
    progress: float
    current_task_node_id: str | None = None
    current_task_node_title: str | None = None
    next_task_node_id: str | None = None
    next_task_node_title: str | None = None
    task_status: TaskStatus | None = None
    metrics: dict[str, float] = Field(default_factory=dict)
    media_object_ids: list[str] = Field(default_factory=list)


class TaskNodeProgress(BaseModel):
    event_id: str
    session_id: str
    task_node_id: str
    title: str
    module_title: str | None = None
    module_summary: str = ""
    cycle_id: int | None = None
    event_kind: str | None = None
    status: TaskStatus
    expected_objects: list[str] = Field(default_factory=list)
    matched_objects: list[str] = Field(default_factory=list)
    missing_objects: list[str] = Field(default_factory=list)
    start_sec: float | None = None
    end_sec: float | None = None
    duration_sec: float = 0.0
    match_score: float = 0.0
    hit_windows: int = 0
    evidence_frames: list[int] = Field(default_factory=list)
    evidence_timestamps_sec: list[float] = Field(default_factory=list)
    summary_metrics: dict[str, float] = Field(default_factory=dict)
    media_object_ids: list[str] = Field(default_factory=list)
    notes: str = ""
    observed_at: str


class DeviationEvent(BaseModel):
    event_id: str
    session_id: str
    task_node_id: str | None = None
    deviation_type: DeviationType
    severity: DeviationSeverity
    summary: str
    description: str = ""
    confidence: float | None = None
    recommended_action: str = ""
    related_event_ids: list[str] = Field(default_factory=list)
    media_object_ids: list[str] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)
    observed_at: str


class InterventionTrigger(BaseModel):
    trigger_id: str
    session_id: str
    trigger_type: InterventionType
    reason: str
    severity: InterventionSeverity
    target_scope: InterventionTargetScope = "teacher_console"
    source_event_ids: list[str] = Field(default_factory=list)
    acknowledgement_required: bool = True
    created_at: str


class EdgeEventEnvelope(BaseModel):
    event_type: EdgeEventType
    event_id: str
    produced_at: str
    payload: dict[str, Any]


class BatchEdgeEventsRequest(BaseModel):
    events: list[EdgeEventEnvelope] = Field(default_factory=list)


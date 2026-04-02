from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


SessionStatus = Literal["planned", "active", "completed", "failed", "cancelled"]
TaskStatus = Literal["completed", "partial", "missing"]
EdgeEventType = Literal[
    "task_context_frame",
    "task_node_progress",
    "deviation_event",
    "intervention_trigger",
]
ArmCommandKind = Literal[
    "execute_action",
    "set_joint_position",
    "set_claw_motion",
    "set_joint_enable",
    "heartbeat_ping",
    "system_reset",
]
ArmActionName = Literal["reset", "extend", "contract", "place", "custom"]
ArmJointName = Literal["joint_1", "joint_2", "joint_3", "joint_4", "joint_5", "joint_6", "all"]
ArmPositionUnit = Literal["rad", "cm"]
ArmPacketStatus = Literal["ready", "consumed", "expired"]
ArmPacketDirection = Literal["read", "write"]
ArmPacketProtocol = Literal["talon_usb_uart_v1"]


class SessionRecord(BaseModel):
    session_id: str
    site_id: str
    robot_id: str
    status: SessionStatus
    title: str = ""
    objective: str = ""
    sop_plan_id: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    created_at: str
    updated_at: str
    tags: list[str] = Field(default_factory=list)


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
    deviation_type: str
    severity: Literal["info", "warning", "critical"]
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
    trigger_type: str
    reason: str
    severity: Literal["warning", "critical"]
    target_scope: Literal["teacher_console", "edge_robot"] = "teacher_console"
    source_event_ids: list[str] = Field(default_factory=list)
    acknowledgement_required: bool = True
    created_at: str


class RobotParameterInput(BaseModel):
    command_kind: ArmCommandKind
    operator_id: str
    reason: str
    source_event_ids: list[str] = Field(default_factory=list)
    expires_at: str | None = None
    action_name: ArmActionName | None = None
    joint_name: ArmJointName | None = None
    position_value: float | None = None
    position_unit: ArmPositionUnit | None = None
    claw_x: float | None = None
    claw_y: float | None = None
    claw_unit: Literal["rad"] | None = None
    enabled: bool | None = None

    @model_validator(mode="after")
    def validate_command_shape(self) -> "RobotParameterInput":
        if self.command_kind == "execute_action":
            if self.action_name is None:
                raise ValueError("action_name is required when command_kind=execute_action")
        elif self.command_kind == "set_joint_position":
            if self.joint_name is None or self.position_value is None:
                raise ValueError("joint_name and position_value are required when command_kind=set_joint_position")
            if self.joint_name == "all":
                raise ValueError("joint_name=all is not supported when command_kind=set_joint_position")
            if self.position_unit is None:
                self.position_unit = "cm" if self.joint_name == "joint_6" else "rad"
            expected_unit: ArmPositionUnit = "cm" if self.joint_name == "joint_6" else "rad"
            if self.position_unit != expected_unit:
                raise ValueError(
                    f"position_unit must be {expected_unit} when command_kind=set_joint_position and joint_name={self.joint_name}"
                )
            if self.joint_name == "joint_6":
                if not 0.0 <= self.position_value <= 10.0:
                    raise ValueError("joint_6 position_value must be within [0, 10] cm")
            elif not -2 * math.pi <= self.position_value <= 2 * math.pi:
                raise ValueError("joint_1 to joint_5 position_value must be within [-2π, 2π] rad")
        elif self.command_kind == "set_claw_motion":
            if self.claw_x is None or self.claw_y is None:
                raise ValueError("claw_x and claw_y are required when command_kind=set_claw_motion")
            if self.claw_unit is None:
                self.claw_unit = "rad"
            if self.claw_unit != "rad":
                raise ValueError("claw_unit must be rad when command_kind=set_claw_motion")
        elif self.command_kind == "set_joint_enable":
            if self.joint_name is None or self.enabled is None:
                raise ValueError("joint_name and enabled are required when command_kind=set_joint_enable")
        elif self.command_kind in {"heartbeat_ping", "system_reset"}:
            return self
        return self


class ArmCommandPacket(BaseModel):
    packet_id: str
    session_id: str
    site_id: str
    robot_id: str
    status: ArmPacketStatus = "ready"
    command_kind: ArmCommandKind
    protocol: ArmPacketProtocol = "talon_usb_uart_v1"
    packet_head: int
    base_address: int
    wire_address: int
    rw: ArmPacketDirection = "write"
    frame_len: int
    data_bytes: list[int] = Field(default_factory=list)
    checksum: int
    frame_bytes: list[int] = Field(default_factory=list)
    frame_hex: str
    target_topic: str
    expected_feedback: str | None = None
    suggested_send_interval_ms: int | None = None
    created_at: str
    expires_at: str | None = None
    input: RobotParameterInput

    @model_validator(mode="after")
    def validate_packet(self) -> "ArmCommandPacket":
        if len(self.frame_bytes) != self.frame_len:
            raise ValueError("frame_len must match the number of frame_bytes")
        if not self.frame_bytes:
            raise ValueError("frame_bytes must not be empty")
        if self.frame_bytes[0] != self.packet_head:
            raise ValueError("packet_head must match the first frame byte")
        if self.frame_bytes[-1] != self.checksum:
            raise ValueError("checksum must match the last frame byte")
        return self


class EdgeEventEnvelope(BaseModel):
    event_type: EdgeEventType
    event_id: str
    produced_at: str
    payload: dict[str, Any]


class BatchEdgeEventsAcceptedResponse(BaseModel):
    session_id: str
    accepted_count: int
    rejected_count: int
    received_at: str
    rejected_event_ids: list[str] = Field(default_factory=list)


class SessionSummary(BaseModel):
    session: SessionRecord
    latest_frame: TaskContextFrame | None = None
    latest_progress: TaskNodeProgress | None = None
    latest_deviation: DeviationEvent | None = None
    latest_intervention: InterventionTrigger | None = None
    last_received_at: str | None = None
    total_events: int = 0


class SessionStreamSnapshot(BaseModel):
    session: SessionRecord
    latest_frame: TaskContextFrame | None = None
    latest_progress: TaskNodeProgress | None = None
    latest_deviation: DeviationEvent | None = None
    latest_intervention: InterventionTrigger | None = None
    event_counts: dict[str, int] = Field(default_factory=dict)
    recent_events: list[EdgeEventEnvelope] = Field(default_factory=list)
    last_received_at: str | None = None

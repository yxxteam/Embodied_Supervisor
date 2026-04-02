from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from data.models import ArmCommandKind, EdgeEventEnvelope, RobotParameterInput


class SessionCreateRequest(BaseModel):
    site_id: str
    robot_id: str
    title: str = ""
    objective: str = ""
    sop_plan_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class BatchEdgeEventsRequest(BaseModel):
    events: list[EdgeEventEnvelope] = Field(default_factory=list)


class RobotParameterInputRequest(RobotParameterInput):
    pass


RobotParameterFieldType = Literal["enum", "number", "boolean"]


class RobotParameterOption(BaseModel):
    value: str | bool
    label: str
    description: str = ""


class RobotParameterFieldSpec(BaseModel):
    name: str
    label: str
    type: RobotParameterFieldType
    required: bool = True
    description: str = ""
    unit: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    default: str | float | bool | None = None
    options: list[RobotParameterOption] = Field(default_factory=list)


class RobotParameterCommandSpec(BaseModel):
    command_kind: ArmCommandKind
    label: str
    description: str
    base_address: int
    base_address_hex: str
    frame_len: int
    rw: Literal["write"]
    expected_feedback: str | None = None
    suggested_send_interval_ms: int | None = None
    docs_refs: list[str] = Field(default_factory=list)
    input_fields: list[RobotParameterFieldSpec] = Field(default_factory=list)
    example_request: RobotParameterInputRequest


class RobotParameterInputCatalogResponse(BaseModel):
    session_id: str
    site_id: str
    robot_id: str
    protocol: str
    packet_head: int
    packet_head_hex: str
    baud_rate: int
    address_rw_rule: str
    frame_len_rule: str
    target_topic: str
    docs_refs: list[str] = Field(default_factory=list)
    supported_commands: list[RobotParameterCommandSpec] = Field(default_factory=list)


class ServiceError(BaseModel):
    detail: str
    context: dict[str, Any] = Field(default_factory=dict)

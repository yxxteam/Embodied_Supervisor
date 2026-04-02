from __future__ import annotations

import struct
import uuid

from data.models import ArmCommandPacket, RobotParameterInput, SessionRecord

from api.schemas import (
    RobotParameterCommandSpec,
    RobotParameterFieldSpec,
    RobotParameterInputCatalogResponse,
    RobotParameterInputRequest,
    RobotParameterOption,
)
from api.service import utc_now_iso


TALON_PACKET_HEAD = 0x42
TALON_BAUD_RATE = 115200
TALON_PROTOCOL = "talon_usb_uart_v1"

PROTOCOL_DOC_REF = "docs/[Talon] 六轴协作机械臂-通信协议_01.png"
TUTORIAL_DOC_REF = "docs/CRAIC-百度智能云智能服务机器人赛-机械臂调节教程.pdf 第11-14页"

TALON_BASE_ADDRESSES = {
    "execute_action": 0x09,
    "set_joint_position": 0x03,
    "set_claw_motion": 0x0A,
    "set_joint_enable": 0x07,
    "heartbeat_ping": 55,
    "system_reset": 66,
}
TALON_ACTION_CODES = {
    "reset": 0x01,
    "extend": 0x02,
    "contract": 0x03,
    "place": 0x04,
    "custom": 0x05,
}
TALON_JOINT_CODES = {
    "joint_1": 0x01,
    "joint_2": 0x02,
    "joint_3": 0x03,
    "joint_4": 0x04,
    "joint_5": 0x05,
    "joint_6": 0x06,
    "all": 0x07,
}
EXPECTED_FEEDBACK = {
    "execute_action": "action_complete_signal",
    "set_joint_position": None,
    "set_claw_motion": None,
    "set_joint_enable": None,
    "heartbeat_ping": "heartbeat_response_signal",
    "system_reset": None,
}
SUGGESTED_SEND_INTERVAL_MS = {
    "execute_action": None,
    "set_joint_position": None,
    "set_claw_motion": None,
    "set_joint_enable": None,
    "heartbeat_ping": 300,
    "system_reset": None,
}


def _float_bytes(value: float) -> list[int]:
    return list(struct.pack("<f", float(value)))


def _build_data_bytes(input_payload: RobotParameterInput) -> list[int]:
    if input_payload.command_kind == "execute_action":
        return [TALON_ACTION_CODES[input_payload.action_name or "custom"]]
    if input_payload.command_kind == "set_joint_position":
        return [
            TALON_JOINT_CODES[input_payload.joint_name or "joint_1"],
            *_float_bytes(input_payload.position_value or 0.0),
        ]
    if input_payload.command_kind == "set_claw_motion":
        return [*_float_bytes(input_payload.claw_x or 0.0), *_float_bytes(input_payload.claw_y or 0.0)]
    if input_payload.command_kind == "set_joint_enable":
        return [TALON_JOINT_CODES[input_payload.joint_name or "joint_1"], 1 if input_payload.enabled else 0]
    if input_payload.command_kind in {"heartbeat_ping", "system_reset"}:
        return []
    raise ValueError(f"unsupported command_kind: {input_payload.command_kind}")


def _example_execute_action() -> RobotParameterInputRequest:
    return RobotParameterInputRequest(
        command_kind="execute_action",
        operator_id="teacher-console-01",
        reason="Cycle 1 final placement failed and the arm should return to reset pose.",
        source_event_ids=["evt_deviation_cycle1_final_place"],
        action_name="reset",
    )


def _example_joint_position() -> RobotParameterInputRequest:
    return RobotParameterInputRequest(
        command_kind="set_joint_position",
        operator_id="teacher-console-01",
        reason="Open the claw before the next pickup attempt.",
        joint_name="joint_6",
        position_value=9.0,
        position_unit="cm",
    )


def _example_claw_motion() -> RobotParameterInputRequest:
    return RobotParameterInputRequest(
        command_kind="set_claw_motion",
        operator_id="teacher-console-01",
        reason="Lift the claw slightly after a successful grasp.",
        claw_x=-0.2,
        claw_y=0.3,
        claw_unit="rad",
    )


def _example_joint_enable() -> RobotParameterInputRequest:
    return RobotParameterInputRequest(
        command_kind="set_joint_enable",
        operator_id="teacher-console-01",
        reason="Re-enable the arm joints after manual teaching mode.",
        joint_name="all",
        enabled=True,
    )


def _example_heartbeat() -> RobotParameterInputRequest:
    return RobotParameterInputRequest(
        command_kind="heartbeat_ping",
        operator_id="edge-bridge-01",
        reason="Keep the Talon controller alive during task execution.",
    )


def _example_system_reset() -> RobotParameterInputRequest:
    return RobotParameterInputRequest(
        command_kind="system_reset",
        operator_id="teacher-console-01",
        reason="Force a full robot reboot after repeated communication failures.",
    )


def build_robot_parameter_input_catalog(session: SessionRecord) -> RobotParameterInputCatalogResponse:
    target_topic = f"embodied/{session.site_id}/{session.robot_id}/command"
    return RobotParameterInputCatalogResponse(
        session_id=session.session_id,
        site_id=session.site_id,
        robot_id=session.robot_id,
        protocol=TALON_PROTOCOL,
        packet_head=TALON_PACKET_HEAD,
        packet_head_hex=f"0x{TALON_PACKET_HEAD:02X}",
        baud_rate=TALON_BAUD_RATE,
        address_rw_rule="Addr 的 bit7 区分读写；当前接口生成写帧，wire_address=base_address。",
        frame_len_rule="len = head + addr + len + data + check，对应协议图 PS2。",
        target_topic=target_topic,
        docs_refs=[PROTOCOL_DOC_REF, TUTORIAL_DOC_REF],
        supported_commands=[
            RobotParameterCommandSpec(
                command_kind="execute_action",
                label="动作库执行",
                description="执行复位、伸展、收缩、放置、自定义动作，对应教程第 11-12 页的 setActions(Action action)。",
                base_address=TALON_BASE_ADDRESSES["execute_action"],
                base_address_hex=f"0x{TALON_BASE_ADDRESSES['execute_action']:02X}",
                frame_len=5,
                rw="write",
                expected_feedback=EXPECTED_FEEDBACK["execute_action"],
                docs_refs=[
                    f"{PROTOCOL_DOC_REF} 执行动作/地址9/备注执行结果反馈结束信号",
                    f"{TUTORIAL_DOC_REF} 6.1 动作库执行",
                ],
                input_fields=[
                    RobotParameterFieldSpec(
                        name="action_name",
                        label="动作类型",
                        type="enum",
                        description="动作库中的预定义动作。协议写入值为 1-5；教程代码中的枚举值为 0-4，写帧时会自动 +1。",
                        options=[
                            RobotParameterOption(value="reset", label="reset / 复位"),
                            RobotParameterOption(value="extend", label="extend / 伸展"),
                            RobotParameterOption(value="contract", label="contract / 收缩"),
                            RobotParameterOption(value="place", label="place / 放置"),
                            RobotParameterOption(value="custom", label="custom / 自定义"),
                        ],
                        default="reset",
                    ),
                ],
                example_request=_example_execute_action(),
            ),
            RobotParameterCommandSpec(
                command_kind="set_joint_position",
                label="单关节控制",
                description="控制关节 1-5 的角度或关节 6 的夹爪开合位置，对应教程第 12-13 页的 setJointPosition(ArmJoint joint, float position)。",
                base_address=TALON_BASE_ADDRESSES["set_joint_position"],
                base_address_hex=f"0x{TALON_BASE_ADDRESSES['set_joint_position']:02X}",
                frame_len=9,
                rw="write",
                docs_refs=[
                    f"{PROTOCOL_DOC_REF} 单关节控制/地址3",
                    f"{TUTORIAL_DOC_REF} 6.2 单关节控制",
                ],
                input_fields=[
                    RobotParameterFieldSpec(
                        name="joint_name",
                        label="关节编号",
                        type="enum",
                        options=[
                            RobotParameterOption(value="joint_1", label="joint_1 / 关节1"),
                            RobotParameterOption(value="joint_2", label="joint_2 / 关节2"),
                            RobotParameterOption(value="joint_3", label="joint_3 / 关节3"),
                            RobotParameterOption(value="joint_4", label="joint_4 / 关节4"),
                            RobotParameterOption(value="joint_5", label="joint_5 / 关节5"),
                            RobotParameterOption(value="joint_6", label="joint_6 / 夹爪位置"),
                        ],
                    ),
                    RobotParameterFieldSpec(
                        name="position_value",
                        label="目标值",
                        type="number",
                        description="joint_1 到 joint_5 使用 rad；joint_6 使用 cm。",
                    ),
                    RobotParameterFieldSpec(
                        name="position_unit",
                        label="单位",
                        type="enum",
                        description="joint_1 到 joint_5 仅支持 rad；joint_6 仅支持 cm。",
                        options=[
                            RobotParameterOption(value="rad", label="rad"),
                            RobotParameterOption(value="cm", label="cm"),
                        ],
                    ),
                ],
                example_request=_example_joint_position(),
            ),
            RobotParameterCommandSpec(
                command_kind="set_claw_motion",
                label="机械爪运动控制",
                description="控制机械爪 X/Y 方向角度，对应教程第 13-14 页的 setClawMotion(float x, float y)。",
                base_address=TALON_BASE_ADDRESSES["set_claw_motion"],
                base_address_hex=f"0x{TALON_BASE_ADDRESSES['set_claw_motion']:02X}",
                frame_len=12,
                rw="write",
                docs_refs=[
                    f"{PROTOCOL_DOC_REF} 夹爪控制/地址10",
                    f"{TUTORIAL_DOC_REF} 6.3 机械爪运动控制",
                ],
                input_fields=[
                    RobotParameterFieldSpec(
                        name="claw_x",
                        label="X 方向角度",
                        type="number",
                        unit="rad",
                    ),
                    RobotParameterFieldSpec(
                        name="claw_y",
                        label="Y 方向角度",
                        type="number",
                        unit="rad",
                    ),
                    RobotParameterFieldSpec(
                        name="claw_unit",
                        label="单位",
                        type="enum",
                        options=[RobotParameterOption(value="rad", label="rad")],
                        default="rad",
                    ),
                ],
                example_request=_example_claw_motion(),
            ),
            RobotParameterCommandSpec(
                command_kind="set_joint_enable",
                label="关节使能",
                description="控制单关节或全部关节的使能状态，对应协议图里的关节使能/地址7。",
                base_address=TALON_BASE_ADDRESSES["set_joint_enable"],
                base_address_hex=f"0x{TALON_BASE_ADDRESSES['set_joint_enable']:02X}",
                frame_len=6,
                rw="write",
                docs_refs=[f"{PROTOCOL_DOC_REF} 关节使能/地址7"],
                input_fields=[
                    RobotParameterFieldSpec(
                        name="joint_name",
                        label="关节编号",
                        type="enum",
                        options=[
                            RobotParameterOption(value="joint_1", label="joint_1 / 关节1"),
                            RobotParameterOption(value="joint_2", label="joint_2 / 关节2"),
                            RobotParameterOption(value="joint_3", label="joint_3 / 关节3"),
                            RobotParameterOption(value="joint_4", label="joint_4 / 关节4"),
                            RobotParameterOption(value="joint_5", label="joint_5 / 关节5"),
                            RobotParameterOption(value="joint_6", label="joint_6 / 夹爪"),
                            RobotParameterOption(value="all", label="all / 所有关节"),
                        ],
                    ),
                    RobotParameterFieldSpec(
                        name="enabled",
                        label="是否使能",
                        type="boolean",
                        options=[
                            RobotParameterOption(value=True, label="true / 使能"),
                            RobotParameterOption(value=False, label="false / 失能"),
                        ],
                        default=True,
                    ),
                ],
                example_request=_example_joint_enable(),
            ),
            RobotParameterCommandSpec(
                command_kind="heartbeat_ping",
                label="心跳信号",
                description="无数据体写帧；协议图要求约 300ms 发送一次，用于维持通信状态。",
                base_address=TALON_BASE_ADDRESSES["heartbeat_ping"],
                base_address_hex=f"0x{TALON_BASE_ADDRESSES['heartbeat_ping']:02X}",
                frame_len=4,
                rw="write",
                expected_feedback=EXPECTED_FEEDBACK["heartbeat_ping"],
                suggested_send_interval_ms=SUGGESTED_SEND_INTERVAL_MS["heartbeat_ping"],
                docs_refs=[f"{PROTOCOL_DOC_REF} 心跳信号/地址55-56"],
                input_fields=[],
                example_request=_example_heartbeat(),
            ),
            RobotParameterCommandSpec(
                command_kind="system_reset",
                label="系统复位",
                description="无数据体写帧，对应协议图的系统复位/地址66。",
                base_address=TALON_BASE_ADDRESSES["system_reset"],
                base_address_hex=f"0x{TALON_BASE_ADDRESSES['system_reset']:02X}",
                frame_len=4,
                rw="write",
                docs_refs=[f"{PROTOCOL_DOC_REF} 系统复位/地址66"],
                input_fields=[],
                example_request=_example_system_reset(),
            ),
        ],
    )


def build_arm_command_packet(
    session: SessionRecord,
    input_payload: RobotParameterInput,
) -> ArmCommandPacket:
    data_bytes = _build_data_bytes(input_payload)
    base_address = TALON_BASE_ADDRESSES[input_payload.command_kind]
    frame_len = 4 + len(data_bytes)
    frame_prefix = [TALON_PACKET_HEAD, base_address, frame_len, *data_bytes]
    checksum = sum(frame_prefix) & 0xFF
    frame_bytes = [*frame_prefix, checksum]
    created_at = utc_now_iso()

    return ArmCommandPacket(
        packet_id=f"pkt_{uuid.uuid4().hex[:12]}",
        session_id=session.session_id,
        site_id=session.site_id,
        robot_id=session.robot_id,
        status="ready",
        command_kind=input_payload.command_kind,
        protocol=TALON_PROTOCOL,
        packet_head=TALON_PACKET_HEAD,
        base_address=base_address,
        wire_address=base_address,
        rw="write",
        frame_len=frame_len,
        data_bytes=data_bytes,
        checksum=checksum,
        frame_bytes=frame_bytes,
        frame_hex=" ".join(f"{byte:02X}" for byte in frame_bytes),
        target_topic=f"embodied/{session.site_id}/{session.robot_id}/command",
        expected_feedback=EXPECTED_FEEDBACK[input_payload.command_kind],
        suggested_send_interval_ms=SUGGESTED_SEND_INTERVAL_MS[input_payload.command_kind],
        created_at=created_at,
        expires_at=input_payload.expires_at,
        input=input_payload,
    )

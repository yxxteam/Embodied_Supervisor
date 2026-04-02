from data.cache.session_stream_cache import LocalSessionStreamCache
from data.models import ArmCommandPacket, EdgeEventEnvelope, RobotParameterInput, SessionRecord
from data.postgres.local_repositories import LocalArmCommandRepository, LocalEventRepository, LocalSessionRepository


def make_session() -> SessionRecord:
    return SessionRecord(
        session_id="sess_demo_001",
        site_id="lab-a",
        robot_id="dual-arm-station-01",
        status="active",
        title="Demo",
        objective="Verify ingest flow.",
        sop_plan_id="sop_demo_v1",
        started_at="2026-03-28T09:00:00Z",
        created_at="2026-03-28T08:59:00Z",
        updated_at="2026-03-28T09:00:00Z",
        tags=["demo"],
    )


def test_local_repositories_persist_session_and_stream_snapshot(tmp_path) -> None:
    session_repo = LocalSessionRepository(tmp_path)
    stream_cache = LocalSessionStreamCache(tmp_path)
    event_repo = LocalEventRepository(tmp_path, stream_cache=stream_cache)

    session = session_repo.create(make_session())
    assert session_repo.get(session.session_id) is not None

    response = event_repo.append_events(
        session,
        [
            EdgeEventEnvelope(
                event_type="task_context_frame",
                event_id="evt_ctx_001",
                produced_at="2026-03-28T09:01:00Z",
                payload={
                    "frame_id": "frame_001",
                    "session_id": session.session_id,
                    "site_id": session.site_id,
                    "robot_id": session.robot_id,
                    "timestamp": "2026-03-28T09:01:00Z",
                    "frame_index": 12,
                    "state": "02 Align",
                    "message": "Alignment in progress.",
                    "progress": 0.42,
                    "current_task_node_id": "align_1",
                    "current_task_node_title": "02 Align",
                    "next_task_node_id": "place_1",
                    "next_task_node_title": "03 Place",
                    "task_status": "partial",
                    "metrics": {"motion_norm": 0.38},
                    "media_object_ids": ["media_frame_001"],
                },
            ),
            EdgeEventEnvelope(
                event_type="deviation_event",
                event_id="evt_dev_001",
                produced_at="2026-03-28T09:01:10Z",
                payload={
                    "event_id": "evt_dev_001",
                    "session_id": session.session_id,
                    "task_node_id": "place_1",
                    "deviation_type": "placement_error",
                    "severity": "warning",
                    "summary": "Final placement drifted.",
                    "description": "The part is still on the left side.",
                    "recommended_action": "Pause and reset.",
                    "metrics": {"left_count": 2, "right_count": 0},
                    "observed_at": "2026-03-28T09:01:10Z",
                },
            ),
        ],
        received_at="2026-03-28T09:01:11Z",
    )

    assert response.accepted_count == 2
    snapshot = event_repo.get_stream(session)
    assert snapshot.latest_frame is not None
    assert snapshot.latest_frame.state == "02 Align"
    assert snapshot.latest_deviation is not None
    assert snapshot.latest_deviation.deviation_type == "placement_error"
    assert snapshot.event_counts["task_context_frame"] == 1
    assert snapshot.event_counts["deviation_event"] == 1


def test_session_repository_lists_latest_first(tmp_path) -> None:
    session_repo = LocalSessionRepository(tmp_path)
    first = make_session()
    second = make_session().model_copy(
        update={
            "session_id": "sess_demo_002",
            "created_at": "2026-03-28T09:10:00Z",
            "updated_at": "2026-03-28T09:10:00Z",
        }
    )
    session_repo.create(first)
    session_repo.create(second)

    sessions = session_repo.list()
    assert [session.session_id for session in sessions] == ["sess_demo_002", "sess_demo_001"]


def test_robot_command_repository_persists_latest_packet(tmp_path) -> None:
    repo = LocalArmCommandRepository(tmp_path)
    packet = ArmCommandPacket(
        packet_id="pkt_demo_001",
        session_id="sess_demo_001",
        site_id="lab-a",
        robot_id="dual-arm-station-01",
        status="ready",
        command_kind="execute_action",
        protocol="talon_usb_uart_v1",
        packet_head=0x42,
        base_address=0x09,
        wire_address=0x09,
        rw="write",
        frame_len=5,
        data_bytes=[0x01],
        checksum=0x51,
        frame_bytes=[0x42, 0x09, 0x05, 0x01, 0x51],
        frame_hex="42 09 05 01 51",
        target_topic="embodied/lab-a/dual-arm-station-01/command",
        expected_feedback="action_complete_signal",
        created_at="2026-04-02T10:20:00Z",
        input=RobotParameterInput(
            command_kind="execute_action",
            operator_id="teacher-console-01",
            reason="Reset the robot before retrying.",
            action_name="reset",
        ),
    )

    repo.create(packet)
    latest = repo.get_latest(packet.session_id)

    assert latest is not None
    assert latest.packet_id == packet.packet_id
    assert latest.frame_bytes[-1] == latest.checksum

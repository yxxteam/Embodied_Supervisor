import json
from pathlib import Path

from edge.context.models import TodoNode
from edge.context.runtime import build_task_context_frame
from edge.uplink.events import (
    build_deviation_event,
    build_edge_event_batch,
    build_intervention_trigger,
    build_task_progress_event,
)


def test_uplink_batch_matches_contract_shape() -> None:
    session_id = "sess_20260327_001"
    node = TodoNode(
        todo_id="cycle1_align_part_a",
        title="Cycle 1 Align Part A",
        module_title="02 Cycle 1 Align Part A",
        module_summary="The arm pair moves the part into the center alignment zone.",
        cycle_id=1,
        event_kind="align",
        status="completed",
        expected_objects=["part_a", "fixture_a"],
        matched_objects=["part_a", "fixture_a"],
        start_sec=36.0,
        end_sec=43.0,
        duration_sec=7.0,
        match_score=0.91,
        hit_windows=7,
        evidence_frames=[1894, 1912, 1940],
        evidence_timestamps_sec=[36.2, 38.0, 41.5],
        summary_metrics={"motion_norm": 0.41, "center_focus": 0.84},
    )

    frame = build_task_context_frame(
        timestamp_sec=42.0,
        frame_index=1842,
        duration_sec=100.0,
        nodes=[node],
        metrics={"motion_norm": 0.38, "center_focus": 0.81},
        session_id=session_id,
        site_id="lab-a",
        robot_id="dual-arm-station-01",
        stream_id="camera-top",
        observed_at="2026-03-27T09:30:15Z",
        media_object_ids=["media_frame_001"],
    )
    progress = build_task_progress_event(
        session_id,
        node,
        media_object_ids=["media_clip_cycle1_align_part_a"],
        observed_at="2026-03-27T09:31:10Z",
        event_id="evt_progress_cycle1_align_part_a",
    )
    deviation = build_deviation_event(
        session_id,
        task_node_id="cycle1_final_placement",
        deviation_type="placement_error",
        severity="warning",
        summary="Final placement failed the left-right validation rule.",
        description="Both finished parts remained on the left side after the final placement step.",
        confidence=0.94,
        recommended_action="Replay the final segment and issue a reset before the next cycle.",
        related_event_ids=["evt_progress_cycle1_align_part_a"],
        media_object_ids=["media_frame_failure_001", "media_clip_placement_failure"],
        metrics={"left_count": 2, "right_count": 0, "motion_norm": 0.08},
        observed_at="2026-03-27T09:35:41Z",
        event_id="evt_deviation_cycle1_final_place",
    )
    trigger = build_intervention_trigger(
        session_id,
        reason="Final placement deviation repeated and requires a clean reset before continuing.",
        trigger_type="remote_reset",
        severity="warning",
        target_scope="edge_robot",
        source_event_ids=["evt_deviation_cycle1_final_place"],
        created_at="2026-03-27T09:36:12Z",
        trigger_id="trg_remote_reset_cycle1_001",
    )

    batch = build_edge_event_batch([frame, progress, deviation, trigger])

    assert [event.event_type for event in batch.events] == [
        "task_context_frame",
        "task_node_progress",
        "deviation_event",
        "intervention_trigger",
    ]
    assert batch.events[0].payload["current_task_node_id"] == "cycle1_align_part_a"
    assert batch.events[1].payload["module_title"] == "02 Cycle 1 Align Part A"
    assert batch.events[2].payload["deviation_type"] == "placement_error"
    assert batch.events[3].payload["trigger_type"] == "remote_reset"

    contract_root = Path(__file__).resolve().parents[2] / "shared-models-and-apis" / "examples" / "http"
    example = json.loads((contract_root / "edge-events-batch.request.json").read_text(encoding="utf-8"))
    assert example["events"][0]["event_type"] == batch.events[0].event_type
    assert example["events"][1]["event_type"] == batch.events[1].event_type
    assert example["events"][2]["event_type"] == batch.events[2].event_type


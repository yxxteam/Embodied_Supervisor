from __future__ import annotations

import argparse
import json
import urllib.request

from edge.context.runtime import build_task_context_frame
from edge.context.models import TodoNode
from edge.uplink.events import (
    build_deviation_event,
    build_edge_event_batch,
    build_intervention_trigger,
    build_task_progress_event,
)


def build_demo_session_request() -> dict[str, object]:
    return {
        "site_id": "lab-a",
        "robot_id": "dual-arm-station-01",
        "title": "Dual-arm assembly supervision",
        "objective": "Track task progress, deviations, and teaching assets for a lab session.",
        "sop_plan_id": "sop_dual_arm_assembly_v1",
        "tags": ["assembly", "teaching-demo"],
    }


def build_demo_batch(session_id: str) -> dict[str, object]:
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
    return batch.model_dump(mode="json", exclude_none=True)


def _request_json(method: str, url: str, payload: dict[str, object] | None = None) -> dict[str, object]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        method=method,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def replay_demo(base_url: str) -> dict[str, object]:
    api_root = base_url.rstrip("/")
    session = _request_json("POST", f"{api_root}/api/v1/sessions", build_demo_session_request())
    session_id = str(session["session_id"])
    ingest = _request_json("POST", f"{api_root}/api/v1/sessions/{session_id}/edge-events:batch", build_demo_batch(session_id))
    stream = _request_json("GET", f"{api_root}/api/v1/sessions/{session_id}/stream")
    return {"session": session, "ingest": ingest, "stream": stream}


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay a demo edge-event batch into the backend API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8010", help="Backend service base URL.")
    args = parser.parse_args()

    result = replay_demo(args.base_url)
    summary = {
        "session_id": result["session"]["session_id"],
        "accepted_count": result["ingest"]["accepted_count"],
        "latest_state": result["stream"]["latest_frame"]["state"],
        "latest_deviation": result["stream"]["latest_deviation"]["deviation_type"],
        "latest_intervention": result["stream"]["latest_intervention"]["trigger_type"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

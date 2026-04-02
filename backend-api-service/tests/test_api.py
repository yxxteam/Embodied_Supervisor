import json
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import create_app


def test_create_session_matches_contract_shape(tmp_path) -> None:
    app = create_app(data_root=tmp_path)
    client = TestClient(app)
    examples = Path(__file__).resolve().parents[2] / "shared-models-and-apis" / "examples" / "http"
    payload = json.loads((examples / "create-session.request.json").read_text(encoding="utf-8"))

    response = client.post("/api/v1/sessions", json=payload)
    assert response.status_code == 201
    body = response.json()

    assert body["site_id"] == payload["site_id"]
    assert body["robot_id"] == payload["robot_id"]
    assert body["status"] == "active"
    assert body["session_id"].startswith("sess_")


def test_edge_batch_ingest_updates_stream_snapshot(tmp_path) -> None:
    app = create_app(data_root=tmp_path)
    client = TestClient(app)
    examples = Path(__file__).resolve().parents[2] / "shared-models-and-apis" / "examples" / "http"

    session_response = client.post(
        "/api/v1/sessions",
        json=json.loads((examples / "create-session.request.json").read_text(encoding="utf-8")),
    )
    session_id = session_response.json()["session_id"]

    batch_payload = json.loads((examples / "edge-events-batch.request.json").read_text(encoding="utf-8"))
    for event in batch_payload["events"]:
        event["payload"]["session_id"] = session_id
        if "task_node_id" in event["payload"] and event["payload"]["task_node_id"].startswith("cycle1"):
            event["payload"]["task_node_id"] = event["payload"]["task_node_id"]

    ingest_response = client.post(f"/api/v1/sessions/{session_id}/edge-events:batch", json=batch_payload)
    assert ingest_response.status_code == 200
    accepted = ingest_response.json()
    assert accepted["accepted_count"] == 3
    assert accepted["rejected_count"] == 0

    stream_response = client.get(f"/api/v1/sessions/{session_id}/stream")
    assert stream_response.status_code == 200
    stream = stream_response.json()
    assert stream["session"]["session_id"] == session_id
    assert stream["latest_frame"]["current_task_node_id"] == "cycle1_align_part_a"
    assert stream["latest_progress"]["task_node_id"] == "cycle1_align_part_a"
    assert stream["latest_deviation"]["deviation_type"] == "placement_error"
    assert stream["event_counts"]["task_context_frame"] == 1
    assert stream["event_counts"]["task_node_progress"] == 1
    assert stream["event_counts"]["deviation_event"] == 1


def test_robot_parameter_packet_api_creates_and_returns_latest_packet(tmp_path) -> None:
    app = create_app(data_root=tmp_path)
    client = TestClient(app)
    examples = Path(__file__).resolve().parents[2] / "shared-models-and-apis" / "examples" / "http"

    session_response = client.post(
        "/api/v1/sessions",
        json=json.loads((examples / "create-session.request.json").read_text(encoding="utf-8")),
    )
    session_id = session_response.json()["session_id"]

    request_payload = json.loads((examples / "robot-parameter-input.request.json").read_text(encoding="utf-8"))
    response = client.post(f"/api/v1/sessions/{session_id}/robot-parameter-inputs", json=request_payload)
    assert response.status_code == 201
    packet = response.json()

    assert packet["session_id"] == session_id
    assert packet["command_kind"] == "execute_action"
    assert packet["frame_bytes"] == [66, 9, 5, 1, 81]
    assert packet["checksum"] == 81
    assert packet["target_topic"].endswith("/command")
    assert packet["input"]["action_name"] == "reset"

    latest_response = client.get(f"/api/v1/sessions/{session_id}/robot-parameter-inputs/latest")
    assert latest_response.status_code == 200
    latest_packet = latest_response.json()
    assert latest_packet["packet_id"] == packet["packet_id"]
    assert latest_packet["frame_hex"] == "42 09 05 01 51"

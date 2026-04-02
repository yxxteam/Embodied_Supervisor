import json
from pathlib import Path

from edge.uplink.robot_packets import (
    build_robot_command_topic,
    compute_packet_checksum,
    packet_checksum_is_valid,
)


def test_robot_packet_helpers_match_shared_example() -> None:
    contract_root = Path(__file__).resolve().parents[2] / "shared-models-and-apis" / "examples" / "http"
    packet = json.loads((contract_root / "robot-parameter-input.response.json").read_text(encoding="utf-8"))

    assert build_robot_command_topic(packet["site_id"], packet["robot_id"]) == packet["target_topic"]
    assert compute_packet_checksum(packet["frame_bytes"]) == packet["checksum"]
    assert packet_checksum_is_valid(packet) is True

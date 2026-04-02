from __future__ import annotations

import json
import urllib.request
from typing import Any


def build_robot_command_topic(site_id: str, robot_id: str) -> str:
    return f"embodied/{site_id}/{robot_id}/command"


def compute_packet_checksum(frame_bytes: list[int]) -> int:
    if len(frame_bytes) < 2:
        raise ValueError("frame_bytes must include at least one payload byte and checksum")
    return sum(frame_bytes[:-1]) & 0xFF


def packet_checksum_is_valid(packet: dict[str, Any]) -> bool:
    frame_bytes = [int(item) for item in packet.get("frame_bytes", [])]
    if not frame_bytes:
        return False
    checksum = int(packet.get("checksum", -1))
    return compute_packet_checksum(frame_bytes) == checksum == frame_bytes[-1]


def fetch_latest_robot_parameter_packet(base_url: str, session_id: str) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/sessions/{session_id}/robot-parameter-inputs/latest"
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))

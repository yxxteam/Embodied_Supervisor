from types import SimpleNamespace

import edge.supervisor.validation as validation
from edge.context.models import LiveMonitorConfig, TodoItem, TodoNode


class DummyDetector:
    def detect(self, frame, frame_index: int, timestamp_sec: float):
        return SimpleNamespace(detections=[timestamp_sec])


def test_validate_placement_node_uses_late_failed_frame_when_both_parts_end_on_same_side(
    tmp_path,
    monkeypatch,
) -> None:
    counts_by_timestamp = {
        83.0: (1, 0),
        83.5: (2, 0),
        84.0: (2, 0),
        86.0: (2, 0),
        86.5: (2, 0),
        87.0: (2, 0),
        87.5: (2, 0),
    }
    written = {}

    def fake_read_frame_at_timestamp(video_path, timestamp_sec: float):
        return SimpleNamespace(shape=(100, 100, 3), timestamp=round(timestamp_sec, 1))

    def fake_count_side_parts_from_yolo(detections, frame_width: int, config: LiveMonitorConfig):
        return (0, 0)

    def fake_count_side_contours(frame, config: LiveMonitorConfig):
        return counts_by_timestamp.get(frame.timestamp, (1, 0))

    def fake_write_annotated_frame(**kwargs):
        written.update(kwargs)

    monkeypatch.setattr(validation, "_read_frame_at_timestamp", fake_read_frame_at_timestamp)
    monkeypatch.setattr(validation, "_count_side_parts_from_yolo", fake_count_side_parts_from_yolo)
    monkeypatch.setattr(validation, "_count_side_contours", fake_count_side_contours)
    monkeypatch.setattr(validation, "_write_annotated_frame", fake_write_annotated_frame)

    result = validation._validate_placement_node(
        video_path="vedio.mp4",
        node=TodoNode(
            todo_id="run1_final_placement",
            title="第一次成品归位",
            cycle_id=1,
            event_kind="placement",
            status="completed",
            start_sec=82.0,
            end_sec=83.0,
        ),
        item=TodoItem(
            id="run1_final_placement",
            title="第一次成品归位",
            cycle_id=1,
            event_kind="placement",
            post_padding_sec=6.0,
            search_end_sec=88.0,
        ),
        keyframes_dir=tmp_path / "keyframes",
        alerts_dir=tmp_path / "alerts",
        config=LiveMonitorConfig(expected_left_part_count=1, expected_right_part_count=1),
        detector=DummyDetector(),
    )

    assert result is not None
    assert result["status"] == "failed"
    assert result["timestamp_sec"] == 87.5
    assert result["image_path"] == "alerts/validation_run1_final_placement.jpg"
    assert result["details"]["part_count_left"] == 2
    assert result["details"]["part_count_right"] == 0
    assert written["title"] == "run1_final_placement FAILED"


def test_validate_placement_node_uses_first_passed_frame_when_left_right_target_is_reached(
    tmp_path,
    monkeypatch,
) -> None:
    counts_by_timestamp = {
        220.0: (1, 0),
        220.5: (1, 1),
        221.0: (1, 1),
        221.5: (1, 1),
    }
    written = {}

    def fake_read_frame_at_timestamp(video_path, timestamp_sec: float):
        return SimpleNamespace(shape=(100, 100, 3), timestamp=round(timestamp_sec, 1))

    def fake_count_side_parts_from_yolo(detections, frame_width: int, config: LiveMonitorConfig):
        return (0, 0)

    def fake_count_side_contours(frame, config: LiveMonitorConfig):
        return counts_by_timestamp.get(frame.timestamp, (1, 0))

    def fake_write_annotated_frame(**kwargs):
        written.update(kwargs)

    monkeypatch.setattr(validation, "_read_frame_at_timestamp", fake_read_frame_at_timestamp)
    monkeypatch.setattr(validation, "_count_side_parts_from_yolo", fake_count_side_parts_from_yolo)
    monkeypatch.setattr(validation, "_count_side_contours", fake_count_side_contours)
    monkeypatch.setattr(validation, "_write_annotated_frame", fake_write_annotated_frame)

    result = validation._validate_placement_node(
        video_path="vedio.mp4",
        node=TodoNode(
            todo_id="run2_final_placement",
            title="第二次成品归位",
            cycle_id=2,
            event_kind="placement",
            status="completed",
            start_sec=219.0,
            end_sec=220.0,
        ),
        item=TodoItem(
            id="run2_final_placement",
            title="第二次成品归位",
            cycle_id=2,
            event_kind="placement",
            post_padding_sec=6.0,
            search_end_sec=226.0,
        ),
        keyframes_dir=tmp_path / "keyframes",
        alerts_dir=tmp_path / "alerts",
        config=LiveMonitorConfig(expected_left_part_count=1, expected_right_part_count=1),
        detector=DummyDetector(),
    )

    assert result is not None
    assert result["status"] == "passed"
    assert result["timestamp_sec"] == 220.5
    assert result["image_path"] == "keyframes/validation_run2_final_placement.jpg"
    assert result["details"]["part_count_left"] == 1
    assert result["details"]["part_count_right"] == 1
    assert written["title"] == "run2_final_placement PASSED"


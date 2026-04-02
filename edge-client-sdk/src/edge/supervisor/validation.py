from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2

from edge.context.models import LiveMonitorConfig, TodoItem, TodoNode


def _read_frame_at_timestamp(video_path: str | Path, timestamp_sec: float):
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"无法打开视频文件: {video_path}")

    fps = float(capture.get(cv2.CAP_PROP_FPS) or 30.0)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    max_frame_index = max(frame_count - 1, 0)
    frame_index = min(max(0, int(timestamp_sec * fps)), max_frame_index)
    capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ok, frame = capture.read()
    capture.release()
    if not ok:
        raise RuntimeError(f"无法读取视频帧: {video_path} @ {timestamp_sec}")
    return frame


def _yellow_mask(frame, config: LiveMonitorConfig):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower = (config.yellow_h_min, config.yellow_s_min, config.yellow_v_min)
    upper = (config.yellow_h_max, 255, 255)
    return cv2.inRange(hsv, lower, upper)


def _count_contours_in_region(mask, min_area_ratio: float) -> int:
    min_area = max(12.0, mask.shape[0] * mask.shape[1] * min_area_ratio)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return sum(1 for contour in contours if cv2.contourArea(contour) >= min_area)


def _count_side_contours(frame, config: LiveMonitorConfig) -> tuple[int, int]:
    mask = _yellow_mask(frame, config)
    _, width = mask.shape
    left_end = int(width * config.left_zone_ratio)
    right_start = int(width * (1 - config.left_zone_ratio))
    left_count = _count_contours_in_region(mask[:, :left_end], config.contour_min_area_ratio)
    right_count = _count_contours_in_region(mask[:, right_start:], config.contour_min_area_ratio)
    return left_count, right_count


def _count_side_parts_from_yolo(detections, frame_width: int, config: LiveMonitorConfig) -> tuple[int, int]:
    labels = set(config.part_labels)
    left_boundary = frame_width * config.left_zone_ratio
    right_boundary = frame_width * (1 - config.left_zone_ratio)
    left_count = 0
    right_count = 0
    for detection in detections:
        if detection.label not in labels or len(detection.bbox) != 4:
            continue
        x1, _, x2, _ = detection.bbox
        center_x = (x1 + x2) / 2
        if center_x <= left_boundary:
            left_count += 1
        elif center_x >= right_boundary:
            right_count += 1
    return left_count, right_count


def _write_annotated_frame(
    video_path: str | Path,
    output_path: str | Path,
    timestamp_sec: float,
    title: str,
    subtitle: str,
    left_zone_ratio: float,
) -> None:
    frame = _read_frame_at_timestamp(video_path, timestamp_sec)
    height, width = frame.shape[:2]
    left_boundary = int(width * left_zone_ratio)
    right_boundary = int(width * (1 - left_zone_ratio))
    annotated = frame.copy()
    cv2.rectangle(annotated, (0, 0), (left_boundary, height), (0, 200, 255), 2)
    cv2.rectangle(annotated, (right_boundary, 0), (width - 1, height - 1), (0, 200, 255), 2)
    cv2.putText(annotated, title[:42], (16, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.78, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(annotated, title[:42], (16, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.78, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(annotated, subtitle[:80], (16, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.56, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(annotated, subtitle[:80], (16, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.56, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.imwrite(str(output_path), annotated)


def _placement_score(left_count: int, right_count: int, config: LiveMonitorConfig) -> float:
    left_target = max(config.expected_left_part_count, 1)
    right_target = max(config.expected_right_part_count, 1)
    left_score = min(left_count / left_target, 1.0)
    right_score = min(right_count / right_target, 1.0)
    balance_bonus = (
        0.0
        if (left_count + right_count) == 0
        else 1.0 - abs(left_count - right_count) / max(left_count + right_count, 1)
    )
    return left_score + right_score + balance_bonus * 0.1 + (left_count + right_count) * 0.001


def _select_best_placement_record(
    records: list[dict[str, Any]],
    config: LiveMonitorConfig,
) -> dict[str, Any] | None:
    if not records:
        return None

    expected_total = config.expected_left_part_count + config.expected_right_part_count
    passed_records = [
        record
        for record in records
        if record["left_count"] >= config.expected_left_part_count
        and record["right_count"] >= config.expected_right_part_count
    ]
    if passed_records:
        complete_records = [
            record for record in passed_records if (record["left_count"] + record["right_count"]) >= expected_total
        ]
        candidates = complete_records or passed_records
        return min(
            candidates,
            key=lambda record: (
                record["timestamp_sec"],
                -(record["left_count"] + record["right_count"]),
                -record["score"],
            ),
        )

    fully_visible_records = [
        record for record in records if (record["left_count"] + record["right_count"]) >= expected_total
    ]
    if fully_visible_records:
        return max(
            fully_visible_records,
            key=lambda record: (
                record["timestamp_sec"],
                record["left_count"] + record["right_count"],
                record["score"],
            ),
        )

    return max(
        records,
        key=lambda record: (
            record["left_count"] + record["right_count"],
            record["score"],
            record["timestamp_sec"],
        ),
    )


def _validate_placement_node(
    video_path: str | Path,
    node: TodoNode,
    item: TodoItem | None,
    keyframes_dir: str | Path,
    alerts_dir: str | Path,
    config: LiveMonitorConfig,
    detector,
) -> dict[str, Any] | None:
    if node.start_sec is None and node.end_sec is None:
        return None

    if item is not None and item.fixed_start_sec is not None and item.fixed_end_sec is not None:
        start_sec = float(item.fixed_start_sec)
        end_sec = float(item.fixed_end_sec)
    else:
        base_start = node.end_sec if node.end_sec is not None else node.start_sec
        start_sec = float(base_start if base_start is not None else 0.0)
        if item is not None and item.search_start_sec is not None:
            start_sec = max(start_sec, float(item.search_start_sec))

        end_candidates = [float(node.end_sec if node.end_sec is not None else start_sec + 2.0) + 1.0]
        if item is not None:
            end_candidates.append(start_sec + max(item.post_padding_sec, 1.0))
            if item.search_end_sec is not None:
                end_candidates.append(float(item.search_end_sec))
        end_sec = max(end_candidates)

    candidate_times: list[float] = []
    current = max(0.0, start_sec)
    upper = max(current + 0.001, end_sec)
    while current <= upper + 1e-6:
        candidate_times.append(round(current, 3))
        current += 0.5
    if not candidate_times:
        candidate_times = [round(start_sec, 3)]

    records: list[dict[str, Any]] = []
    for timestamp_sec in candidate_times:
        frame = _read_frame_at_timestamp(video_path, timestamp_sec)
        observation = detector.detect(frame=frame, frame_index=int(timestamp_sec * 1000), timestamp_sec=timestamp_sec)
        yolo_left, yolo_right = _count_side_parts_from_yolo(observation.detections, frame.shape[1], config)
        color_left, color_right = _count_side_contours(frame, config)
        left_count = max(yolo_left, color_left)
        right_count = max(yolo_right, color_right)
        records.append(
            {
                "timestamp_sec": timestamp_sec,
                "left_count": left_count,
                "right_count": right_count,
                "yolo_left_count": yolo_left,
                "yolo_right_count": yolo_right,
                "color_left_count": color_left,
                "color_right_count": color_right,
                "score": _placement_score(left_count, right_count, config),
            }
        )

    best_record = _select_best_placement_record(records, config)
    if best_record is None:
        return None

    passed = (
        best_record["left_count"] >= config.expected_left_part_count
        and best_record["right_count"] >= config.expected_right_part_count
    )
    event_id = f"validation_{node.todo_id}"
    frame_name = f"{event_id}.jpg"
    frame_dir = Path(keyframes_dir) if passed else Path(alerts_dir)
    frame_path = frame_dir / frame_name
    subtitle = (
        f"L {best_record['left_count']}/{config.expected_left_part_count} "
        f"R {best_record['right_count']}/{config.expected_right_part_count}"
    )
    _write_annotated_frame(
        video_path=video_path,
        output_path=frame_path,
        timestamp_sec=best_record["timestamp_sec"],
        title=f"{node.todo_id} {'PASSED' if passed else 'FAILED'}",
        subtitle=subtitle,
        left_zone_ratio=config.left_zone_ratio,
    )
    return {
        "id": event_id,
        "title": node.module_title or node.title,
        "message": "达到一左一右归位效果。" if passed else "未达到一左一右归位效果。",
        "timestamp_sec": best_record["timestamp_sec"],
        "cycle_id": node.cycle_id,
        "status": "passed" if passed else "failed",
        "image_path": f"{'keyframes' if passed else 'alerts'}/{frame_name}",
        "details": {
            "expected_left_part_count": config.expected_left_part_count,
            "expected_right_part_count": config.expected_right_part_count,
            "part_count_left": best_record["left_count"],
            "part_count_right": best_record["right_count"],
            "yolo_part_count_left": best_record["yolo_left_count"],
            "yolo_part_count_right": best_record["yolo_right_count"],
            "color_part_count_left": best_record["color_left_count"],
            "color_part_count_right": best_record["color_right_count"],
        },
    }

from __future__ import annotations

from dataclasses import dataclass

from edge.context.models import FrameObservation, TimelineWindow, TodoItem, TodoNode


@dataclass(slots=True)
class WindowMatch:
    window: TimelineWindow
    score: float
    matched_labels: list[str]


def score_window(todo: TodoItem, window: TimelineWindow) -> WindowMatch:
    expected = todo.expected_objects
    if not expected:
        return WindowMatch(window=window, score=0.0, matched_labels=[])

    matched = [label for label in expected if window.label_counts.get(label, 0) > 0]
    if not matched:
        return WindowMatch(window=window, score=0.0, matched_labels=[])

    presence_score = len(matched) / len(expected)
    completeness_score = presence_score**2
    density_score = min(
        sum(window.label_counts[label] for label in matched) / max(len(expected), 1),
        1.0,
    )
    score = round(completeness_score * 0.7 + density_score * 0.3, 4)
    return WindowMatch(window=window, score=score, matched_labels=matched)


def split_segments(matches: list) -> list[list]:
    if not matches:
        return []

    segments: list[list] = [[matches[0]]]
    for current in matches[1:]:
        previous = segments[-1][-1]
        if current.window.index - previous.window.index <= 1:
            segments[-1].append(current)
        else:
            segments.append([current])
    return segments


def collect_evidence(
    observations: list[FrameObservation],
    expected_objects: list[str],
    start_sec: float | None,
    end_sec: float | None,
    limit: int = 3,
) -> tuple[list[int], list[float], list[str]]:
    if start_sec is None or end_sec is None:
        return [], [], []

    scored_frames: list[tuple[float, FrameObservation, list[str]]] = []
    matched_objects: set[str] = set()

    for observation in observations:
        if observation.timestamp_sec < start_sec or observation.timestamp_sec >= end_sec:
            continue
        matched = [label for label in expected_objects if observation.label_counts.get(label, 0) > 0]
        if not matched:
            continue
        score = len(matched) / max(len(expected_objects), 1)
        scored_frames.append((score, observation, matched))
        matched_objects.update(matched)

    scored_frames.sort(key=lambda item: (-item[0], item[1].timestamp_sec))
    top_frames = scored_frames[:limit]
    frame_indexes = [item[1].frame_index for item in top_frames]
    timestamps = [item[1].timestamp_sec for item in top_frames]
    return frame_indexes, timestamps, sorted(matched_objects)


def match_todo_items(
    todo_items: list[TodoItem],
    timeline: list[TimelineWindow],
    observations: list[FrameObservation],
) -> list[TodoNode]:
    nodes: list[TodoNode] = []
    cursor_window_index = 0

    for todo in todo_items:
        remaining_timeline = [window for window in timeline if window.index >= cursor_window_index]
        scored = [score_window(todo, window) for window in remaining_timeline]
        hits = [item for item in scored if item.score >= todo.success_threshold]
        segments = split_segments(hits)
        best_segment = max(
            segments,
            key=lambda segment: (len(segment), sum(item.score for item in segment) / len(segment)),
            default=[],
        )

        partial_candidates = [item for item in scored if item.score > 0]
        partial_segments = split_segments(partial_candidates)
        best_partial = max(
            partial_segments,
            key=lambda segment: (len(segment), sum(item.score for item in segment) / len(segment)),
            default=[],
        )

        notes = ""
        if not todo.expected_objects:
            notes = "未显式配置 expected_objects，仅能输出低置信度结果。"

        if best_segment:
            start_sec = best_segment[0].window.start_sec
            end_sec = best_segment[-1].window.end_sec
            duration_sec = round(end_sec - start_sec, 3)
            avg_score = round(sum(item.score for item in best_segment) / len(best_segment), 4)
            frame_indexes, timestamps, matched_objects = collect_evidence(
                observations,
                todo.expected_objects,
                start_sec,
                end_sec,
            )
            status = "completed"
            if len(best_segment) < todo.min_hits or duration_sec < todo.min_duration_sec:
                status = "partial"
                notes = "命中窗口存在，但未达到最小持续时间或最小命中次数。"

            cursor_window_index = best_segment[-1].window.index + 1
            nodes.append(
                TodoNode(
                    todo_id=todo.id,
                    title=todo.title,
                    module_title=todo.module_title,
                    module_summary=todo.module_summary or todo.description,
                    cycle_id=todo.cycle_id,
                    event_kind=todo.event_kind,
                    status=status,
                    expected_objects=todo.expected_objects,
                    matched_objects=matched_objects,
                    missing_objects=[label for label in todo.expected_objects if label not in matched_objects],
                    start_sec=start_sec,
                    end_sec=end_sec,
                    duration_sec=duration_sec,
                    match_score=avg_score,
                    hit_windows=len(best_segment),
                    evidence_frames=frame_indexes,
                    evidence_timestamps_sec=timestamps,
                    notes=notes,
                )
            )
            continue

        if best_partial:
            start_sec = best_partial[0].window.start_sec
            end_sec = best_partial[-1].window.end_sec
            duration_sec = round(end_sec - start_sec, 3)
            avg_score = round(sum(item.score for item in best_partial) / len(best_partial), 4)
            frame_indexes, timestamps, matched_objects = collect_evidence(
                observations,
                todo.expected_objects,
                start_sec,
                end_sec,
            )
            cursor_window_index = best_partial[-1].window.index + 1
            nodes.append(
                TodoNode(
                    todo_id=todo.id,
                    title=todo.title,
                    module_title=todo.module_title,
                    module_summary=todo.module_summary or todo.description,
                    cycle_id=todo.cycle_id,
                    event_kind=todo.event_kind,
                    status="partial",
                    expected_objects=todo.expected_objects,
                    matched_objects=matched_objects,
                    missing_objects=[label for label in todo.expected_objects if label not in matched_objects],
                    start_sec=start_sec,
                    end_sec=end_sec,
                    duration_sec=duration_sec,
                    match_score=avg_score,
                    hit_windows=len(best_partial),
                    evidence_frames=frame_indexes,
                    evidence_timestamps_sec=timestamps,
                    notes="检测到相关目标，但匹配度未达到完成阈值。",
                )
            )
            continue

        nodes.append(
            TodoNode(
                todo_id=todo.id,
                title=todo.title,
                module_title=todo.module_title,
                module_summary=todo.module_summary or todo.description,
                cycle_id=todo.cycle_id,
                event_kind=todo.event_kind,
                status="missing",
                expected_objects=todo.expected_objects,
                matched_objects=[],
                missing_objects=todo.expected_objects,
                match_score=0.0,
                hit_windows=0,
                notes=notes or "未检测到与该 todo 节点相关的窗口。",
            )
        )

    return nodes


def annotate_timeline_with_nodes(
    timeline: list[TimelineWindow],
    nodes: list[TodoNode],
) -> list[TimelineWindow]:
    annotated: list[TimelineWindow] = []
    for window in timeline:
        matched_ids = [
            node.todo_id
            for node in nodes
            if node.start_sec is not None
            and node.end_sec is not None
            and window.start_sec >= node.start_sec
            and window.end_sec <= node.end_sec
        ]
        annotated.append(window.model_copy(update={"matched_todo_ids": matched_ids}))
    return annotated

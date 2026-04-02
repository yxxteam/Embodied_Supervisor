from __future__ import annotations

from dataclasses import dataclass

from edge.context.models import SignalObservation, SignalRule, TimelineWindow, TodoItem, TodoNode
from edge.supervisor.object_matcher import split_segments


@dataclass(slots=True)
class SignalMatch:
    window: TimelineWindow
    score: float
    matched_metrics: dict[str, float]


def evaluate_signal_rule(rule: SignalRule, metrics: dict[str, float]) -> float:
    value = metrics.get(rule.metric)
    if value is None:
        return 0.0

    if rule.op == "gte":
        threshold = rule.value if rule.value is not None else 0.0
        if threshold <= 1e-6:
            return 1.0 if value >= threshold else 0.0
        if value >= threshold:
            return 1.0
        return max(0.0, value / threshold)

    if rule.op == "lte":
        threshold = rule.value if rule.value is not None else 0.0
        if value <= threshold:
            return 1.0
        tolerance = max(abs(threshold), 1.0)
        return max(0.0, 1.0 - (value - threshold) / tolerance)

    lower = rule.min_value if rule.min_value is not None else float("-inf")
    upper = rule.max_value if rule.max_value is not None else float("inf")
    if lower <= value <= upper:
        return 1.0
    if value < lower:
        tolerance = max(abs(lower), 1.0)
        return max(0.0, 1.0 - (lower - value) / tolerance)
    tolerance = max(abs(upper - lower), abs(upper), 1.0)
    return max(0.0, 1.0 - (value - upper) / tolerance)


def score_signal_window(todo: TodoItem, window: TimelineWindow) -> SignalMatch:
    if not todo.signal_rules:
        score = window.metrics.get("motion_norm", 0.0)
        return SignalMatch(window=window, score=round(score, 4), matched_metrics={"motion_norm": score})

    weighted_scores: list[float] = []
    matched_metrics: dict[str, float] = {}
    total_weight = 0.0

    for rule in todo.signal_rules:
        rule_score = evaluate_signal_rule(rule, window.metrics)
        weighted_scores.append(rule_score * rule.weight)
        total_weight += rule.weight
        matched_metrics[rule.metric] = round(window.metrics.get(rule.metric, 0.0), 6)

    final_score = sum(weighted_scores) / total_weight if total_weight > 0 else 0.0
    return SignalMatch(window=window, score=round(final_score, 4), matched_metrics=matched_metrics)


def _summarize_metrics(segment: list[SignalMatch], todo: TodoItem) -> dict[str, float]:
    if not segment:
        return {}

    metric_names = [rule.metric for rule in todo.signal_rules] or ["motion_norm"]
    summary: dict[str, float] = {}
    for metric in metric_names:
        values = [item.window.metrics.get(metric, 0.0) for item in segment]
        summary[metric] = round(sum(values) / len(values), 4)
    return summary


def collect_signal_evidence(
    observations: list[SignalObservation],
    todo: TodoItem,
    start_sec: float | None,
    end_sec: float | None,
    limit: int = 3,
) -> tuple[list[int], list[float], dict[str, float]]:
    if start_sec is None or end_sec is None:
        return [], [], {}

    total_weight = sum(rule.weight for rule in todo.signal_rules)
    scored: list[tuple[float, SignalObservation]] = []
    for observation in observations:
        if observation.timestamp_sec < start_sec or observation.timestamp_sec >= end_sec:
            continue
        score = (
            sum(evaluate_signal_rule(rule, observation.metrics) * rule.weight for rule in todo.signal_rules)
            / max(total_weight, 1.0)
            if todo.signal_rules
            else observation.metrics.get("motion_norm", 0.0)
        )
        scored.append((score, observation))

    scored.sort(key=lambda item: (-item[0], item[1].timestamp_sec))
    top = scored[:limit]
    if not top:
        return [], [], {}

    frame_indexes = [item[1].frame_index for item in top]
    timestamps = [item[1].timestamp_sec for item in top]
    metrics_summary = {
        metric: round(sum(item[1].metrics.get(metric, 0.0) for item in top) / len(top), 4)
        for metric in ([rule.metric for rule in todo.signal_rules] or ["motion_norm"])
    }
    return frame_indexes, timestamps, metrics_summary


def _segment_duration(segment: list[SignalMatch]) -> float:
    if not segment:
        return 0.0
    return round(segment[-1].window.end_sec - segment[0].window.start_sec, 3)


def _pick_ordered_completed_segment(
    segments: list[list[SignalMatch]],
    todo: TodoItem,
) -> list[SignalMatch]:
    for segment in segments:
        for end_index in range(1, len(segment) + 1):
            candidate = segment[:end_index]
            if len(candidate) >= todo.min_hits and _segment_duration(candidate) >= todo.min_duration_sec:
                return candidate
    return []


def _pick_ordered_partial_segment(segments: list[list[SignalMatch]]) -> list[SignalMatch]:
    for segment in segments:
        if segment:
            return segment
    return []


def _collect_fixed_windows(
    timeline: list[TimelineWindow],
    start_sec: float,
    end_sec: float,
) -> list[TimelineWindow]:
    return [
        window
        for window in timeline
        if window.end_sec > start_sec and window.start_sec < end_sec
    ]


def _fixed_cursor_window_index(
    timeline: list[TimelineWindow],
    end_sec: float,
    fallback: int,
) -> int:
    covered = [window.index for window in timeline if window.start_sec < end_sec]
    if not covered:
        return fallback
    return max(covered) + 1


def _build_fixed_todo_node(
    todo: TodoItem,
    timeline: list[TimelineWindow],
    observations: list[SignalObservation],
) -> TodoNode:
    assert todo.fixed_start_sec is not None
    assert todo.fixed_end_sec is not None

    start_sec = float(todo.fixed_start_sec)
    end_sec = float(todo.fixed_end_sec)
    duration_sec = round(max(end_sec - start_sec, 0.0), 3)
    frame_indexes, timestamps, metrics_summary = collect_signal_evidence(
        observations,
        todo,
        start_sec,
        end_sec,
    )
    fixed_windows = _collect_fixed_windows(timeline, start_sec, end_sec)
    hit_windows = len(fixed_windows)
    notes = "使用 todo 固定时间段切分。"
    status = "completed" if duration_sec > 0 else "missing"
    if hit_windows == 0:
        notes = "固定时间段内没有采样窗口。"

    return TodoNode(
        todo_id=todo.id,
        title=todo.title,
        module_title=todo.module_title or todo.title,
        module_summary=todo.module_summary or todo.description,
        cycle_id=todo.cycle_id,
        event_kind=todo.event_kind,
        status=status,
        start_sec=start_sec if status != "missing" else None,
        end_sec=end_sec if status != "missing" else None,
        duration_sec=duration_sec if status != "missing" else 0.0,
        match_score=1.0 if status == "completed" else 0.0,
        hit_windows=hit_windows,
        evidence_frames=frame_indexes,
        evidence_timestamps_sec=timestamps,
        summary_metrics=metrics_summary,
        notes=notes,
    )


def match_signal_todo_items(
    todo_items: list[TodoItem],
    timeline: list[TimelineWindow],
    observations: list[SignalObservation],
) -> list[TodoNode]:
    nodes: list[TodoNode] = []
    cursor_window_index = 0

    for todo in todo_items:
        if todo.fixed_start_sec is not None and todo.fixed_end_sec is not None:
            node = _build_fixed_todo_node(todo, timeline, observations)
            nodes.append(node)
            cursor_window_index = _fixed_cursor_window_index(
                timeline,
                float(todo.fixed_end_sec),
                cursor_window_index,
            )
            continue

        scoped_timeline = [
            window
            for window in timeline
            if window.index >= cursor_window_index
            and (todo.search_start_sec is None or window.start_sec >= todo.search_start_sec)
            and (todo.search_end_sec is None or window.end_sec <= todo.search_end_sec)
        ]
        scored = [score_signal_window(todo, window) for window in scoped_timeline]
        hits = [item for item in scored if item.score >= todo.success_threshold]
        best_segment = _pick_ordered_completed_segment(split_segments(hits), todo)

        partial_candidates = [item for item in scored if item.score > 0]
        best_partial = _pick_ordered_partial_segment(split_segments(partial_candidates))

        if best_segment:
            start_sec = best_segment[0].window.start_sec
            end_sec = best_segment[-1].window.end_sec
            duration_sec = round(end_sec - start_sec, 3)
            avg_score = round(sum(item.score for item in best_segment) / len(best_segment), 4)
            frame_indexes, timestamps, metrics_summary = collect_signal_evidence(
                observations,
                todo,
                start_sec,
                end_sec,
            )
            status = "completed"
            notes = ""
            if len(best_segment) < todo.min_hits or duration_sec < todo.min_duration_sec:
                status = "partial"
                notes = "命中窗口存在，但未达到最小持续时间或最小命中次数。"
            cursor_window_index = best_segment[-1].window.index + 1
            nodes.append(
                TodoNode(
                    todo_id=todo.id,
                    title=todo.title,
                    module_title=todo.module_title or todo.title,
                    module_summary=todo.module_summary or todo.description,
                    cycle_id=todo.cycle_id,
                    event_kind=todo.event_kind,
                    status=status,
                    start_sec=start_sec,
                    end_sec=end_sec,
                    duration_sec=duration_sec,
                    match_score=avg_score,
                    hit_windows=len(best_segment),
                    evidence_frames=frame_indexes,
                    evidence_timestamps_sec=timestamps,
                    summary_metrics=_summarize_metrics(best_segment, todo) | metrics_summary,
                    notes=notes,
                )
            )
            continue

        if best_partial:
            start_sec = best_partial[0].window.start_sec
            end_sec = best_partial[-1].window.end_sec
            duration_sec = round(end_sec - start_sec, 3)
            avg_score = round(sum(item.score for item in best_partial) / len(best_partial), 4)
            frame_indexes, timestamps, metrics_summary = collect_signal_evidence(
                observations,
                todo,
                start_sec,
                end_sec,
            )
            cursor_window_index = best_partial[-1].window.index + 1
            nodes.append(
                TodoNode(
                    todo_id=todo.id,
                    title=todo.title,
                    module_title=todo.module_title or todo.title,
                    module_summary=todo.module_summary or todo.description,
                    cycle_id=todo.cycle_id,
                    event_kind=todo.event_kind,
                    status="partial",
                    start_sec=start_sec,
                    end_sec=end_sec,
                    duration_sec=duration_sec,
                    match_score=avg_score,
                    hit_windows=len(best_partial),
                    evidence_frames=frame_indexes,
                    evidence_timestamps_sec=timestamps,
                    summary_metrics=_summarize_metrics(best_partial, todo) | metrics_summary,
                    notes="检测到相关片段，但匹配度未达到完成阈值。",
                )
            )
            continue

        nodes.append(
            TodoNode(
                todo_id=todo.id,
                title=todo.title,
                module_title=todo.module_title or todo.title,
                module_summary=todo.module_summary or todo.description,
                cycle_id=todo.cycle_id,
                event_kind=todo.event_kind,
                status="missing",
                notes="未找到满足该节点规则的时间片段。",
            )
        )

    return nodes


def annotate_signal_timeline(
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

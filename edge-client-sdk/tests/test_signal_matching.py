from edge.capture.timeline import build_signal_timeline
from edge.context.models import SignalObservation, SignalRule, TimelineWindow, TodoItem
from edge.supervisor.signal_matcher import evaluate_signal_rule, match_signal_todo_items


def make_signal_window(index: int, motion: float, dual: float, center: float, focus: float) -> TimelineWindow:
    return TimelineWindow(
        index=index,
        start_sec=float(index),
        end_sec=float(index + 1),
        metrics={
            "motion_norm": motion,
            "dual_arm_activity": dual,
            "yellow_center_norm": center,
            "center_focus": focus,
        },
    )


def test_evaluate_signal_rule_supports_between() -> None:
    rule = SignalRule(metric="motion_norm", op="between", min_value=0.4, max_value=0.8)
    assert evaluate_signal_rule(rule, {"motion_norm": 0.6}) == 1.0
    assert evaluate_signal_rule(rule, {"motion_norm": 0.2}) < 1.0


def test_signal_matching_assigns_non_overlapping_stages() -> None:
    timeline = [
        make_signal_window(0, 0.9, 0.8, 0.1, 0.1),
        make_signal_window(1, 0.88, 0.82, 0.2, 0.1),
        make_signal_window(2, 0.55, 0.4, 0.72, 0.55),
        make_signal_window(3, 0.58, 0.42, 0.78, 0.62),
        make_signal_window(4, 0.7, 0.76, 0.92, 0.75),
        make_signal_window(5, 0.72, 0.79, 0.95, 0.82),
    ]
    observations = [
        SignalObservation(frame_index=index * 10, timestamp_sec=float(index), metrics=window.metrics)
        for index, window in enumerate(timeline)
    ]
    items = [
        TodoItem(
            id="approach",
            title="双臂进入",
            success_threshold=0.8,
            min_hits=2,
            min_duration_sec=2,
            signal_rules=[
                SignalRule(metric="motion_norm", op="gte", value=0.8, weight=1.0),
                SignalRule(metric="dual_arm_activity", op="gte", value=0.75, weight=1.0),
            ],
        ),
        TodoItem(
            id="transfer",
            title="移动到中心",
            success_threshold=0.75,
            min_hits=2,
            min_duration_sec=2,
            signal_rules=[
                SignalRule(metric="yellow_center_norm", op="gte", value=0.7, weight=1.0),
                SignalRule(metric="center_focus", op="gte", value=0.5, weight=1.0),
            ],
        ),
        TodoItem(
            id="insert",
            title="插装",
            success_threshold=0.8,
            min_hits=2,
            min_duration_sec=2,
            signal_rules=[
                SignalRule(metric="yellow_center_norm", op="gte", value=0.9, weight=1.0),
                SignalRule(metric="dual_arm_activity", op="gte", value=0.7, weight=1.0),
            ],
        ),
    ]

    nodes = match_signal_todo_items(items, timeline, observations)

    assert [node.status for node in nodes] == ["completed", "completed", "completed"]
    assert nodes[0].start_sec == 0.0
    assert nodes[0].end_sec == 2.0
    assert nodes[1].start_sec == 2.0
    assert nodes[1].end_sec == 4.0
    assert nodes[2].start_sec == 4.0
    assert nodes[2].end_sec == 6.0


def test_signal_matching_supports_fixed_time_segments() -> None:
    timeline = [
        make_signal_window(0, 0.1, 0.1, 0.1, 0.1),
        make_signal_window(1, 0.2, 0.1, 0.1, 0.1),
        make_signal_window(2, 0.9, 0.8, 0.8, 0.6),
        make_signal_window(3, 0.85, 0.75, 0.82, 0.62),
        make_signal_window(4, 0.12, 0.1, 0.1, 0.1),
    ]
    observations = [
        SignalObservation(frame_index=index * 10, timestamp_sec=float(index), metrics=window.metrics)
        for index, window in enumerate(timeline)
    ]
    items = [
        TodoItem(
            id="pickup",
            title="拿起零件",
            fixed_start_sec=1.0,
            fixed_end_sec=3.0,
            signal_rules=[
                SignalRule(metric="motion_norm", op="gte", value=0.5, weight=1.0),
            ],
        ),
        TodoItem(
            id="align",
            title="对准零件",
            fixed_start_sec=3.0,
            fixed_end_sec=4.0,
            signal_rules=[
                SignalRule(metric="yellow_center_norm", op="gte", value=0.7, weight=1.0),
            ],
        ),
    ]

    nodes = match_signal_todo_items(items, timeline, observations)

    assert [node.status for node in nodes] == ["completed", "completed"]
    assert nodes[0].start_sec == 1.0
    assert nodes[0].end_sec == 3.0
    assert nodes[0].match_score == 1.0
    assert nodes[0].notes == "使用 todo 固定时间段切分。"
    assert nodes[1].start_sec == 3.0
    assert nodes[1].end_sec == 4.0


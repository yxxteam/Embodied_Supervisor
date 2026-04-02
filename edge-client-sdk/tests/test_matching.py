from edge.capture.timeline import build_timeline
from edge.context.models import Detection, FrameObservation, TodoItem
from edge.context.todo import infer_expected_objects, load_todo_plan
from edge.supervisor.object_matcher import match_todo_items


def make_observation(timestamp_sec: float, labels: list[str]) -> FrameObservation:
    label_counts: dict[str, int] = {}
    detections: list[Detection] = []
    for index, label in enumerate(labels):
        label_counts[label] = label_counts.get(label, 0) + 1
        detections.append(
            Detection(
                label=label,
                confidence=0.9,
                bbox=[index, index, index + 10, index + 10],
            )
        )
    return FrameObservation(
        frame_index=int(timestamp_sec * 10),
        timestamp_sec=timestamp_sec,
        detections=detections,
        label_counts=label_counts,
    )


def test_todo_matching_generates_completed_nodes() -> None:
    observations = [
        make_observation(0.0, ["robot_arm", "box"]),
        make_observation(1.0, ["robot_arm", "box"]),
        make_observation(2.0, ["robot_arm", "table"]),
        make_observation(3.0, ["robot_arm", "table"]),
        make_observation(4.0, ["robot_arm", "part", "table"]),
        make_observation(5.0, ["robot_arm", "part", "table"]),
    ]

    todo_items = [
        TodoItem(
            id="pickup",
            title="取料",
            expected_objects=["robot_arm", "box"],
            success_threshold=0.7,
            min_hits=2,
            min_duration_sec=2,
        ),
        TodoItem(
            id="assembly",
            title="装配",
            expected_objects=["robot_arm", "part", "table"],
            success_threshold=0.6,
            min_hits=2,
            min_duration_sec=2,
        ),
    ]

    timeline = build_timeline(observations, window_sec=1.0)
    nodes = match_todo_items(todo_items, timeline, observations)

    assert nodes[0].status == "completed"
    assert nodes[0].start_sec == 0.0
    assert nodes[0].end_sec == 2.0
    assert set(nodes[0].matched_objects) == {"box", "robot_arm"}

    assert nodes[1].status == "completed"
    assert nodes[1].start_sec == 4.0
    assert nodes[1].end_sec == 6.0
    assert set(nodes[1].matched_objects) == {"part", "robot_arm", "table"}


def test_infer_expected_objects_from_text() -> None:
    todo = TodoItem(
        id="todo-1",
        title="机器人将箱子搬运到工位",
        description="机械臂把零件和料箱移动到台面",
    )

    inferred = infer_expected_objects(todo)

    assert "robot" in inferred
    assert "box" in inferred
    assert "table" in inferred
    assert "part" in inferred


def test_load_todo_plan_keeps_explicit_expected_objects(tmp_path) -> None:
    todo_path = tmp_path / "todo.yaml"
    todo_path.write_text(
        "\n".join(
            [
                "items:",
                "  - id: todo-2",
                "    title: 机器人归位",
                "    expected_objects:",
                "      - robot_arm",
            ]
        ),
        encoding="utf-8",
    )

    plan = load_todo_plan(todo_path)

    assert plan.items[0].expected_objects == ["robot_arm"]


def test_todos_do_not_reuse_same_timeline_segment() -> None:
    observations = [
        make_observation(0.0, ["robot_arm"]),
        make_observation(1.0, ["robot_arm"]),
        make_observation(2.0, ["robot_arm"]),
        make_observation(3.0, ["robot_arm"]),
    ]
    todo_items = [
        TodoItem(
            id="step-1",
            title="步骤一",
            expected_objects=["robot_arm"],
            success_threshold=0.9,
            min_hits=2,
            min_duration_sec=2,
        ),
        TodoItem(
            id="step-2",
            title="步骤二",
            expected_objects=["robot_arm"],
            success_threshold=0.9,
            min_hits=2,
            min_duration_sec=2,
        ),
    ]

    timeline = build_timeline(observations, window_sec=1.0)
    nodes = match_todo_items(todo_items, timeline, observations)

    assert nodes[0].status == "completed"
    assert nodes[0].start_sec == 0.0
    assert nodes[0].end_sec == 4.0
    assert nodes[1].status == "missing"


def test_evidence_frames_do_not_leak_to_next_window() -> None:
    observations = [
        make_observation(0.0, ["robot_arm", "box"]),
        make_observation(1.0, ["robot_arm", "box"]),
        make_observation(2.0, ["robot_arm", "table"]),
    ]
    todo_items = [
        TodoItem(
            id="pickup",
            title="取料",
            expected_objects=["robot_arm", "box"],
            success_threshold=0.7,
            min_hits=2,
            min_duration_sec=2,
        )
    ]

    timeline = build_timeline(observations, window_sec=1.0)
    nodes = match_todo_items(todo_items, timeline, observations)

    assert nodes[0].evidence_timestamps_sec == [0.0, 1.0]


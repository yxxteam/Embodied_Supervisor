from edge.context.models import TodoNode
from edge.context.runtime import _build_state_frame, _node_completion_timestamp


def test_build_state_frame_uses_active_todo_node() -> None:
    nodes = [
        TodoNode(
            todo_id="todo-1",
            title="取料",
            module_title="01 取料",
            module_summary="机械臂抓取零件。",
            status="completed",
            start_sec=1.0,
            end_sec=3.0,
        ),
        TodoNode(
            todo_id="todo-2",
            title="装配",
            module_title="02 装配",
            module_summary="进行插装动作。",
            status="completed",
            start_sec=3.0,
            end_sec=5.0,
        ),
    ]

    frame = _build_state_frame(
        timestamp_sec=1.5,
        frame_index=15,
        duration_sec=10.0,
        nodes=nodes,
        metrics={"motion_norm": 0.7},
    )

    assert frame.current_task_node_id == "todo-1"
    assert frame.current_task_node_title == "01 取料"
    assert frame.state == "01 取料"


def test_build_state_frame_uses_next_todo_when_not_in_active_node() -> None:
    nodes = [
        TodoNode(
            todo_id="todo-1",
            title="取料",
            module_title="01 取料",
            status="completed",
            start_sec=1.0,
            end_sec=2.0,
        ),
        TodoNode(
            todo_id="todo-2",
            title="装配",
            module_title="02 装配",
            status="completed",
            start_sec=4.0,
            end_sec=6.0,
        ),
    ]

    frame = _build_state_frame(
        timestamp_sec=3.0,
        frame_index=30,
        duration_sec=10.0,
        nodes=nodes,
        metrics={},
    )

    assert frame.current_task_node_id is None
    assert frame.next_task_node_id == "todo-2"
    assert frame.state == "等待 02 装配"


def test_node_completion_timestamp_prefers_evidence_timestamp() -> None:
    node = TodoNode(
        todo_id="todo-3",
        title="完成",
        status="completed",
        start_sec=5.0,
        end_sec=7.0,
        evidence_timestamps_sec=[5.4, 6.2],
    )

    assert _node_completion_timestamp(node) == 6.2


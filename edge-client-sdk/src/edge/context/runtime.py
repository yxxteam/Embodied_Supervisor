from __future__ import annotations

import re
from datetime import datetime, timezone

from edge.context.models import TaskContextFrame, TodoNode


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _frame_id(session_id: str, frame_index: int) -> str:
    session_slug = re.sub(r"[^0-9a-zA-Z]+", "_", session_id).strip("_") or "session"
    return f"frame_{session_slug}_{frame_index:07d}"


def _node_completion_timestamp(node: TodoNode) -> float:
    if node.evidence_timestamps_sec:
        return float(node.evidence_timestamps_sec[-1])
    if node.end_sec is not None:
        return float(node.end_sec)
    if node.start_sec is not None:
        return float(node.start_sec)
    return 0.0


def _pick_active_node(timestamp_sec: float, nodes: list[TodoNode]) -> TodoNode | None:
    for node in nodes:
        if node.start_sec is None or node.end_sec is None:
            continue
        if node.start_sec <= timestamp_sec < node.end_sec:
            return node
    return None


def _pick_next_node(timestamp_sec: float, nodes: list[TodoNode]) -> TodoNode | None:
    for node in nodes:
        if node.start_sec is not None and node.start_sec > timestamp_sec:
            return node
    return None


def build_task_context_frame(
    timestamp_sec: float,
    frame_index: int,
    duration_sec: float,
    nodes: list[TodoNode],
    metrics: dict[str, float],
    *,
    session_id: str = "local-session",
    site_id: str = "default-site",
    robot_id: str = "default-robot",
    stream_id: str | None = None,
    media_object_ids: list[str] | None = None,
    observed_at: str | None = None,
) -> TaskContextFrame:
    progress = timestamp_sec / duration_sec if duration_sec > 0 else 0.0
    active = _pick_active_node(timestamp_sec, nodes)
    next_node = _pick_next_node(timestamp_sec, nodes)

    if active is not None:
        state = active.module_title or active.title
        message = active.module_summary or f"当前处于节点 {active.title}"
        current_task_node_id = active.todo_id
        current_task_node_title = active.module_title or active.title
        task_status = active.status
    else:
        current_task_node_id = None
        current_task_node_title = None
        task_status = None
        if next_node is not None:
            state = f"等待 {next_node.module_title or next_node.title}"
            message = f"即将进入节点 {next_node.module_title or next_node.title}"
        elif nodes:
            state = "终局校验"
            message = "todo 节点已结束，等待最终位置校验。"
        else:
            state = "解析中"
            message = "后台正在根据 todo 节点解析视频。"

    return TaskContextFrame(
        frame_id=_frame_id(session_id, frame_index),
        session_id=session_id,
        site_id=site_id,
        robot_id=robot_id,
        stream_id=stream_id,
        timestamp=observed_at or utc_now_iso(),
        frame_index=frame_index,
        state=state,
        message=message,
        progress=round(progress, 4),
        current_task_node_id=current_task_node_id,
        current_task_node_title=current_task_node_title,
        next_task_node_id=next_node.todo_id if next_node else None,
        next_task_node_title=(next_node.module_title or next_node.title) if next_node else None,
        task_status=task_status,
        metrics={key: round(float(value), 6) for key, value in metrics.items()},
        media_object_ids=list(media_object_ids or []),
    )


def _build_state_frame(
    timestamp_sec: float,
    frame_index: int,
    duration_sec: float,
    nodes: list[TodoNode],
    metrics: dict[str, float],
) -> TaskContextFrame:
    return build_task_context_frame(
        timestamp_sec=timestamp_sec,
        frame_index=frame_index,
        duration_sec=duration_sec,
        nodes=nodes,
        metrics=metrics,
    )

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from edge.context.models import TodoItem, TodoPlan


DEFAULT_OBJECT_ALIASES: dict[str, list[str]] = {
    "机器人": ["robot", "person", "robot_arm"],
    "机械臂": ["robot_arm", "robot", "person"],
    "手臂": ["robot_arm", "arm"],
    "料箱": ["box", "crate", "carton"],
    "箱子": ["box", "crate", "carton"],
    "箱": ["box", "crate", "carton"],
    "工位": ["table", "bench", "workstation"],
    "台面": ["table", "bench"],
    "零件": ["part", "component"],
    "工件": ["part", "component"],
    "托盘": ["tray", "plate", "bowl"],
    "相机": ["camera"],
    "屏幕": ["screen", "monitor", "tv"],
    "检测": ["screen", "monitor", "camera"],
    "夹具": ["fixture", "clamp"],
    "物料": ["box", "bottle", "cup", "package"],
    "工具": ["tool", "wrench", "screwdriver", "scissors"],
    "robot": ["robot", "robot_arm", "person"],
    "robot_arm": ["robot_arm", "robot"],
    "box": ["box", "crate", "carton"],
    "table": ["table", "bench", "workstation"],
    "part": ["part", "component"],
}


def normalize_label(value: str) -> str:
    normalized = value.strip().lower()
    normalized = normalized.replace("-", "_").replace(" ", "_")
    normalized = re.sub(r"[^0-9a-zA-Z_\u4e00-\u9fa5]+", "", normalized)
    return normalized


def dedupe_labels(labels: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for label in labels:
        normalized = normalize_label(label)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def infer_expected_objects(item: TodoItem) -> list[str]:
    inferred = list(item.expected_objects)
    text = " ".join([item.title, item.description, *item.keywords]).lower()
    for phrase, labels in DEFAULT_OBJECT_ALIASES.items():
        if phrase.lower() in text:
            inferred.extend(labels)
    return dedupe_labels(inferred)


def load_todo_plan(path: str | Path) -> TodoPlan:
    todo_path = Path(path)
    payload = todo_path.read_text(encoding="utf-8")

    if todo_path.suffix.lower() in {".yaml", ".yml"}:
        raw = yaml.safe_load(payload)
    else:
        raw = json.loads(payload)

    if isinstance(raw, list):
        raw = {"items": raw}

    plan = TodoPlan.model_validate(raw)
    normalized_items: list[TodoItem] = []
    for item in plan.items:
        explicit_expected_objects = dedupe_labels(item.expected_objects)
        expected_objects = explicit_expected_objects or infer_expected_objects(item)
        normalized_items.append(
            item.model_copy(
                update={
                    "expected_objects": expected_objects,
                    "keywords": dedupe_labels(item.keywords),
                }
            )
        )
    return plan.model_copy(update={"items": normalized_items})


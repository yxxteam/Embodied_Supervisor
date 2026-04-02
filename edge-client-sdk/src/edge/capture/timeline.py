from __future__ import annotations

from collections import defaultdict

from edge.context.models import FrameObservation, SignalObservation, TimelineWindow


def build_timeline(
    observations: list[FrameObservation],
    window_sec: float,
    top_k: int = 5,
) -> list[TimelineWindow]:
    if window_sec <= 0:
        raise ValueError("window_sec 必须大于 0")

    windows: dict[int, dict[str, int]] = {}
    bounds: dict[int, tuple[float, float]] = {}

    for observation in observations:
        window_index = int(observation.timestamp_sec // window_sec)
        bucket = windows.setdefault(window_index, {})
        for label, count in observation.label_counts.items():
            bucket[label] = bucket.get(label, 0) + count

        start_sec = round(window_index * window_sec, 3)
        end_sec = round(start_sec + window_sec, 3)
        bounds[window_index] = (start_sec, end_sec)

    timeline: list[TimelineWindow] = []
    for window_index in sorted(windows):
        label_counts = dict(sorted(windows[window_index].items(), key=lambda item: (-item[1], item[0])))
        dominant_objects = [label for label, _ in list(label_counts.items())[:top_k]]
        start_sec, end_sec = bounds[window_index]
        timeline.append(
            TimelineWindow(
                index=window_index,
                start_sec=start_sec,
                end_sec=end_sec,
                label_counts=label_counts,
                dominant_objects=dominant_objects,
            )
        )

    return timeline


def build_signal_timeline(
    observations: list[SignalObservation],
    window_sec: float = 1.0,
) -> list[TimelineWindow]:
    if window_sec <= 0:
        raise ValueError("window_sec 必须大于 0")

    sums: dict[int, dict[str, float]] = defaultdict(dict)
    counts: dict[int, int] = defaultdict(int)
    bounds: dict[int, tuple[float, float]] = {}

    for observation in observations:
        window_index = int(observation.timestamp_sec // window_sec)
        counts[window_index] += 1
        bucket = sums[window_index]
        for metric, value in observation.metrics.items():
            bucket[metric] = bucket.get(metric, 0.0) + value
        start_sec = round(window_index * window_sec, 3)
        bounds[window_index] = (start_sec, round(start_sec + window_sec, 3))

    windows: list[TimelineWindow] = []
    for window_index in sorted(sums):
        metric_means = {
            metric: round(total / counts[window_index], 6)
            for metric, total in sums[window_index].items()
        }
        states = [
            state
            for state, predicate in {
                "active": metric_means.get("motion_norm", 0.0) >= 0.7,
                "dual_arm": metric_means.get("dual_arm_activity", 0.0) >= 0.65,
                "centered": metric_means.get("yellow_center_norm", 0.0) >= 0.75,
                "stable": metric_means.get("motion_norm", 0.0) <= 0.4,
            }.items()
            if predicate
        ]
        start_sec, end_sec = bounds[window_index]
        windows.append(
            TimelineWindow(
                index=window_index,
                start_sec=start_sec,
                end_sec=end_sec,
                metrics=metric_means,
                states=states,
            )
        )
    return windows

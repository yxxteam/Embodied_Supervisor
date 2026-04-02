from __future__ import annotations

from pathlib import Path

from data.models import (
    DeviationEvent,
    EdgeEventEnvelope,
    InterventionTrigger,
    SessionRecord,
    SessionStreamSnapshot,
    TaskContextFrame,
    TaskNodeProgress,
)
from data.utils import read_json, write_json


class LocalSessionStreamCache:
    def __init__(self, root: str | Path, recent_limit: int = 24) -> None:
        self.root = Path(root)
        self.recent_limit = recent_limit

    def _path(self, session_id: str) -> Path:
        return self.root / "cache" / "streams" / f"{session_id}.json"

    def get(self, session: SessionRecord) -> SessionStreamSnapshot:
        payload = read_json(
            self._path(session.session_id),
            {
                "session": session.model_dump(mode="json"),
                "event_counts": {},
                "recent_events": [],
                "last_received_at": None,
            },
        )
        payload["session"] = session.model_dump(mode="json")
        return SessionStreamSnapshot.model_validate(payload)

    def apply_events(
        self,
        session: SessionRecord,
        events: list[EdgeEventEnvelope],
        *,
        received_at: str,
    ) -> SessionStreamSnapshot:
        snapshot = self.get(session)
        event_counts = dict(snapshot.event_counts)
        recent_events = list(snapshot.recent_events)

        latest_frame = snapshot.latest_frame
        latest_progress = snapshot.latest_progress
        latest_deviation = snapshot.latest_deviation
        latest_intervention = snapshot.latest_intervention

        for event in events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
            recent_events.append(event)
            if event.event_type == "task_context_frame":
                latest_frame = TaskContextFrame.model_validate(event.payload)
            elif event.event_type == "task_node_progress":
                latest_progress = TaskNodeProgress.model_validate(event.payload)
            elif event.event_type == "deviation_event":
                latest_deviation = DeviationEvent.model_validate(event.payload)
            elif event.event_type == "intervention_trigger":
                latest_intervention = InterventionTrigger.model_validate(event.payload)

        trimmed_events = recent_events[-self.recent_limit :]
        updated = SessionStreamSnapshot(
            session=session,
            latest_frame=latest_frame,
            latest_progress=latest_progress,
            latest_deviation=latest_deviation,
            latest_intervention=latest_intervention,
            event_counts=event_counts,
            recent_events=trimmed_events,
            last_received_at=received_at,
        )
        write_json(self._path(session.session_id), updated.model_dump(mode="json", exclude_none=True))
        return updated

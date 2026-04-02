from __future__ import annotations

from pathlib import Path

from data.cache.session_stream_cache import LocalSessionStreamCache
from data.models import (
    ArmCommandPacket,
    BatchEdgeEventsAcceptedResponse,
    EdgeEventEnvelope,
    SessionRecord,
    SessionSummary,
    SessionStreamSnapshot,
)
from data.utils import read_json, write_json


class LocalSessionRepository:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.sessions_path = self.root / "postgres" / "sessions.json"

    def create(self, session: SessionRecord) -> SessionRecord:
        sessions = self._load_all()
        sessions[session.session_id] = session
        self._save_all(sessions)
        return session

    def get(self, session_id: str) -> SessionRecord | None:
        return self._load_all().get(session_id)

    def update(self, session: SessionRecord) -> SessionRecord:
        sessions = self._load_all()
        sessions[session.session_id] = session
        self._save_all(sessions)
        return session

    def list(self) -> list[SessionRecord]:
        return sorted(self._load_all().values(), key=lambda item: item.created_at, reverse=True)

    def _load_all(self) -> dict[str, SessionRecord]:
        payload = read_json(self.sessions_path, {})
        return {key: SessionRecord.model_validate(value) for key, value in payload.items()}

    def _save_all(self, sessions: dict[str, SessionRecord]) -> None:
        write_json(
            self.sessions_path,
            {key: value.model_dump(mode="json", exclude_none=True) for key, value in sessions.items()},
        )


class LocalEventRepository:
    def __init__(
        self,
        root: str | Path,
        *,
        stream_cache: LocalSessionStreamCache,
    ) -> None:
        self.root = Path(root)
        self.stream_cache = stream_cache

    def append_events(
        self,
        session: SessionRecord,
        events: list[EdgeEventEnvelope],
        *,
        received_at: str,
    ) -> BatchEdgeEventsAcceptedResponse:
        path = self._path(session.session_id)
        existing = [EdgeEventEnvelope.model_validate(item) for item in read_json(path, [])]
        combined = existing + events
        write_json(path, [item.model_dump(mode="json", exclude_none=True) for item in combined])
        self.stream_cache.apply_events(session, events, received_at=received_at)
        return BatchEdgeEventsAcceptedResponse(
            session_id=session.session_id,
            accepted_count=len(events),
            rejected_count=0,
            received_at=received_at,
            rejected_event_ids=[],
        )

    def list_events(self, session_id: str) -> list[EdgeEventEnvelope]:
        path = self._path(session_id)
        return [EdgeEventEnvelope.model_validate(item) for item in read_json(path, [])]

    def get_stream(self, session: SessionRecord) -> SessionStreamSnapshot:
        return self.stream_cache.get(session)

    def get_summary(self, session: SessionRecord) -> SessionSummary:
        snapshot = self.get_stream(session)
        return SessionSummary(
            session=session,
            latest_frame=snapshot.latest_frame,
            latest_progress=snapshot.latest_progress,
            latest_deviation=snapshot.latest_deviation,
            latest_intervention=snapshot.latest_intervention,
            last_received_at=snapshot.last_received_at,
            total_events=sum(snapshot.event_counts.values()),
        )

    def _path(self, session_id: str) -> Path:
        return self.root / "postgres" / "events" / f"{session_id}.json"


class LocalArmCommandRepository:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def create(self, packet: ArmCommandPacket) -> ArmCommandPacket:
        packets = self.list(packet.session_id)
        packets.append(packet)
        self._save(packet.session_id, packets)
        return packet

    def list(self, session_id: str) -> list[ArmCommandPacket]:
        path = self._path(session_id)
        payload = read_json(path, [])
        return [ArmCommandPacket.model_validate(item) for item in payload]

    def get_latest(self, session_id: str) -> ArmCommandPacket | None:
        packets = self.list(session_id)
        if not packets:
            return None
        return packets[-1]

    def _save(self, session_id: str, packets: list[ArmCommandPacket]) -> None:
        write_json(
            self._path(session_id),
            [packet.model_dump(mode="json", exclude_none=True) for packet in packets],
        )

    def _path(self, session_id: str) -> Path:
        return self.root / "postgres" / "robot_command_packets" / f"{session_id}.json"

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from data.models import SessionRecord

from api.deps import RepositoryBundle
from api.schemas import SessionCreateRequest


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_session(payload: SessionCreateRequest) -> SessionRecord:
    now = utc_now_iso()
    return SessionRecord(
        session_id=f"sess_{uuid.uuid4().hex[:12]}",
        site_id=payload.site_id,
        robot_id=payload.robot_id,
        status="active",
        title=payload.title,
        objective=payload.objective,
        sop_plan_id=payload.sop_plan_id,
        started_at=now,
        created_at=now,
        updated_at=now,
        tags=payload.tags,
    )


def update_session_timestamp(session: SessionRecord, *, updated_at: str | None = None) -> SessionRecord:
    return session.model_copy(update={"updated_at": updated_at or utc_now_iso()})


def save_created_session(repositories: RepositoryBundle, payload: SessionCreateRequest) -> SessionRecord:
    session = build_session(payload)
    return repositories.session_repo.create(session)

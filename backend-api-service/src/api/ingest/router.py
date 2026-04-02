from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from data.models import BatchEdgeEventsAcceptedResponse, SessionRecord

from api.deps import RepositoryBundle, get_repositories
from api.schemas import BatchEdgeEventsRequest, SessionCreateRequest
from api.service import save_created_session, update_session_timestamp, utc_now_iso


router = APIRouter(tags=["ingest"])


@router.post("/sessions", response_model=SessionRecord, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreateRequest,
    repositories: RepositoryBundle = Depends(get_repositories),
) -> SessionRecord:
    return save_created_session(repositories, payload)


@router.get("/sessions/{session_id}", response_model=SessionRecord)
def get_session(
    session_id: str,
    repositories: RepositoryBundle = Depends(get_repositories),
) -> SessionRecord:
    session = repositories.session_repo.get(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session_not_found")
    return session


@router.post("/sessions/{session_id}/edge-events:batch", response_model=BatchEdgeEventsAcceptedResponse)
def batch_ingest_edge_events(
    session_id: str,
    payload: BatchEdgeEventsRequest,
    repositories: RepositoryBundle = Depends(get_repositories),
) -> BatchEdgeEventsAcceptedResponse:
    session = repositories.session_repo.get(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session_not_found")

    received_at = utc_now_iso()
    result = repositories.event_repo.append_events(session, payload.events, received_at=received_at)
    repositories.session_repo.update(update_session_timestamp(session, updated_at=received_at))
    return result

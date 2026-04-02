from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from data.models import SessionStreamSnapshot

from api.deps import RepositoryBundle, get_repositories


router = APIRouter(tags=["realtime"])


@router.get("/sessions/{session_id}/stream", response_model=SessionStreamSnapshot)
def get_session_stream(
    session_id: str,
    repositories: RepositoryBundle = Depends(get_repositories),
) -> SessionStreamSnapshot:
    session = repositories.session_repo.get(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session_not_found")
    return repositories.event_repo.get_stream(session)

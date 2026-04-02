from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fastapi import Request

from data import (
    InMemoryEmbeddingRepository,
    LocalArmCommandRepository,
    LocalEventRepository,
    LocalMediaObjectStore,
    LocalSessionRepository,
    LocalSessionStreamCache,
)


@dataclass
class RepositoryBundle:
    session_repo: LocalSessionRepository
    event_repo: LocalEventRepository
    robot_command_repo: LocalArmCommandRepository
    stream_cache: LocalSessionStreamCache
    media_store: LocalMediaObjectStore
    embedding_repo: InMemoryEmbeddingRepository


def build_repositories(root: str | Path) -> RepositoryBundle:
    stream_cache = LocalSessionStreamCache(root)
    return RepositoryBundle(
        session_repo=LocalSessionRepository(root),
        event_repo=LocalEventRepository(root, stream_cache=stream_cache),
        robot_command_repo=LocalArmCommandRepository(root),
        stream_cache=stream_cache,
        media_store=LocalMediaObjectStore(root),
        embedding_repo=InMemoryEmbeddingRepository(),
    )


def get_repositories(request: Request) -> RepositoryBundle:
    return request.app.state.repositories

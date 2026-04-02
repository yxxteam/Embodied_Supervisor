from __future__ import annotations

from typing import Any


class InMemoryEmbeddingRepository:
    def __init__(self) -> None:
        self._items: list[dict[str, Any]] = []

    def add(self, item_id: str, vector: list[float], metadata: dict[str, Any] | None = None) -> None:
        self._items.append({"item_id": item_id, "vector": vector, "metadata": metadata or {}})

    def search(self, query_vector: list[float], limit: int = 5) -> list[dict[str, Any]]:
        def score(item: dict[str, Any]) -> float:
            item_vector = item["vector"]
            size = min(len(query_vector), len(item_vector))
            return sum(query_vector[index] * item_vector[index] for index in range(size))

        ranked = sorted(self._items, key=score, reverse=True)
        return ranked[:limit]

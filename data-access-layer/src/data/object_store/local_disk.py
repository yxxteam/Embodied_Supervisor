from __future__ import annotations

from pathlib import Path


class LocalMediaObjectStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def write_bytes(self, object_id: str, payload: bytes, suffix: str = ".bin") -> str:
        path = self.root / "object_store" / f"{object_id}{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return str(path)

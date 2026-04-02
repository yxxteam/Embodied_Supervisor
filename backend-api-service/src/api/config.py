from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Embodied Supervisor Control Plane"
    api_prefix: str = "/api/v1"
    data_root: Path


def load_settings(*, data_root: str | Path | None = None) -> Settings:
    default_root = Path(__file__).resolve().parents[2] / "runtime" / "state"
    resolved = Path(data_root) if data_root is not None else Path(os.getenv("EMBODIED_DATA_ROOT", default_root))
    return Settings(data_root=resolved)

"""Схемы фоновых задач."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.enums import JobStatus


class JobResponse(BaseModel):
    id: uuid.UUID
    task_name: str
    status: JobStatus
    status_label: str
    progress: int
    started_at: datetime | None
    finished_at: datetime | None
    result: dict[str, Any]
    error_message: str | None
    retries: int
    created_at: datetime

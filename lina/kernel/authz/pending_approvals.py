"""In-memory store for pending human-in-the-loop approval requests."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from kernel.entities.base import utcnow
from kernel.ports.authz import AuthorizationRequest


@dataclass(slots=True)
class PendingApproval:
    token: str
    request: AuthorizationRequest
    created_at: datetime
    resolved: bool = False
    approved: bool | None = None
    approved_by: str | None = None
    resolved_at: datetime | None = None


class PendingApprovalStore:
    """Thread-safe (single-event-loop) registry of outstanding approval requests."""

    def __init__(self) -> None:
        self._store: dict[str, PendingApproval] = {}
        self._lock = asyncio.Lock()

    async def create(self, request: AuthorizationRequest) -> PendingApproval:
        async with self._lock:
            token = str(uuid.uuid4())
            entry = PendingApproval(token=token, request=request, created_at=utcnow())
            self._store[token] = entry
            return entry

    async def resolve(
        self, token: str, *, approved: bool, approved_by: str
    ) -> PendingApproval | None:
        async with self._lock:
            entry = self._store.get(token)
            if entry is None or entry.resolved:
                return None
            entry.resolved = True
            entry.approved = approved
            entry.approved_by = approved_by
            entry.resolved_at = utcnow()
            return entry

    async def get(self, token: str) -> PendingApproval | None:
        async with self._lock:
            return self._store.get(token)

    async def list_pending(self) -> list[PendingApproval]:
        async with self._lock:
            return [e for e in self._store.values() if not e.resolved]
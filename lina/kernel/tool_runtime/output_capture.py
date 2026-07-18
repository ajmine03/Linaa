"""Bounded output capture — prevents runaway tool output from exhausting memory."""

from __future__ import annotations

_MAX_CAPTURE_BYTES = 2 * 1024 * 1024  # 2 MiB per stream


class BoundedBuffer:
    """Accumulates bytes up to a cap, then discards further input while
    tracking that truncation occurred.
    """

    def __init__(self, max_bytes: int = _MAX_CAPTURE_BYTES) -> None:
        self._max_bytes = max_bytes
        self._chunks: list[bytes] = []
        self._size = 0
        self._truncated = False

    def write(self, chunk: bytes) -> None:
        if self._size >= self._max_bytes:
            self._truncated = True
            return
        remaining = self._max_bytes - self._size
        if len(chunk) > remaining:
            chunk = chunk[:remaining]
            self._truncated = True
        self._chunks.append(chunk)
        self._size += len(chunk)

    def getvalue(self) -> str:
        return b"".join(self._chunks).decode("utf-8", errors="replace")

    @property
    def truncated(self) -> bool:
        return self._truncated
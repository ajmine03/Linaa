"""Deterministic, config-consistent naming for ChromaDB collections."""

from __future__ import annotations

import re

_SAFE_PATTERN = re.compile(r"[^a-zA-Z0-9_-]")


def build_collection_name(prefix: str, collection: str) -> str:
    """Sanitize and namespace a logical collection name for ChromaDB.

    ChromaDB collection names must be 3-63 chars, alphanumeric/underscore/
    hyphen only, start/end with alphanumeric. We enforce that here so
    callers can pass human-friendly names like 'engagement:abc123:findings'.
    """
    raw = f"{prefix}_{collection}"
    sanitized = _SAFE_PATTERN.sub("_", raw)
    sanitized = sanitized.strip("_-")
    if len(sanitized) < 3:
        sanitized = sanitized.ljust(3, "0")
    return sanitized[:63]
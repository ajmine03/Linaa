"""Glob-style pattern matching for event-type subscriptions.

Supports:
    'finding.*'      -> matches 'finding.created', 'finding.status_changed'
    '*'               -> matches everything
    'finding.created' -> exact match only
"""

from __future__ import annotations

import fnmatch
from functools import lru_cache


@lru_cache(maxsize=512)
def matches(event_type: str, pattern: str) -> bool:
    """Return True if `event_type` matches `pattern` (fnmatch-style glob)."""
    if pattern == "*":
        return True
    return fnmatch.fnmatchcase(event_type, pattern)
"""Scope matching engine: resolves whether a target identifier falls within
an Engagement's authorized ScopeRules.

Supports three pattern families, auto-detected from the pattern string:
  - CIDR notation      e.g. '192.168.56.0/24', '10.0.0.0/8'
  - Exact IP/host       e.g. '192.168.56.10'
  - Domain glob          e.g. '*.example.com', 'app.example.com'
  - URL prefix           e.g. 'https://target.example.com/*'
"""

from __future__ import annotations

import fnmatch
import ipaddress
from dataclasses import dataclass
from urllib.parse import urlparse

import structlog

from kernel.entities.engagement import ScopeRule

logger = structlog.get_logger(__name__)


@dataclass(slots=True, frozen=True)
class ScopeMatchResult:
    matched: bool
    matched_rule: ScopeRule | None
    reason: str


def _try_parse_network(pattern: str) -> ipaddress.IPv4Network | ipaddress.IPv6Network | None:
    try:
        return ipaddress.ip_network(pattern, strict=False)
    except ValueError:
        return None


def _try_parse_ip(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(value)
    except ValueError:
        return None


def _extract_host(identifier: str) -> str:
    """Normalize a target identifier that might be a bare host, or a URL, into a host string."""
    if "://" in identifier:
        parsed = urlparse(identifier)
        return parsed.hostname or identifier
    return identifier.split(":")[0].strip("/")


def _single_rule_matches(identifier: str, pattern: str) -> bool:
    network = _try_parse_network(pattern)
    if network is not None:
        host = _extract_host(identifier)
        ip = _try_parse_ip(host)
        if ip is None:
            return False
        return ip in network

    if "://" in pattern or pattern.endswith("/*"):
        # URL-prefix style rule
        prefix = pattern[:-1] if pattern.endswith("*") else pattern
        return identifier.startswith(prefix)

    host = _extract_host(identifier)
    return fnmatch.fnmatchcase(host.lower(), pattern.lower())


class ScopeMatcher:
    """Stateless matcher evaluating a target identifier against a rule set.

    Exclusion rules take precedence: if any exclusion rule matches, the
    target is out of scope regardless of inclusion matches.
    """

    def evaluate(self, identifier: str, rules: list[ScopeRule]) -> ScopeMatchResult:
        if not rules:
            return ScopeMatchResult(
                matched=False, matched_rule=None, reason="No scope rules defined."
            )

        exclusions = [r for r in rules if r.is_exclusion]
        inclusions = [r for r in rules if not r.is_exclusion]

        for rule in exclusions:
            if self._safe_match(identifier, rule.pattern):
                return ScopeMatchResult(
                    matched=False,
                    matched_rule=rule,
                    reason=f"Excluded by rule '{rule.pattern}'.",
                )

        for rule in inclusions:
            if self._safe_match(identifier, rule.pattern):
                return ScopeMatchResult(
                    matched=True,
                    matched_rule=rule,
                    reason=f"Matched inclusion rule '{rule.pattern}'.",
                )

        return ScopeMatchResult(
            matched=False,
            matched_rule=None,
            reason="No inclusion rule matched target identifier.",
        )

    @staticmethod
    def _safe_match(identifier: str, pattern: str) -> bool:
        try:
            return _single_rule_matches(identifier, pattern)
        except Exception:  # noqa: BLE001 — malformed pattern must never crash authz
            logger.warning("scope_matcher.pattern_error", pattern=pattern, identifier=identifier)
            return False
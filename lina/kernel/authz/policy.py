"""Risk-based approval policy: decides which risk levels require human sign-off."""

from __future__ import annotations

from dataclasses import dataclass

from kernel.entities.enums import ToolRiskLevel


@dataclass(slots=True, frozen=True)
class RiskPolicy:
    """Configurable mapping of risk level -> whether human approval is mandatory.

    Defaults are deliberately conservative: only READ_ONLY and LOW run
    without a human in the loop. This can be tightened further via config
    but never loosened below these defaults by plugin code.
    """

    auto_approve_levels: frozenset[ToolRiskLevel] = frozenset(
        {ToolRiskLevel.READ_ONLY, ToolRiskLevel.LOW}
    )

    def requires_human_approval(self, risk_level: ToolRiskLevel) -> bool:
        return risk_level not in self.auto_approve_levels

    def is_read_only(self, risk_level: ToolRiskLevel) -> bool:
        return risk_level == ToolRiskLevel.READ_ONLY
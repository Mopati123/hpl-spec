from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..context import RuntimeContext


@dataclass(frozen=True)
class StabilizerDecision:
    ok: bool
    refusal_type: Optional[str]
    reasons: List[str]
    required_roles: List[str]


def evaluate_stabilizer(
    action: str,
    endpoint: str,
    ctx: RuntimeContext,
    net_policy: Optional[Dict[str, object]],
) -> StabilizerDecision:
    reasons: List[str] = []
    if not ctx.net_enabled:
        reasons.append("NET not enabled")
        return StabilizerDecision(False, "NetGuardNotEnabled", reasons, [])
    if net_policy is None:
        reasons.append("net_policy missing")
        return StabilizerDecision(False, "NetPermissionDenied", reasons, [])
    if endpoint:
        allowlist = {
            str(item)
            for item in net_policy.get("net_endpoints_allowlist", [])
            if str(item).strip()
        }
        if allowlist and endpoint not in allowlist:
            reasons.append(f"endpoint not allowed: {endpoint}")
            return StabilizerDecision(False, "NetEndpointNotAllowed", reasons, [])
    required_roles = ["net_request_log", "net_response_log", "net_session_manifest", "redaction_report"]
    return StabilizerDecision(True, None, [], required_roles)

from __future__ import annotations

from exonware.xwaction import XWAction
from exonware.xwaction.defs import ActionSecurityLevel


def test_critical_actions_default_to_non_http_exposure() -> None:
    @XWAction(operationId="critical_action", profile="endpoint", security_level=ActionSecurityLevel.CRITICAL)
    def critical_action() -> dict[str, str]:
        return {"ok": "yes"}

    assert critical_action.xwaction.security_level == ActionSecurityLevel.CRITICAL
    assert critical_action.xwaction.expose_http is False


def test_explicit_http_exposure_override_is_honored() -> None:
    @XWAction(operationId="high_action", profile="endpoint", security_level="high", expose_http=True)
    def high_action() -> dict[str, str]:
        return {"ok": "yes"}

    assert high_action.xwaction.security_level == ActionSecurityLevel.HIGH
    assert high_action.xwaction.expose_http is True

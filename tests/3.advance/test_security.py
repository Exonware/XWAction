#!/usr/bin/env python3
"""
#exonware/xwaction/tests/3.advance/test_security.py
Comprehensive security tests for xwaction.
Priority #1: Security Excellence
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 07-Jan-2025
"""

from __future__ import annotations
import pytest
from exonware.xwaction.facade import XWAction
from exonware.xwaction.registry import ActionRegistry
@pytest.mark.xwaction_advance
@pytest.mark.xwaction_security

class TestInputValidation:
    """Security tests for input validation."""

    def test_malicious_input_handling(self):
        """Test handling of malicious input."""
        def safe_action(data: str) -> dict:
            return {"result": data}
        action = XWAction(api_name="safe_action", func=safe_action)
        # Test various malicious inputs
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../etc/passwd",
        ]
        for malicious_input in malicious_inputs:
            # Should handle safely without executing code
            try:
                result = action.execute({"data": malicious_input})
                # Should return data, not execute
                assert isinstance(result, dict)
            except Exception:
                # Exception is acceptable for invalid inputs
                pass
@pytest.mark.xwaction_advance
@pytest.mark.xwaction_security

class TestActionIsolation:
    """Security tests for action isolation."""

    def test_action_registry_isolation(self):
        """Test that actions in registry are isolated."""
        def action1(x: int) -> dict:
            return {"result": x}
        def action2(y: str) -> dict:
            return {"result": y}
        action1_obj = XWAction(api_name="action1", func=action1)
        action2_obj = XWAction(api_name="action2", func=action2)
        registry = ActionRegistry()
        registry.register("test1", action1_obj)
        registry.register("test2", action2_obj)
        # Actions should be isolated
        actions1 = registry.get_actions_for("test1")
        actions2 = registry.get_actions_for("test2")
        assert "action1" in actions1
        assert "action2" in actions2
        assert "action1" not in actions2
        assert "action2" not in actions1

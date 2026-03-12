#!/usr/bin/env python3
"""
#exonware/xwaction/tests/3.advance/test_performance.py
Comprehensive performance benchmarks for xwaction.
Priority #4: Performance Excellence
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 07-Jan-2025
"""

from __future__ import annotations
import pytest
import time
from exonware.xwaction.facade import XWAction
from exonware.xwaction.registry import ActionRegistry
from exonware.xwaction.core.openapi import OpenAPIGenerator
from exonware.xwaction.context import ActionContext
@pytest.mark.xwaction_advance
@pytest.mark.xwaction_performance

class TestActionExecutionPerformance:
    """Performance tests for action execution."""

    def test_action_execution_performance(self):
        """Test action execution performance."""
        def fast_action(x: int) -> dict:
            return {"result": x * 2}
        action = XWAction(api_name="fast_action", func=fast_action)
        # Test execution performance
        context = ActionContext(actor="test", source="test")
        start = time.time()
        for i in range(1000):
            result = action.execute(context, None, x=i)
        elapsed = time.time() - start
        # 1000 executions should complete in < 1 second
        assert elapsed < 1.0, f"Action execution too slow: {elapsed:.3f}s for 1000 executions"

    def test_action_registry_lookup_performance(self):
        """Test action registry lookup performance."""
        def test_action(x: int) -> dict:
            return {"result": x}
        action = XWAction(api_name="test_action", func=test_action)
        registry = ActionRegistry()
        registry.register("test", action)
        # Test lookup performance
        start = time.time()
        for _ in range(1000):
            actions = registry.get_actions_for("test")
            found = actions.get("test_action")
            assert found is not None
        elapsed = time.time() - start
        # 1000 lookups should complete in < 0.1 seconds
        assert elapsed < 0.1, f"Registry lookup too slow: {elapsed:.3f}s for 1000 lookups"
@pytest.mark.xwaction_advance
@pytest.mark.xwaction_performance

class TestOpenAPIGenerationPerformance:
    """Performance tests for OpenAPI generation."""

    def test_openapi_spec_generation_performance(self):
        """Test OpenAPI spec generation performance."""
        def test_action(x: int, y: str) -> dict:
            return {"result": f"{x}_{y}"}
        action = XWAction(api_name="test_action", func=test_action)
        generator = OpenAPIGenerator()
        # Test generation performance
        start = time.time()
        for _ in range(100):
            spec = generator.generate_spec(action)
        elapsed = time.time() - start
        # 100 generations should complete in < 1 second
        assert elapsed < 1.0, f"OpenAPI generation too slow: {elapsed:.3f}s for 100 generations"

    def test_openapi_export_performance(self):
        """Test OpenAPI export performance."""
        def test_action(x: int) -> dict:
            return {"result": x}
        action = XWAction(api_name="test_action", func=test_action)
        registry = ActionRegistry()
        registry.register("test", action)
        # Test export performance
        start = time.time()
        spec = registry.export_openapi_spec()
        elapsed = time.time() - start
        # Export should complete in < 0.5 seconds
        assert elapsed < 0.5, f"OpenAPI export too slow: {elapsed:.3f}s"

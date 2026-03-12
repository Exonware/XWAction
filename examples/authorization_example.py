#!/usr/bin/env python3
"""
Example: Using IActionAuthorizer interface for authorization.
This example shows how to:
1. Use a mock authorizer for testing
2. Set authorizer on an action
3. Use the authorization interface pattern
"""

from exonware.xwaction import XWAction, ActionProfile, ActionContext
from xwaction.test_auth_helpers import MockAdminAuthorizer, MockRoleBasedAuthorizer
# Example 1: Using MockAdminAuthorizer for testing
@XWAction(operationId="test_action", profile=ActionProfile.COMMAND, roles=["admin"])


def test_action(param: str) -> str:
    """Test action that requires admin role."""
    return f"Action executed with param: {param}"


def example_mock_admin():
    """Example: Use mock admin authorizer for testing."""
    # Get the action instance
    action = test_action.xwaction
    # Set mock authorizer that always allows
    action.set_authorizer(MockAdminAuthorizer())
    # Create context (no roles needed, authorizer handles it)
    context = ActionContext(actor="test_user", source="test")
    # Check permissions (will pass because MockAdminAuthorizer allows)
    has_permission = action.check_permissions(context)
    print(f"Has permission: {has_permission}")  # True


def example_role_based():
    """Example: Use role-based authorizer."""
    action = test_action.xwaction
    # Set role-based authorizer
    action.set_authorizer(MockRoleBasedAuthorizer())
    # Context with admin role
    context_with_admin = ActionContext(
        actor="admin_user",
        source="test",
        metadata={"roles": ["admin"]}
    )
    # Context without admin role
    context_without_admin = ActionContext(
        actor="regular_user",
        source="test",
        metadata={"roles": ["user"]}
    )
    print(f"Admin user has permission: {action.check_permissions(context_with_admin)}")  # True
    print(f"Regular user has permission: {action.check_permissions(context_without_admin)}")  # False
if __name__ == "__main__":
    print("Example 1: Mock Admin Authorizer")
    example_mock_admin()
    print("\nExample 2: Role-Based Authorizer")
    example_role_based()

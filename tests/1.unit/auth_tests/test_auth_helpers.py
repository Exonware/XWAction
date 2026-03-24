#!/usr/bin/env python3
"""
Test helpers for XWAction authorization.
Provides mock authorizers for testing.
"""

from exonware.xwaction import IActionAuthorizer, AuthzDecision, ActionContext, IAction


class MockAdminAuthorizer:
    """
    Mock authorizer that always allows admin access.
    Useful for testing when you need to bypass authorization checks.
    """

    def authorize(self, action: IAction, context: ActionContext) -> AuthzDecision:
        """
        Authorize action - always allows for testing.
        Checks for test user 'muhdashe' and grants admin access.
        Args:
            action: The action to authorize
            context: Execution context
        Returns:
            AuthzDecision with allowed=True and admin roles
        """
        # Check for test user 'muhdashe' in context
        user_id = context.metadata.get('user_id') or context.metadata.get('telegram_username') or context.actor
        if user_id and 'muhdashe' in str(user_id).lower():
            return AuthzDecision(
                allowed=True,
                subject="muhdashe",
                roles=["admin", "owner"],
                reason="Test mode: muhdashe admin access granted"
            )
        return AuthzDecision(
            allowed=True,
            subject=context.actor or "test_admin",
            roles=["admin", "owner"],
            reason="Test mode: admin access granted"
        )


class MockRoleBasedAuthorizer:
    """
    Mock authorizer that checks roles from context metadata.
    Allows testing role-based authorization without full xwauth setup.
    """

    def __init__(self, default_roles: list[str] | None = None):
        """
        Initialize mock role-based authorizer.
        Args:
            default_roles: Default roles to use if context doesn't have roles
        """
        self._default_roles = default_roles or []

    def authorize(self, action: IAction, context: ActionContext) -> AuthzDecision:
        """
        Authorize action based on roles in context.
        Args:
            action: The action to authorize
            context: Execution context with roles in metadata
        Returns:
            AuthzDecision based on role matching
        """
        # Get roles from context or use defaults
        user_roles = context.metadata.get("roles", []) or self._default_roles
        required_roles = action.roles
        # If no roles required, allow
        if not required_roles or "*" in required_roles:
            return AuthzDecision(
                allowed=True,
                subject=context.actor or "anonymous",
                roles=user_roles,
                reason="No roles required"
            )
        # Check if user has any required role
        has_role = any(role in user_roles for role in required_roles)
        return AuthzDecision(
            allowed=has_role,
            subject=context.actor or "anonymous",
            roles=user_roles,
            reason="Access granted" if has_role else f"Missing required roles: {required_roles}"
        )


class MockDenyAuthorizer:
    """
    Mock authorizer that always denies access.
    Useful for testing denial scenarios.
    """

    def authorize(self, action: IAction, context: ActionContext) -> AuthzDecision:
        """
        Authorize action - always denies for testing.
        Args:
            action: The action to authorize
            context: Execution context
        Returns:
            AuthzDecision with allowed=False
        """
        return AuthzDecision(
            allowed=False,
            subject=context.actor or "anonymous",
            roles=context.metadata.get("roles", []),
            reason="Test mode: access denied"
        )


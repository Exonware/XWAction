#exonware/xwaction/handlers/contracts.py
"""
XWAction Handler Contracts
Interfaces for action handler implementations.
"""

from typing import Any, Protocol, runtime_checkable
from ..context import ActionContext
from ..defs import ActionHandlerPhase
@runtime_checkable


class IActionHandler(Protocol):
    """
    Action Handler Interface
    Defines the contract that all action handlers must implement.
    """
    @property

    def name(self) -> str:
        """Get the name of this action handler."""
        ...
    @property

    def priority(self) -> int:
        """Get the priority of this action handler."""
        ...
    @property

    def supported_phases(self) -> set[ActionHandlerPhase]:
        """Get the phases this action handler supports."""
        ...
    @property

    def async_enabled(self) -> bool:
        """Whether this action handler supports async execution."""
        ...

    def before_execution(self, action: Any, context: ActionContext, **kwargs) -> bool:
        """Execute before action execution."""
        ...

    def after_execution(self, action: Any, context: ActionContext, result: Any) -> bool:
        """Execute after successful action execution."""
        ...

    def on_error(self, action: Any, context: ActionContext, error: Exception) -> bool:
        """Execute when an error occurs during action execution."""
        ...

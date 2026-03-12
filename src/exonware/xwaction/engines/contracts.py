#exonware/xwaction/engines/contracts.py
"""
XWAction Engine Contracts
Interfaces for action engine implementations.
"""

from __future__ import annotations
from typing import Any, TYPE_CHECKING, Protocol, runtime_checkable
from ..context import ActionContext, ActionResult
from ..defs import ActionProfile
if TYPE_CHECKING:
    from .defs import ActionEngineType
@runtime_checkable


class IActionEngine(Protocol):
    """
    Action Engine Interface
    Defines the contract that all action engines must implement.
    """
    @property

    def engine_type(self) -> ActionEngineType:
        """Get the type of this action engine."""
        ...
    @property

    def name(self) -> str:
        """Get the name of this action engine."""
        ...
    @property

    def priority(self) -> int:
        """Get the priority of this action engine."""
        ...

    def can_execute(self, action_profile: ActionProfile, **kwargs) -> bool:
        """Check if this action engine can execute the given action."""
        ...

    def execute(self, action: Any, context: ActionContext, 
                instance: Any, **kwargs) -> ActionResult:
        """Execute an action using this action engine."""
        ...

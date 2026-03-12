#exonware/xwaction/handlers/defs.py
"""
XWAction Handler Definitions
Type definitions, constants, and dataclasses for handlers.
"""

from typing import Any, Optional
from dataclasses import dataclass
@dataclass


class ActionHandlerConfig:
    """Configuration for an action handler."""
    name: str
    enabled: bool = True
    async_enabled: bool = False
    priority: int = 0
    cache_ttl: int = 0
    config: Optional[dict[str, Any]] = None

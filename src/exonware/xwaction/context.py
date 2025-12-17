#exonware/xwaction/context.py
"""
XWAction Context Module
Execution context and result management.
"""

from typing import Any, Dict, Optional
from datetime import datetime
import uuid


class ActionContext:
    """Execution context for actions."""
    
    def __init__(self, 
                 actor: Optional[str] = None,
                 source: str = "internal",
                 trace_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.actor = actor  # Who's executing
        self.timestamp = datetime.now()  # When
        self.source = source  # Where from (api, cli, internal)
        self.trace_id = trace_id or self._generate_trace_id()
        self.metadata = metadata or {}
        self.start_time = None  # Set by monitoring handlers
        self.workflow_state = None  # Set by workflow handlers
    
    @staticmethod
    def _generate_trace_id() -> str:
        """Generate a simple trace ID."""
        return str(uuid.uuid4())
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to the context."""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata from the context."""
        return self.metadata.get(key, default)
    
    def has_metadata(self, key: str) -> bool:
        """Check if metadata key exists."""
        return key in self.metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "actor": self.actor,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "trace_id": self.trace_id,
            "metadata": self.metadata,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "workflow_state": self.workflow_state
        }


class ActionResult:
    """Standardized result wrapper."""
    
    def __init__(self, 
                 success: bool,
                 data: Any = None,
                 error: Optional[str] = None,
                 duration: float = 0.0,
                 metadata: Optional[Dict[str, Any]] = None):
        self.success = success
        self.data = data
        self.error = error
        self.duration = duration  # Execution time in seconds
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to the result."""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata from the result."""
        return self.metadata.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "duration": self.duration,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def success(cls, data: Any = None, duration: float = 0.0, **metadata) -> 'ActionResult':
        """Create a successful result."""
        return cls(success=True, data=data, duration=duration, metadata=metadata)
    
    @classmethod
    def failure(cls, error: str, duration: float = 0.0, **metadata) -> 'ActionResult':
        """Create a failed result."""
        return cls(success=False, error=error, duration=duration, metadata=metadata)


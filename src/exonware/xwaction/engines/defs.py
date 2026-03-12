#exonware/xwaction/engines/defs.py
"""
XWAction Engine Definitions
Type definitions, constants, and dataclasses for engines.
"""

from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass


class ActionEngineType(Enum):
    """Types of action engines for different execution contexts."""
    EXECUTION = "execution"      # WHERE to run (fastapi, celery, prefect, native)
    STORAGE = "storage"          # WHERE to persist (redis, postgres, mongodb, s3)
    COMMUNICATION = "communication"  # HOW to communicate (http, grpc, websocket, kafka)
    PROCESSING = "processing"    # HOW to process (ray, dask, spark, gpu)
@dataclass


class ActionEngineConfig:
    """Configuration for an action engine."""
    name: str
    engine_type: ActionEngineType
    priority: int = 0  # Higher priority engines are used first
    enabled: bool = True
    config: Optional[dict[str, Any]] = None

#exonware/xwaction/defs.py
"""
XWAction Definitions
Enums and constants for action system.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field


class ActionProfile(Enum):
    """Pre-configured action profiles with smart defaults."""
    ACTION = "action"       # Default: general purpose action
    QUERY = "query"         # Read-only operations with caching
    COMMAND = "command"     # State-changing operations with audit
    TASK = "task"           # Background/scheduled operations
    WORKFLOW = "workflow"   # Multi-step operations with rollback
    ENDPOINT = "endpoint"   # API endpoint operations


class ActionHandlerPhase(Enum):
    """Execution phases for action handlers."""
    BEFORE = "before"       # Before execution
    AFTER = "after"         # After execution
    ERROR = "error"         # On error
    FINALLY = "finally"     # Finally (always executed)


@dataclass
class ProfileConfig:
    """Configuration for action profiles."""
    readonly: bool = False
    cache_ttl: int = 0
    audit: bool = False
    background: bool = False
    rate_limit: Optional[str] = None
    security: Union[str, List[str]] = "default"
    retry_attempts: int = 0
    timeout: Optional[float] = None
    engine: Union[str, List[str]] = "native"


# Built-in profile configurations
PROFILE_CONFIGS: Dict[ActionProfile, ProfileConfig] = {
    ActionProfile.ACTION: ProfileConfig(),
    ActionProfile.QUERY: ProfileConfig(
        readonly=True,
        cache_ttl=60,
        rate_limit="1000/hour",
        security="api_key",
        engine="fastapi"
    ),
    ActionProfile.COMMAND: ProfileConfig(
        audit=True,
        rate_limit="100/hour", 
        security=["api_key", "roles"],
        retry_attempts=1,
        engine="fastapi"
    ),
    ActionProfile.TASK: ProfileConfig(
        background=True,
        audit=True,
        security="internal",
        retry_attempts=3,
        timeout=3600.0,
        engine="celery"
    ),
    ActionProfile.WORKFLOW: ProfileConfig(
        audit=True,
        retry_attempts=3,
        timeout=300.0,
        security="oauth2",
        engine="prefect"
    ),
    ActionProfile.ENDPOINT: ProfileConfig(
        audit=True,
        rate_limit="500/hour",
        security="oauth2",
        engine="fastapi"
    )
}


@dataclass
class WorkflowStep:
    """Configuration for workflow steps."""
    name: str
    timeout: Optional[float] = None
    retry: int = 0
    async_execution: bool = False
    rollback_func: Optional[str] = None


@dataclass
class MonitoringConfig:
    """Monitoring and metrics configuration."""
    metrics: List[str] = field(default_factory=lambda: ["duration"])
    alerts: Dict[str, str] = field(default_factory=dict)
    threshold: Dict[str, str] = field(default_factory=dict)


@dataclass
class SecurityConfig:
    """Security configuration for actions."""
    schemes: Union[str, List[str], Dict[str, List[str]]] = "default"
    rate_limit: Optional[str] = None
    audit: bool = False
    mfa_required: bool = False


@dataclass
class ContractConfig:
    """Contract validation configuration."""
    input: Dict[str, str] = field(default_factory=dict)
    output: Dict[str, str] = field(default_factory=dict)
    strict: bool = True


def get_profile_config(profile: Union[str, ActionProfile]) -> ProfileConfig:
    """Get configuration for a profile."""
    if isinstance(profile, str):
        try:
            profile = ActionProfile(profile)
        except ValueError:
            profile = ActionProfile.ACTION
    
    return PROFILE_CONFIGS.get(profile, ProfileConfig())


def register_profile(name: str, config: ProfileConfig):
    """Register a new action profile."""
    if isinstance(name, str):
        try:
            profile_enum = ActionProfile(name)
            PROFILE_CONFIGS[profile_enum] = config
        except ValueError:
            pass  # Invalid profile name


def get_all_profiles() -> Dict[str, ProfileConfig]:
    """Get all registered profiles."""
    return {profile.value: config for profile, config in PROFILE_CONFIGS.items()}


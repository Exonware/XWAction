#!/usr/bin/env python3
"""
🎯 xAction Profiles Module
Action profiles and configuration management.
"""

from typing import Any, Dict, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, field

from src.xlib.xsystem import get_logger

logger = get_logger(__name__)


class ActionProfile(Enum):
    """Pre-configured action profiles with smart defaults."""
    ACTION = "action"       # Default: general purpose action
    QUERY = "query"         # Read-only operations with caching
    COMMAND = "command"     # State-changing operations with audit
    TASK = "task"           # Background/scheduled operations
    WORKFLOW = "workflow"   # Multi-step operations with rollback
    ENDPOINT = "endpoint"   # API endpoint operations


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
PROFILE_CONFIGS = {
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


def get_profile_config(profile: Union[str, ActionProfile]) -> ProfileConfig:
    """
    Get configuration for a profile.
    
    Args:
        profile: Profile name or enum value
        
    Returns:
        ProfileConfig for the profile
    """
    if isinstance(profile, str):
        try:
            profile = ActionProfile(profile)
        except ValueError:
            logger.warning(f"Unknown profile '{profile}', using 'action'")
            profile = ActionProfile.ACTION
    
    return PROFILE_CONFIGS.get(profile, ProfileConfig())


def register_profile(name: str, config: ProfileConfig):
    """
    Register a custom action profile.
    
    Args:
        name: Profile name
        config: Profile configuration
    """
    if isinstance(name, str):
        profile_enum = ActionProfile(name) if name in [p.value for p in ActionProfile] else None
        if profile_enum:
            PROFILE_CONFIGS[profile_enum] = config
            logger.info(f"Registered custom profile: {name}")
        else:
            logger.warning(f"Cannot register profile '{name}' - not a valid ActionProfile")


def get_all_profiles() -> Dict[str, ProfileConfig]:
    """
    Get all available action profiles.
    
    Returns:
        Dictionary mapping profile names to configurations
    """
    return {profile.value: config for profile, config in PROFILE_CONFIGS.items()}

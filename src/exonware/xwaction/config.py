#exonware/xwaction/config.py
"""
XWAction Configuration Classes
Configuration classes for action profiles, workflows, monitoring, security, and contracts.
"""

from __future__ import annotations
from typing import Any, Optional
from dataclasses import dataclass, field
from .defs import ActionProfile
@dataclass


class XWActionConfig:
    """Main configuration for XWAction."""
    default_profile: ActionProfile = ActionProfile.ACTION
    auto_detect_profile: bool = True
    default_security: str | list[str] = "default"
    default_engine: str | list[str] = "native"
    default_handlers: list[str] = field(default_factory=lambda: ["validation"])
    enable_openapi: bool = True
    enable_metrics: bool = True
    enable_caching: bool = True
    cache_ttl: int = 300
    max_retry_attempts: int = 3
    default_timeout: Optional[float] = None

    def copy(self) -> XWActionConfig:
        """Create a deep copy of the configuration."""
        return XWActionConfig(
            default_profile=self.default_profile,
            auto_detect_profile=self.auto_detect_profile,
            default_security=self.default_security,
            default_engine=self.default_engine,
            default_handlers=self.default_handlers.copy(),
            enable_openapi=self.enable_openapi,
            enable_metrics=self.enable_metrics,
            enable_caching=self.enable_caching,
            cache_ttl=self.cache_ttl,
            max_retry_attempts=self.max_retry_attempts,
            default_timeout=self.default_timeout
        )
@dataclass


class ValidationConfig:
    """Validation configuration."""
    mode: str = "strict"  # strict, lax
    enable_caching: bool = True
    cache_ttl: int = 300
    use_xwschema: bool = True  # Use XWSchema for validation
@dataclass


class ProfileConfig:
    """Configuration for action profiles."""
    readonly: bool = False
    cache_ttl: int = 0
    audit: bool = False
    background: bool = False
    rate_limit: Optional[str] = None
    security: str | list[str] = "default"
    retry_attempts: int = 0
    timeout: Optional[float] = None
    engine: str | list[str] = "native"
# Built-in profile configurations
PROFILE_CONFIGS: dict[ActionProfile, ProfileConfig] = {
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
    metrics: list[str] = field(default_factory=lambda: ["duration"])
    alerts: dict[str, str] = field(default_factory=dict)
    threshold: dict[str, str] = field(default_factory=dict)
@dataclass


class SecurityConfig:
    """Security configuration for actions."""
    schemes: str | list[str] | dict[str, list[str]] = "default"
    rate_limit: Optional[str] = None
    audit: bool = False
    mfa_required: bool = False
@dataclass


class ContractConfig:
    """Contract validation configuration."""
    input: dict[str, str] = field(default_factory=dict)
    output: dict[str, str] = field(default_factory=dict)
    strict: bool = True


def get_profile_config(profile: str | ActionProfile) -> ProfileConfig:
    """Get configuration for a profile."""
    if isinstance(profile, str):
        profile = ActionProfile(profile)
    return PROFILE_CONFIGS.get(profile, ProfileConfig())


def register_profile(name: str, config: ProfileConfig):
    """Register a new action profile."""
    profile_enum = ActionProfile(name)
    PROFILE_CONFIGS[profile_enum] = config


def get_all_profiles() -> dict[str, ProfileConfig]:
    """Get all registered profiles."""
    return {profile.value: config for profile, config in PROFILE_CONFIGS.items()}

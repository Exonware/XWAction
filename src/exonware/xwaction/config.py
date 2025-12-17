#exonware/xwaction/config.py
"""
XWAction Configuration Classes
Configuration classes for action profiles, workflows, monitoring, security, and contracts.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from .defs import ActionProfile, ProfileConfig, PROFILE_CONFIGS


@dataclass
class XWActionConfig:
    """Main configuration for XWAction."""
    default_profile: ActionProfile = ActionProfile.ACTION
    auto_detect_profile: bool = True
    default_security: Union[str, List[str]] = "default"
    default_engine: Union[str, List[str]] = "native"
    default_handlers: List[str] = field(default_factory=lambda: ["validation"])
    enable_openapi: bool = True
    enable_metrics: bool = True
    enable_caching: bool = True
    cache_ttl: int = 300
    max_retry_attempts: int = 3
    default_timeout: Optional[float] = None
    
    def copy(self) -> 'XWActionConfig':
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
class SecurityConfig:
    """Security configuration for actions."""
    default_scheme: str = "api_key"
    enable_rate_limiting: bool = True
    enable_audit: bool = True
    enable_mfa: bool = False
    rate_limit_default: str = "1000/hour"


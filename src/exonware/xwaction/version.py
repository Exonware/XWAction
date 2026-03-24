"""
Centralized version management for eXonware projects.
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
This module provides centralized version management for the entire project.
All version references should import from this module to ensure consistency.
"""

from datetime import datetime
# =============================================================================
# VERSION CONFIGURATION
# =============================================================================

def _today_release_date() -> str:
    """Return today's date in DD-MMM-YYYY."""
    return datetime.now().strftime("%d-%b-%Y")
# Main version - update this to change version across entire project
__version__ = "0.9.0.3"
# Release/update date (DD-MMM-YYYY). Evaluated at import time.
__date__ = _today_release_date()
# Version components for programmatic access
VERSION_MAJOR = 0
VERSION_MINOR = 9
VERSION_PATCH = 0
VERSION_BUILD = 3  # Set to None for releases, or build number for dev builds
# Version metadata
VERSION_SUFFIX = ""  # e.g., "dev", "alpha", "beta", "rc1"
VERSION_STRING = __version__ + VERSION_SUFFIX
# =============================================================================
# VERSION UTILITIES
# =============================================================================

def get_version() -> str:
    """Get the current version string."""
    return VERSION_STRING


def get_date() -> str:
    """Get the release/update date (DD-MMM-YYYY)."""
    return __date__


def get_version_info() -> tuple:
    """Get version as a tuple (major, minor, patch, build)."""
    return (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH, VERSION_BUILD)

def get_version_dict() -> dict:
    """Get version information as a dictionary."""
    return {
        "version": VERSION_STRING,
        "major": VERSION_MAJOR,
        "minor": VERSION_MINOR,
        "patch": VERSION_PATCH,
        "build": VERSION_BUILD,
        "suffix": VERSION_SUFFIX
    }

def is_dev_version() -> bool:
    """Check if this is a development version."""
    return VERSION_SUFFIX in ("dev", "alpha", "beta") or VERSION_BUILD is not None

def is_release_version() -> bool:
    """Check if this is a release version."""
    return not is_dev_version()
# =============================================================================
# EXPORTS
# =============================================================================
__all__ = [
    "__version__",
    "__date__",
    "VERSION_MAJOR",
    "VERSION_MINOR", 
    "VERSION_PATCH",
    "VERSION_BUILD",
    "VERSION_SUFFIX",
    "VERSION_STRING",
    "get_version",
    "get_date",
    "get_version_info",
    "get_version_dict",
    "is_dev_version",
    "is_release_version"
]

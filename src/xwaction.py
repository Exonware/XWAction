"""
#exonware/xwaction/src/xwaction.py
Convenience module for importing xwaction.
This allows users to import the library in two ways:
- import exonware.xwaction
- import xwaction
"""
# Import everything from the main package

from exonware.xwaction import *  # noqa: F401, F403
# Preserve the version
from exonware.xwaction.version import __version__  # noqa: F401

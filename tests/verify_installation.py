#!/usr/bin/env python3
"""
#exonware/xwaction/tests/verify_installation.py
Installation verification script for xwaction.
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 18-Dec-2025
"""

from __future__ import annotations
import sys
from pathlib import Path


def verify_installation() -> bool:
    print("Verifying xwaction installation...")
    # Add src to Python path for testing
    src_path = Path(__file__).parent.parent / "src"
    sys.path.insert(0, str(src_path))
    # Canonical import path for this library
    import exonware.xwaction as xwaction_pkg  # noqa: F401
    import xwaction  # noqa: F401
    # Basic version checks
    assert hasattr(xwaction_pkg, "__version__")
    # Core API checks (parity with MIGRAT exports)
    assert hasattr(xwaction_pkg, "XWAction")
    assert hasattr(xwaction_pkg, "ActionRegistry")
    assert hasattr(xwaction_pkg, "ActionProfile")
    assert hasattr(xwaction_pkg, "ActionHandlerPhase")
    return True


def main() -> None:
    ok = verify_installation()
    raise SystemExit(0 if ok else 1)
if __name__ == "__main__":
    main()

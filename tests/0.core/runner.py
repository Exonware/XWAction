#!/usr/bin/env python3
"""
#exonware/xwaction/tests/0.core/runner.py
Core test runner for xwaction.
Auto-discovers and runs core tests with colored output.
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 18-Dec-2025
"""

import sys
import subprocess
from pathlib import Path
# ⚠️ CRITICAL: Configure UTF-8 encoding for Windows console (GUIDE_TEST.md compliance)
from exonware.xwsystem.console.cli import ensure_utf8_console
ensure_utf8_console()
# Add src to Python path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))
# Fallback implementation

class TestRunner:
    """Fallback TestRunner without xwsystem utilities."""

    def __init__(self, library_name: str, layer_name: str, description: str, test_dir: Path, markers: list[str] = None):
        self.library_name = library_name
        self.layer_name = layer_name
        self.description = description
        self.test_dir = test_dir
        self.markers = markers or []

    def run(self) -> int:
        """Run tests using pytest."""
        cmd = [sys.executable, "-m", "pytest", str(self.test_dir), "-v", "--tb=short", "-x"]
        if self.markers:
            cmd.extend(["-m", " and ".join(self.markers)])
        result = subprocess.run(cmd)
        return result.returncode


def main() -> int:
    """Run core tests."""
    test_dir = Path(__file__).parent
    runner = TestRunner(
        library_name="xwaction",
        layer_name="0.core",
        description="Core Tests - Fast, High-Value Checks",
        test_dir=test_dir,
        markers=["xwaction_core"]
    )
    return runner.run()
if __name__ == "__main__":
    sys.exit(main())

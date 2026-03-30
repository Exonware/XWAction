#!/usr/bin/env python3
"""
#exonware/xwaction/tests/runner.py
Main test runner for xwaction.
Coordinates all test layers and records a single Markdown summary under docs/logs/tests.
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 18-Dec-2025
Usage:
 python tests/runner.py # Run all tests
 python tests/runner.py --core # Run only core tests
 python tests/runner.py --unit # Run only unit tests
 python tests/runner.py --integration # Run only integration tests
 python tests/runner.py --advance # Run only advance tests (v1.0.0+)
 python tests/runner.py --security # Run only security tests
 python tests/runner.py --performance # Run only performance tests
Output:
 - Terminal: Colored, formatted output
 - File: docs/logs/tests/TEST_<timestamp>_SUMMARY.md (Markdown-friendly format)
"""

import sys
import subprocess
import os
from pathlib import Path
from datetime import datetime
# ⚠️ CRITICAL: Configure UTF-8 encoding for Windows console (GUIDE_TEST.md compliance)
from exonware.xwsystem.console.cli import ensure_utf8_console
ensure_utf8_console()
# Add src to Python path for testing
test_dir = Path(__file__).parent
src_path = test_dir.parent / "src"
sys.path.insert(0, str(src_path))
# Fallback implementations

class DualOutput:
    """Fallback DualOutput without colors."""

    def __init__(self, output_file: Path):
        self.output_file = output_file
        self.markdown_lines = []

    def print(self, text: str, markdown_format: str = None, color: str = None, emoji: str = None):
        display_text = f"{emoji} {text}" if emoji else text
        print(display_text)
        if markdown_format:
            self.markdown_lines.append(markdown_format)
        else:
            cleaned = text.replace("="*80, "---")
            if emoji:
                cleaned = f"{emoji} {cleaned}"
            self.markdown_lines.append(cleaned)

    def save(self, header_info: dict = None):
        now = datetime.now()
        header = f"""# Test Runner Output
**Library:** xwaction  
**Generated:** {now.strftime("%d-%b-%Y %H:%M:%S")}.{now.microsecond//1000:03d}  
**Runner:** Main Orchestrator
---
"""
        content = header + "\n".join(self.markdown_lines) + "\n"
        self.output_file.write_text(content, encoding='utf-8')


def format_path(path: Path) -> str:
    return str(path.resolve())


def print_header(title: str, output=None):
    print("=" * 80)
    print(f"🎯 {title}")
    print("=" * 80)


def print_section(title: str, output=None):
    print(f"\n📋 {title}")


def print_status(success: bool, message: str, output=None):
    emoji = '✅' if success else '❌'
    print(f"{emoji} {message}")


def run_sub_runner(runner_path: Path, description: str, output: DualOutput) -> int:
    """Run a sub-runner and return exit code."""
    separator = "="*80
    output.print(separator, f"\n## {description}\n", emoji='📂')
    output.print(f"Starting: {description}", f"**Status:** Running...", color='info', emoji='▶️')
    output.print(f"Runner Path: {format_path(runner_path)}", f"**Runner Path:** `{format_path(runner_path)}`", color='info', emoji='📍')
    output.print(separator, "")
    workspace_root = test_dir.parent.parent
    sibling_src_paths = [
        test_dir.parent / "src",
        workspace_root / "xwdata" / "src",
        workspace_root / "xwsystem" / "src",
        workspace_root / "xwlazy" / "src",
        workspace_root / "xwnode" / "src",
    ]
    existing_paths = [str(p) for p in sibling_src_paths if p.exists()]
    env = os.environ.copy()
    current_py_path = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(existing_paths + ([current_py_path] if current_py_path else []))

    result = subprocess.run(
        [sys.executable, str(runner_path)],
        cwd=runner_path.parent,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',  # Replace invalid chars instead of crashing
        env=env,
    )
    # Print sub-runner output
    if result.stdout:
        output.print(result.stdout, f"```\n{result.stdout}\n```")
    if result.stderr:
        output.print(result.stderr, f"**Errors:**\n```\n{result.stderr}\n```", color='error')
    # Status
    if result.returncode == 0:
        output.print(f"{description} PASSED", f"\n**Result:** ✅ PASSED", color='success', emoji='✅')
    else:
        output.print(f"{description} FAILED", f"\n**Result:** ❌ FAILED", color='error', emoji='❌')
    return result.returncode


def main():
    """Main test runner function following GUIDE_TEST.md."""
    # Setup output logger
    reports_dir = test_dir.parent / "docs" / "logs" / "tests"
    reports_dir.mkdir(parents=True, exist_ok=True)
    from exonware.xwsystem.utils.test_runner import timestamp_for_filename
    timestamp = timestamp_for_filename()
    output_file = reports_dir / f"TEST_{timestamp}_SUMMARY.md"
    output = DualOutput(output_file)
    # Header using reusable utility
    print_header("xwaction Test Runner - Hierarchical Orchestrator", output)
    # Print paths
    output.print(
        f"Test Directory: {format_path(test_dir)}",
        f"**Test Directory:** `{format_path(test_dir)}`",
        color='info', emoji='ℹ️'
    )
    # Parse arguments
    args = sys.argv[1:]
    # Define sub-runners
    core_runner = test_dir / "0.core" / "runner.py"
    unit_runner = test_dir / "1.unit" / "runner.py"
    integration_runner = test_dir / "2.integration" / "runner.py"
    advance_runner = test_dir / "3.advance" / "runner.py"
    exit_codes = []
    # Determine which tests to run
    if "--core" in args:
        if core_runner.exists():
            exit_codes.append(run_sub_runner(core_runner, "Core Tests", output))
    elif "--unit" in args:
        if unit_runner.exists():
            exit_codes.append(run_sub_runner(unit_runner, "Unit Tests", output))
    elif "--integration" in args:
        if integration_runner.exists():
            exit_codes.append(run_sub_runner(integration_runner, "Integration Tests", output))
    elif "--advance" in args:
        if advance_runner.exists():
            exit_codes.append(run_sub_runner(advance_runner, "Advance Tests", output))
        else:
            msg = "\n⚠️ Advance tests not available (requires v1.0.0)"
            output.print(msg, f"\n> {msg}")
    elif "--security" in args or "--performance" in args or "--usability" in args or "--maintainability" in args or "--extensibility" in args:
        # Forward to advance runner if exists
        if advance_runner.exists():
            result = subprocess.run([sys.executable, str(advance_runner)] + args)
            exit_codes.append(result.returncode)
        else:
            msg = "\n⚠️ Advance tests not available (requires v1.0.0)"
            output.print(msg, f"\n> {msg}")
    else:
        # Run all tests in sequence
        msg_header = "\n🚀 Running: ALL Tests"
        msg_layers = " Layers: 0.core ✅ 1.unit ✅ 2.integration ✅ 3.advance"
        output.print(msg_header, "\n## Running All Test Layers")
        output.print(msg_layers, f"\n**Execution Order:** 0.core ✅ 1.unit ✅ 2.integration ✅ 3.advance\n")
        output.print("", "")
        # Core tests
        if core_runner.exists():
            exit_codes.append(run_sub_runner(core_runner, "Layer 0: Core Tests", output))
        # Unit tests
        if unit_runner.exists():
            exit_codes.append(run_sub_runner(unit_runner, "Layer 1: Unit Tests", output))
        # Integration tests
        if integration_runner.exists():
            exit_codes.append(run_sub_runner(integration_runner, "Layer 2: Integration Tests", output))
        # Advance tests (if available)
        if advance_runner.exists():
            exit_codes.append(run_sub_runner(advance_runner, "Layer 3: Advance Tests", output))
    # Print summary
    summary_header = f"\n{'='*80}"
    output.print(summary_header, f"\n---\n\n## 📈 Test Execution Summary")
    output.print("📈 TEST EXECUTION SUMMARY", "")
    output.print(f"{'='*80}", "")
    total_runs = len(exit_codes)
    passed = sum(1 for code in exit_codes if code == 0)
    failed = total_runs - passed
    output.print(f"Total Layers: {total_runs}", f"- **Total Layers:** {total_runs}")
    output.print(f"Passed: {passed}", f"- **Passed:** {passed}")
    output.print(f"Failed: {failed}", f"- **Failed:** {failed}")
    # Final status
    if all(code == 0 for code in exit_codes):
        final_msg = "\n✅ ALL TESTS PASSED!"
        output.print(final_msg, f"\n### {final_msg}")
        # Save output
        output.save()
        print(f"\n💾 Test results saved to: {output_file}")
        sys.exit(0)
    else:
        final_msg = "\n❌ SOME TESTS FAILED!"
        output.print(final_msg, f"\n### {final_msg}")
        # Save output
        output.save()
        print(f"\n💾 Test results saved to: {output_file}")
        sys.exit(1)
if __name__ == "__main__":
    main()

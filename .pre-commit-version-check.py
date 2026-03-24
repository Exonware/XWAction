#!/usr/bin/env python3
"""
Check that the package version and date are defined only in the version.py
specified by pyproject.toml [tool.hatch.version] path (no hardcoded versions
or dates elsewhere). Used by .github/workflows/check-versions.yml.
Exits 0 if OK, 2 if hardcoded versions or dates found.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path
# Repo root (where this script lives)
ROOT = Path(__file__).resolve().parent
SKIP_DIRS = {"_old", ".venv", "__pycache__", ".git"}
def get_version_py_path() -> Path:
    """Read version.py path from pyproject.toml [tool.hatch.version] path."""
    pyproject = ROOT / "pyproject.toml"
    if not pyproject.exists():
        print("ERROR: pyproject.toml not found", file=sys.stderr)
        sys.exit(2)
    text = pyproject.read_text(encoding="utf-8")
    m = re.search(r"\[tool\.hatch\.version\][^\n]*\n\s*path\s*=\s*[\"']([^\"']+)[\"']", text, re.DOTALL)
    if not m:
        print("ERROR: [tool.hatch.version] path not found in pyproject.toml", file=sys.stderr)
        sys.exit(2)
    return (ROOT / m.group(1).strip()).resolve()
def get_canonical_version(version_py: Path) -> str:
    """Read __version__ from version.py."""
    if not version_py.exists():
        print(f"ERROR: {version_py} not found", file=sys.stderr)
        sys.exit(2)
    code = version_py.read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', code)
    if not m:
        print("ERROR: __version__ not found in version.py", file=sys.stderr)
        sys.exit(2)
    return m.group(1)
def get_canonical_date(version_py: Path) -> str | None:
    """Read __date__ from version.py (YYYY-MM-DD). Returns None if not present."""
    if not version_py.exists():
        return None
    code = version_py.read_text(encoding="utf-8")
    m = re.search(r'__date__\s*=\s*["\']([^"\']+)["\']', code)
    return m.group(1) if m else None
# Patterns that mean "hardcoded version" when found outside version.py
VERSION_ASSIGNMENT_RE = re.compile(r'__version__\s*=\s*["\'](\d+\.\d+(?:\.\d+)*(?:\.\d+)?)["\']')
def check_py_file(path: Path, version_py: Path, canonical: str, init_fallback_ok: Path | None) -> list[str]:
    """Check a Python file for hardcoded versions. Returns list of error messages."""
    errors = []
    if any(s in path.parts for s in SKIP_DIRS):
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"{path}: could not read: {e}"]
    allowed = {version_py, Path(__file__).resolve()}
    for m in VERSION_ASSIGNMENT_RE.finditer(text):
        if path in allowed:
            continue
        if init_fallback_ok and path == init_fallback_ok and m.group(1) == "0.0.0":
            continue
        errors.append(f"{path}:{text[: m.start()].count(chr(10)) + 1}: {m.group(0)!r} (use version from version.py)")
    # Only flag __version__ assignments in .py; docstrings like "Version: X.Y.Z" are allowed
    return errors
def check_text_file(path: Path, canonical: str) -> list[str]:
    """Check README etc. for literal version string."""
    errors = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return []
    if canonical not in text:
        return []
    for i, line in enumerate(text.splitlines(), 1):
        if canonical in line:
            errors.append(f"{path}:{i}: hardcoded version {canonical!r} (use version.py or 'see version.py')")
            break
    return errors
def check_text_file_date(path: Path, canonical_date: str) -> list[str]:
    """Check README etc. for literal date string (version.py is source of truth)."""
    errors = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return []
    if canonical_date not in text:
        return []
    for i, line in enumerate(text.splitlines(), 1):
        if canonical_date not in line:
            continue
        # Allow lines that already point to version.py / __date__
        if "version.py" in line or "(__date__)" in line:
            continue
        errors.append(
            f"{path}:{i}: hardcoded date {canonical_date!r} (use version.py __date__ or 'See version.py')"
        )
        break
    return errors
def main() -> None:
    version_py = get_version_py_path()
    canonical = get_canonical_version(version_py)
    allowed = {version_py, Path(__file__).resolve()}
    # Allow fallback in src/exonware/__init__.py when present
    init_py = ROOT / "src" / "exonware" / "__init__.py"
    init_fallback_ok = init_py if init_py.exists() else None
    all_errors: list[str] = []
    for py in ROOT.rglob("*.py"):
        if not py.is_file() or py in allowed:
            continue
        if any(s in py.parts for s in SKIP_DIRS):
            continue
        try:
            rel = py.relative_to(ROOT)
        except ValueError:
            continue
        if "src" not in rel.parts and ".github" in rel.parts:
            continue
        if "src" in rel.parts:
            all_errors.extend(check_py_file(py, version_py, canonical, init_fallback_ok))
    for name in ("README.md", "README.rst"):
        p = ROOT / name
        if p.exists():
            all_errors.extend(check_text_file(p, canonical))
    canonical_date = get_canonical_date(version_py)
    if canonical_date:
        for name in ("README.md", "README.rst"):
            p = ROOT / name
            if p.exists():
                all_errors.extend(check_text_file_date(p, canonical_date))
        for toml in sorted(ROOT.glob("pyproject*.toml")):
            if toml.exists():
                try:
                    for i, line in enumerate(toml.read_text(encoding="utf-8").splitlines(), 1):
                        if canonical_date in line and not line.strip().startswith("#"):
                            all_errors.append(
                                f"{toml}:{i}: hardcoded date {canonical_date!r} (use version.py __date__)"
                            )
                            break
                except Exception:
                    pass
    for toml in sorted(ROOT.glob("pyproject*.toml")):
        if not toml.exists():
            continue
        try:
            for i, line in enumerate(toml.read_text(encoding="utf-8").splitlines(), 1):
                if canonical in line and not line.strip().startswith("#"):
                    all_errors.append(
                        f"{toml}:{i}: hardcoded version {canonical!r} (version is dynamic from version.py)"
                    )
                    break
        except Exception:
            pass
    if all_errors:
        print("Hardcoded version(s) or date(s) found (version.py is the only source of truth):", file=sys.stderr)
        for e in all_errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(2)
    try:
        rel = version_py.relative_to(ROOT)
    except ValueError:
        rel = version_py
    msg = f"OK: version {canonical!r} only in {rel}"
    if canonical_date:
        msg += f", date {canonical_date!r} only in {rel}"
    print(msg)
    sys.exit(0)
if __name__ == "__main__":
    main()

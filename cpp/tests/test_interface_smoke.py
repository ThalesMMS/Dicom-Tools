#!/usr/bin/env python3
"""
Smoke tests for the interactive interface helper (scripts/test_interface.py).
Keeps coverage light: import sanity, help text, and command builder outputs.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "test_interface.py"


def check(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_help_runs() -> None:
    """Ensure --help runs without needing the DicomTools binary."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    check(result.returncode == 0, f"--help returned {result.returncode}")
    combined = (result.stdout + result.stderr)
    check("Interface interativa" in combined, "Help output missing expected title")


def test_build_command_functions() -> None:
    """Validate basic utilities without spawning the GUI or running suites."""
    import importlib.util  # noqa: WPS433 - local import to limit scope

    spec = importlib.util.spec_from_file_location("test_interface_mod", SCRIPT)
    check(spec and spec.loader, "Failed to load scripts/test_interface.py spec")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[arg-type]
    exe = sys.executable  # guaranteed to exist
    resolved = mod.resolve_executable(exe)
    check(resolved == exe, "resolve_executable should return the same path when it exists")

    cmd = mod.build_command(exe, "all", "input.dcm", "out_dir", True)
    expected = [exe, "all", "-i", "input.dcm", "-o", "out_dir", "-v"]
    check(cmd == expected, f"build_command mismatch: {cmd} != {expected}")


def main() -> int:
    tests = [
        ("help", test_help_runs),
        ("build_command", test_build_command_functions),
    ]
    for name, fn in tests:
        try:
            fn()
            print(f"[OK] {name}")
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {name}: {exc}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

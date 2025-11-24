#!/usr/bin/env python3
#
# dicom_echo.py
# Dicom-Tools-py
#
# Sends standalone C-ECHO requests to verify DICOM network connectivity.
#
# Thales Matheus Mendonça Santos - November 2025

"""
Send a C-ECHO (DICOM ping) to verify PACS connectivity.

This wraps the pynetdicom-powered helper used in the unified CLI, but exposes
it as a dedicated command so it can be scripted independently.
"""

import argparse
import sys

from .core.network import send_c_echo


def run_echo(host: str, port: int, *, calling_aet: str, called_aet: str, timeout: int) -> int:
    """Execute a C-ECHO and return the raw status code."""
    # Delegate to the shared network helper so the CLI and standalone script behave identically
    return send_c_echo(host, port, calling_aet=calling_aet, called_aet=called_aet, timeout=timeout)


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a C-ECHO (DICOM ping) request")
    parser.add_argument("host", help="Remote host", nargs="?", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=11112, help="Remote DICOM port")
    parser.add_argument("--calling-aet", default="DICOMTOOLS_SCU", help="Calling AE Title")
    parser.add_argument("--called-aet", default="DICOMTOOLS_SCP", help="Called AE Title")
    parser.add_argument("--timeout", type=int, default=5, help="Association timeout in seconds")
    args = parser.parse_args()

    try:
        status = run_echo(args.host, args.port, calling_aet=args.calling_aet, called_aet=args.called_aet, timeout=args.timeout)
        print(f"C-ECHO response status: 0x{status:04x}")
        sys.exit(0 if status == 0x0000 else 1)
    except Exception as exc:  # noqa: BLE001
        # Convert any networking/runtime failure into a non-zero exit for shell scripting
        print(f"Failed to complete C-ECHO: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

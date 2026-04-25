"""
Runs CLI/JSON contract requests from the command line (no UI).

Usage:
  python -m interface.contract_runner --backend python --op info --input /path/file.dcm
  python -m interface.contract_runner --request-file request.json
  echo '{"backend": "rust", "op": "dump", "input": "file.dcm"}' | python -m interface.contract_runner
"""

import argparse
import json
import sys
from pathlib import Path

from .adapters import get_adapter


def load_request_from_args(args: argparse.Namespace) -> dict:
    if args.request_file:
        return json.loads(Path(args.request_file).read_text())
    if not sys.stdin.isatty():
        # Allows piping: echo '{...}' | python -m interface.contract_runner
        payload = sys.stdin.read()
        if payload.strip():
            return json.loads(payload)

    # Individual flag mode
    options = json.loads(args.options) if args.options else {}
    return {
        "backend": args.backend,
        "op": args.op,
        "input": args.input,
        "output": args.output,
        "options": options,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="CLI/JSON contract executor (no UI)")
    parser.add_argument("--request-file", help="JSON file with the complete request")
    parser.add_argument("--backend", help="Backend (python|rust|cpp|java|csharp|js)")
    parser.add_argument("--op", help="Operation (info, anonymize, ...)")
    parser.add_argument("--input", help="Input path")
    parser.add_argument("--output", help="Optional output path")
    parser.add_argument("--options", help='JSON options (for example: \'{"frame":0}\')')

    args = parser.parse_args()

    try:
        request = load_request_from_args(args)
    except Exception as exc:
        print(f"Error reading request: {exc}", file=sys.stderr)
        return 1

    try:
        adapter = get_adapter(request.get("backend", ""))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    result = adapter.handle(request)
    print(json.dumps(result.as_dict(), indent=2, ensure_ascii=False))
    return 0 if result.ok else (result.returncode or 1)


if __name__ == "__main__":
    sys.exit(main())

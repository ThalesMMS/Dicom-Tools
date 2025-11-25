import json
import os
import shlex
import subprocess
from pathlib import Path

from .runner import RunResult


class JsCliAdapter:
    """Adapter for the JavaScript contract CLI (shim backed by python for now)."""

    def __init__(self) -> None:
        root = Path(__file__).resolve().parent.parent.parent
        default_cmd = ["node", str(root / "js" / "contract-cli" / "index.js")]
        env_cmd = os.environ.get("JS_DICOM_TOOLS_CMD")
        self.cmd = shlex.split(env_cmd) if env_cmd else default_cmd

    def handle(self, request: dict) -> RunResult:
        op = request.get("op")
        input_path = request.get("input") or ""
        output = request.get("output") or ""
        options = request.get("options") or {}

        args = self.cmd + [
            "--op",
            op,
            "--input",
            str(input_path),
        ]
        if output:
            args += ["--output", str(output)]
        if options:
            args += ["--options", json.dumps(options)]

        proc = subprocess.run(args, capture_output=True, text=True)
        try:
            payload = json.loads(proc.stdout) if proc.stdout else {}
        except json.JSONDecodeError:
            payload = {}
        return RunResult(
            ok=proc.returncode == 0,
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            output_files=payload.get("output_files") or [],
            metadata=payload.get("metadata"),
        )

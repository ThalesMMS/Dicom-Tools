import json
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class RunResult:
    ok: bool
    returncode: int
    stdout: str
    stderr: str
    output_files: List[str]
    metadata: Optional[Dict[str, Any]] = None
    backend: Optional[str] = None
    operation: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "output_files": self.output_files,
            "artifacts": self.output_files,
            "metadata": self.metadata,
            "backend": self.backend,
            "operation": self.operation,
        }


def run_process(cmd: List[str], cwd: Optional[Path] = None, timeout: float | None = None) -> RunResult:
    """Run a command and capture stdout/stderr with friendly failures."""
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError as exc:
        message = f"Command not found: {exc.filename}" if exc.filename else str(exc)
        return RunResult(ok=False, returncode=127, stdout="", stderr=message, output_files=[])
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or "").strip() if hasattr(exc, "stdout") else ""
        stderr = (exc.stderr or "").strip() if hasattr(exc, "stderr") else ""
        if not stderr:
            stderr = f"Command timed out after {timeout} seconds"
        return RunResult(ok=False, returncode=-1, stdout=stdout, stderr=stderr, output_files=[])

    return RunResult(
        ok=proc.returncode == 0,
        returncode=proc.returncode,
        stdout=proc.stdout.strip(),
        stderr=proc.stderr.strip(),
        output_files=[],
    )


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def parse_json_maybe(text: str) -> Optional[Dict[str, Any]]:
    """Try to parse stdout as JSON when the backend supports it."""
    try:
        return json.loads(text)
    except Exception:
        return None


def split_cmd(cmd: str) -> List[str]:
    """Split env-provided commands that may come as a single string."""
    return shlex.split(cmd)

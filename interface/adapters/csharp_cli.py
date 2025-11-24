import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from .runner import RunResult, run_process


class CSharpCliAdapter:
    """Adapter para CLI fo-dicom (projeto cs/). Espera um binário/CLI que aceite o contrato CLI/JSON."""

    def __init__(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        default_cmd = os.environ.get("CS_DICOM_TOOLS_CMD", str(self.root / "cs" / "bin" / "Release" / "net8.0" / "DicomTools.Cli"))
        self.base_cmd: List[str] = [default_cmd]

    def handle(self, request: Dict[str, Any]) -> RunResult:
        op = request.get("op")
        options = request.get("options", {}) or {}
        input_path = request.get("input")
        output = request.get("output")

        if not op or not input_path:
            return RunResult(False, 1, "", "op e input são obrigatórios", [], None)

        cmd = self._build_cmd(op, input_path, output, options)
        if cmd is None:
            return RunResult(False, 1, "", f"operação não suportada pelo backend C#: {op}", [], None)

        result = run_process(cmd, cwd=self.root / "cs")
        if output:
            result.output_files.append(str(Path(output)))
        return result

    def _build_cmd(self, op: str, input_path: str, output: str | None, options: Dict[str, Any]) -> List[str] | None:
        # Placeholder: assumimos um CLI com mesmas operações do contrato.
        inferred_output = output
        if op == "info":
            return [*self.base_cmd, "info", input_path, "--json"]
        if op == "anonymize":
            inferred_output = inferred_output or str(Path(input_path).with_name(f"{Path(input_path).stem}_anon.dcm"))
            return [*self.base_cmd, "anonymize", input_path, "--output", inferred_output]
        if op == "to_image":
            inferred_output = inferred_output or str(Path(input_path).with_suffix(".png"))
            cmd = [*self.base_cmd, "to-image", input_path, "--output", inferred_output]
            if options.get("frame") is not None:
                cmd.extend(["--frame", str(options["frame"])])
            return cmd
        if op == "transcode":
            inferred_output = inferred_output or str(Path(input_path).with_name(f"{Path(input_path).stem}_explicit.dcm"))
            syntax = options.get("syntax", "explicit")
            return [*self.base_cmd, "transcode", input_path, "--output", inferred_output, "--transfer-syntax", str(syntax)]
        if op == "validate":
            return [*self.base_cmd, "validate", input_path]
        if op == "echo":
            host = options.get("host", "127.0.0.1")
            port = options.get("port", 104)
            return [*self.base_cmd, "echo", f"{host}:{port}"]
        if op == "dump":
            return [*self.base_cmd, "dump", input_path]
        if op == "stats":
            return [*self.base_cmd, "stats", input_path]
        if op == "histogram":
            bins = options.get("bins", 256)
            return [*self.base_cmd, "histogram", input_path, "--bins", str(bins)]
        return None

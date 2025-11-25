import os
from pathlib import Path
from typing import Any, Dict, List

from .runner import RunResult, parse_json_maybe, run_process, split_cmd


class CSharpCliAdapter:
    """Adapter para CLI fo-dicom (projeto cs/). Usa binário DicomTools.Cli, preferindo Release/net8.0 e fallback para Debug."""

    def __init__(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        env_cmd = os.environ.get("CS_DICOM_TOOLS_CMD")
        if env_cmd:
            self.base_cmd = split_cmd(env_cmd)
        else:
            default_cmd = self._find_default_cmd()
            self.base_cmd = [default_cmd]

    def _find_default_cmd(self) -> str:
        candidates = [
            self.root / "cs" / "bin" / "Release" / "net8.0" / "DicomTools.Cli",
            self.root / "cs" / "bin" / "Debug" / "net8.0" / "DicomTools.Cli",
        ]
        for path in candidates:
            if path.exists():
                return str(path)
        # fallback: let PATH resolve if not found
        return "DicomTools.Cli"

    def handle(self, request: Dict[str, Any]) -> RunResult:
        op = request.get("op")
        options = request.get("options", {}) or {}
        input_path = request.get("input")
        output = request.get("output")

        if not op or (op != "custom" and not input_path):
            return RunResult(False, 1, "", "op e input são obrigatórios", [], None)

        cmd = self._build_cmd(op, input_path, output, options)
        if cmd is None:
            return RunResult(False, 1, "", f"operação não suportada pelo backend C#: {op}", [], None)

        result = run_process(cmd, cwd=self.root / "cs")
        meta = parse_json_maybe(result.stdout)
        result.metadata = meta
        result.backend = "csharp"
        result.operation = op
        if output:
            result.output_files.append(str(Path(output)))
        return result

    def _build_cmd(self, op: str, input_path: str, output: str | None, options: Dict[str, Any]) -> List[str] | None:
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
            if options.get("format"):
                cmd.extend(["--format", str(options["format"])])
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
            depth = options.get("max_depth")
            max_val = options.get("max_value_len")
            cmd = [*self.base_cmd, "dump", input_path]
            if depth is not None:
                cmd.extend(["--depth", str(depth)])
            if max_val is not None:
                cmd.extend(["--max-value-length", str(max_val)])
            return cmd
        if op == "stats":
            cmd = [*self.base_cmd, "stats", input_path]
            if options.get("frame") is not None:
                cmd.extend(["--frame", str(options["frame"])])
            cmd.append("--json")
            return cmd
        if op == "histogram":
            bins = options.get("bins", 256)
            cmd = [*self.base_cmd, "histogram", input_path, "--bins", str(bins), "--json"]
            if options.get("frame") is not None:
                cmd.extend(["--frame", str(options["frame"])])
            return cmd
        if op == "custom":
            custom_cmd = options.get("custom_cmd")
            if not custom_cmd:
                return None
            parts = str(custom_cmd).split()
            parts = [str(input_path) if p == "{input}" else str(output) if p == "{output}" else p for p in parts]
            return [*self.base_cmd, *parts]
        return None

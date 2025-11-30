import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from .runner import RunResult, ensure_dir, parse_json_maybe, run_process, split_cmd


class PythonCliAdapter:
    """Chama o CLI Python (`python -m DICOM_reencoder.cli`)."""

    def __init__(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        self.cwd = self.root / "python"
        default_cmd = os.environ.get("PYTHON_DICOM_TOOLS_CMD", f"{sys.executable} -m DICOM_reencoder.cli")
        self.base_cmd: List[str] = split_cmd(default_cmd)

    def handle(self, request: Dict[str, Any]) -> RunResult:
        op = request.get("op")
        options = request.get("options", {}) or {}
        input_path = request.get("input")
        output = request.get("output")

        requires_input = op not in {"echo", "custom"}
        if not op or (requires_input and not input_path):
            return RunResult(False, 1, "", "op e input são obrigatórios", [], None)

        cmd = self._build_cmd(op, input_path, output, options)
        if cmd is None:
            return RunResult(False, 1, "", f"operação não suportada pelo backend Python: {op}", [], None)

        result = run_process(cmd, cwd=self.cwd)

        # Tentar extrair metadata quando a saída for JSON (info/summary)
        meta = parse_json_maybe(result.stdout)
        result.metadata = meta
        result.backend = "python"
        result.operation = op

        if output:
            result.output_files.append(str(Path(output)))

        return result

    def _build_cmd(self, op: str, input_path: str, output: str | None, options: Dict[str, Any]) -> List[str] | None:
        if op == "info":
            cmd = [*self.base_cmd, "summary", input_path, "--json"]
            if options.get("verbose"):
                cmd.append("--verbose")
            return cmd

        if op == "anonymize":
            inferred_output = output or self._infer_output(input_path, suffix="_anonymized")
            return [*self.base_cmd, "anonymize", input_path, "-o", inferred_output]

        if op == "to_image":
            inferred_output = output or self._infer_output(input_path, suffix=".png")
            cmd = [*self.base_cmd, "png", input_path, "-o", inferred_output]
            if options.get("frame") is not None:
                cmd.extend(["--frame", str(options["frame"])])
            return cmd

        if op == "transcode":
            inferred_output = output or self._infer_output(input_path, suffix="_explicit.dcm")
            syntax = options.get("syntax", "explicit")
            return [*self.base_cmd, "transcode", input_path, "-o", inferred_output, "--syntax", str(syntax)]

        if op == "validate":
            # Usa script dedicado, pois não existe subcomando em cli.py
            return [sys.executable, "-m", "DICOM_reencoder.validate_dicom", input_path]

        if op == "echo":
            host = options.get("host", "127.0.0.1")
            port = options.get("port", 11112)
            timeout = options.get("timeout", 5)
            calling = options.get("calling_aet", "DICOMTOOLS_SCU")
            called = options.get("called_aet", "DICOMTOOLS_SCP")
            return [
                "python",
                "-m",
                "DICOM_reencoder.dicom_echo",
                host,
                "--port",
                str(port),
                "--timeout",
                str(timeout),
                "--calling-aet",
                calling,
                "--called-aet",
                called,
            ]

        if op == "volume":
            inferred_output = output or str((self.cwd / "output" / "volume.npy").resolve())
            meta_path = options.get("metadata") or str(Path(inferred_output).with_suffix(".json"))
            cmd = [*self.base_cmd, "volume", input_path, "-o", inferred_output, "--metadata", meta_path]
            if options.get("preview"):
                cmd.append("--preview")
            return cmd

        if op == "nifti":
            inferred_output = output or self._infer_output(input_path, suffix=".nii.gz")
            cmd = [*self.base_cmd, "nifti", input_path, "-o", inferred_output]
            if options.get("series_uid"):
                cmd.extend(["--series-uid", options["series_uid"]])
            if options.get("no_compress"):
                cmd.append("--no-compress")
            if options.get("metadata"):
                cmd.extend(["--metadata", options["metadata"]])
            return cmd

        if op == "stats":
            return [*self.base_cmd, "stats", input_path]

        if op == "dump":
            return [*self.base_cmd, "dump", input_path]

        if op == "split_multiframe":
            output_dir = output or str((self.root / "output" / "python_split").resolve())
            cmd = [sys.executable, "-m", "DICOM_reencoder.split_multiframe", input_path, "--output-dir", output_dir]
            if options.get("prefix"):
                cmd.extend(["--prefix", str(options["prefix"])])
            frames = options.get("frames")
            if frames:
                cmd.extend(["--frames", *[str(f) for f in frames]])
            if options.get("info"):
                cmd.append("--info")
            return cmd

        if op in {
            "batch_list",
            "batch_decompress",
            "batch_anonymize",
            "batch_convert",
            "batch_validate",
        }:
            directory = input_path or "."
            op_map = {
                "batch_list": "list",
                "batch_decompress": "decompress",
                "batch_anonymize": "anonymize",
                "batch_convert": "convert",
                "batch_validate": "validate",
            }
            sub_op = op_map[op]
            cmd = [sys.executable, "-m", "DICOM_reencoder.batch_process", "-d", directory, "-o", sub_op]
            if options.get("recursive"):
                cmd.append("-r")
            if op in {"batch_decompress", "batch_anonymize", "batch_convert"}:
                output_dir = output or options.get("output_dir") or str((self.root / "output" / f"python_{sub_op}").resolve())
                cmd.extend(["--output-dir", str(output_dir)])
            if op == "batch_convert" and options.get("format"):
                cmd.extend(["--format", str(options["format"])])
            return cmd

        if op == "custom":
            custom_cmd = options.get("custom_cmd")
            if not custom_cmd:
                return None
            parts = split_cmd(str(custom_cmd))
            parts = [str(input_path) if p == "{input}" else str(output) if p == "{output}" else p for p in parts]
            cmd = [*self.base_cmd, *parts]
            return cmd

        return None

    def _infer_output(self, input_path: str, *, suffix: str) -> str:
        path = Path(input_path)
        if suffix.startswith("."):
            return str(path.with_suffix(suffix))
        return str(path.with_name(path.stem + suffix + path.suffix))

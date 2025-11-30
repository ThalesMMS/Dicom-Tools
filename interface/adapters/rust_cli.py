import os
from pathlib import Path
from typing import Any, Dict, List

from .runner import RunResult, parse_json_maybe, run_process, split_cmd


class RustCliAdapter:
    """Chama o binário Rust (`dicom-tools`)."""

    def __init__(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        self.cwd = self.root / "rust"
        env_cmd = os.environ.get("RUST_DICOM_TOOLS_CMD")
        if env_cmd:
            self.base_cmd = split_cmd(env_cmd)
        else:
            default_bin = os.environ.get("RUST_DICOM_TOOLS_BIN", str(self.cwd / "target" / "release" / "dicom-tools"))
            bin_path = Path(default_bin)
            if not bin_path.is_absolute():
                bin_path = (self.root / bin_path).resolve()
            if bin_path.exists():
                self.base_cmd = [str(bin_path)]
            else:
                # Fallback para cargo run --release -- <args>
                self.base_cmd = ["cargo", "run", "--quiet", "--release", "--"]

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
            return RunResult(False, 1, "", f"operação não suportada pelo backend Rust: {op}", [], None)

        result = run_process(cmd, cwd=self.cwd)
        meta = parse_json_maybe(result.stdout)
        if meta is not None:
            result.metadata = meta
        result.backend = "rust"
        result.operation = op
        if output:
            result.output_files.append(str(Path(output)))
        return result

    def _build_cmd(self, op: str, input_path: str, output: str | None, options: Dict[str, Any]) -> List[str] | None:
        if op == "info":
            cmd = [*self.base_cmd, "info", input_path]
            if options.get("verbose"):
                cmd.append("--verbose")
            if options.get("json"):
                cmd.append("--json")
            return cmd

        if op == "anonymize":
            inferred_output = output or self._infer_output(input_path, suffix="_anonymized.dcm")
            return [*self.base_cmd, "anonymize", input_path, "--output", inferred_output]

        if op == "to_image":
            inferred_output = output or self._infer_output(input_path, suffix=".png")
            cmd = [*self.base_cmd, "to-image", input_path, "--output", inferred_output]
            if options.get("format"):
                cmd.extend(["--format", str(options["format"])])
            if options.get("frame") is not None:
                cmd.extend(["--frame", str(options["frame"])])
            if options.get("window_center") is not None:
                cmd.extend(["--window-center", str(options["window_center"])])
            if options.get("window_width") is not None:
                cmd.extend(["--window-width", str(options["window_width"])])
            if options.get("normalize"):
                cmd.append("--normalize")
            if options.get("disable_modality_lut"):
                cmd.append("--disable-modality-lut")
            if options.get("disable_voi_lut"):
                cmd.append("--disable-voi-lut")
            if options.get("force_8bit"):
                cmd.append("--force-8bit")
            if options.get("force_16bit"):
                cmd.append("--force-16bit")
            return cmd

        if op == "transcode":
            inferred_output = output or self._infer_output(input_path, suffix="_explicit.dcm")
            syntax = options.get("syntax", "explicit-vr-little-endian")
            return [
                *self.base_cmd,
                "transcode",
                input_path,
                "--output",
                inferred_output,
                "--transfer-syntax",
                str(syntax),
            ]

        if op == "validate":
            return [*self.base_cmd, "validate", input_path]

        if op == "echo":
            host = options.get("host", "127.0.0.1")
            port = options.get("port", 104)
            return [*self.base_cmd, "echo", f"{host}:{port}"]

        if op == "dump":
            cmd = [*self.base_cmd, "dump", input_path]
            if options.get("max_depth") is not None:
                cmd.extend(["--max-depth", str(options["max_depth"])])
            if options.get("max_value_len") is not None:
                cmd.extend(["--max-value-len", str(options["max_value_len"])])
            if options.get("json"):
                cmd.append("--json")
            return cmd

        if op == "stats":
            return [*self.base_cmd, "stats", input_path]

        if op == "histogram":
            cmd = [*self.base_cmd, "histogram", input_path]
            if options.get("bins") is not None:
                cmd.extend(["--bins", str(options["bins"])])
            return cmd

        if op == "to_json":
            inferred_output = output or self._infer_output(input_path, suffix=".json")
            return [*self.base_cmd, "to-json", input_path, "--output", inferred_output]

        if op == "from_json":
            inferred_output = output or self._infer_output(str(input_path), suffix=".dcm")
            return [*self.base_cmd, "from-json", input_path, "--output", inferred_output]

        if op == "custom":
            custom_cmd = options.get("custom_cmd")
            if not custom_cmd:
                return None
            parts = split_cmd(str(custom_cmd))
            parts = [str(input_path) if p == "{input}" else str(output) if p == "{output}" else p for p in parts]
            return [*self.base_cmd, *parts]

        return None

    def _infer_output(self, input_path: str, *, suffix: str) -> str:
        path = Path(input_path)
        if suffix.startswith("."):
            return str(path.with_suffix(suffix))
        return str(path.with_name(path.stem + suffix))

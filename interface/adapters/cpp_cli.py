import os
from pathlib import Path
from typing import Any, Dict, List

from .runner import RunResult, ensure_dir, run_process


class CppCliAdapter:
    """Chama o executável C++ (`DicomTools`)."""

    def __init__(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        default_bin = os.environ.get("CPP_DICOM_TOOLS_BIN", str(self.root / "cpp" / "build" / "DicomTools"))
        bin_path = Path(default_bin)
        if not bin_path.is_absolute():
            bin_path = (self.root / bin_path).resolve()
        self.base_cmd: List[str] = [str(bin_path)]

    def handle(self, request: Dict[str, Any]) -> RunResult:
        op = request.get("op")
        input_path = request.get("input")
        output = request.get("output")
        options = request.get("options", {}) or {}

        if not op or not input_path:
            return RunResult(False, 1, "", "op e input são obrigatórios", [], None)

        cmd, output_files = self._build_cmd(op, input_path, output, options)
        if cmd is None:
            return RunResult(False, 1, "", f"operação não suportada pelo backend C++: {op}", [], None)

        result = run_process(cmd)
        result.output_files.extend(output_files)
        return result

    def _build_cmd(
        self, op: str, input_path: str, output: str | None, options: Dict[str, Any]
    ) -> tuple[List[str] | None, List[str]]:
        output_dir = Path(output) if output else self.root / "cpp" / "output"
        ensure_dir(output_dir)

        if op in {"info", "dump"}:
            cmd = [*self.base_cmd, "gdcm:dump", "-i", input_path, "-o", str(output_dir)]
            return cmd, [str(output_dir / "dump.txt")]

        if op == "anonymize":
            cmd = [*self.base_cmd, "gdcm:anonymize", "-i", input_path, "-o", str(output_dir)]
            return cmd, [str(output_dir / Path(input_path).name)]

        if op == "to_image":
            cmd = [*self.base_cmd, "gdcm:preview", "-i", input_path, "-o", str(output_dir)]
            return cmd, [str(output_dir / "preview.pgm")]

        if op == "stats":
            cmd = [*self.base_cmd, "gdcm:stats", "-i", input_path, "-o", str(output_dir)]
            return cmd, [str(output_dir / "pixel_stats.txt")]

        if op == "transcode":
            syntax = options.get("syntax", "j2k")
            if syntax in ("j2k", "jpeg2000", "jpeg2000-lossless", "jpeg2000_lossless"):
                cmd = [*self.base_cmd, "gdcm:transcode-j2k", "-i", input_path, "-o", str(output_dir)]
                return cmd, [str(output_dir / Path(input_path).name)]
            if syntax in ("rle", "rle-lossless", "rle_lossless"):
                cmd = [*self.base_cmd, "gdcm:transcode-rle", "-i", input_path, "-o", str(output_dir)]
                return cmd, [str(output_dir / Path(input_path).name)]
            # Fallback: JPEG-LS
            cmd = [*self.base_cmd, "gdcm:jpegls", "-i", input_path, "-o", str(output_dir)]
            return cmd, [str(output_dir / Path(input_path).name)]

        if op == "validate":
            # Não há validação dedicada; usar dump como proxy mínima.
            cmd = [*self.base_cmd, "gdcm:dump", "-i", input_path, "-o", str(output_dir)]
            return cmd, [str(output_dir / "dump.txt")]

        return None, []

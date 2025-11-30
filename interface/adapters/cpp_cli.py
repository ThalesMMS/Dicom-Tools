import os
from pathlib import Path
from typing import Any, Dict, List

from .runner import RunResult, ensure_dir, parse_json_maybe, run_process, split_cmd


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

        requires_input = op not in {"custom"}
        if not op or (requires_input and not input_path):
            return RunResult(False, 1, "", "op e input são obrigatórios", [], None)

        cmd, output_files = self._build_cmd(op, input_path, output, options)
        if cmd is None:
            return RunResult(False, 1, "", f"operação não suportada pelo backend C++: {op}", [], None)

        test_ops = {
            "test_gdcm",
            "test_dcmtk",
            "test_itk",
            "test_vtk_unit",
            "test_utils",
            "test_integration",
            "test_edge_cases",
            "test_validation",
            "run_cpp_tests",
        }
        cwd = self.root / "cpp" / "build" if op in test_ops else None

        result = run_process(cmd, cwd=cwd)
        meta = parse_json_maybe(result.stdout)
        if meta is not None:
            result.metadata = meta
        result.backend = "cpp"
        result.operation = op
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

        # VTK feature demos (require series directory)
        vtk_map = {
            "vtk_export": "vtk:export",
            "vtk_nifti": "vtk:nifti",
            "vtk_isosurface": "vtk:isosurface",
            "vtk_resample": "vtk:resample",
            "vtk_mask": "vtk:mask",
            "vtk_connectivity": "vtk:connectivity",
            "vtk_mip": "vtk:mip",
            "vtk_metadata": "vtk:metadata",
            "vtk_stats": "vtk:stats",
            "vtk_viewer": "vtk:viewer",
            "vtk_volume_render": "vtk:volume-render",
            "vtk_mpr_multi": "vtk:mpr-multi",
            "vtk_overlay": "vtk:overlay",
            "vtk_stream": "vtk:stream",
            "test_vtk": "test-vtk",
        }
        if op in vtk_map:
            cmd = [*self.base_cmd, vtk_map[op], "-i", input_path, "-o", str(output_dir)]
            return cmd, [str(output_dir)]

        if op == "custom":
            custom_cmd = options.get("custom_cmd")
            if not custom_cmd:
                return None, []
            parts = split_cmd(str(custom_cmd))
            parts = [str(input_path) if p == "{input}" else str(output_dir) if p == "{output}" else p for p in parts]
            cmd = [*self.base_cmd, *parts]
            return cmd, []

        # C++ unit/integration tests (executables in cpp/build)
        test_map = {
            "test_gdcm": "test_gdcm",
            "test_dcmtk": "test_dcmtk",
            "test_itk": "test_itk",
            "test_vtk_unit": "test_vtk",
            "test_utils": "test_utils",
            "test_integration": "test_integration",
            "test_edge_cases": "test_edge_cases",
            "test_validation": "test_validation",
        }
        if op in test_map:
            exe = self.root / "cpp" / "build" / test_map[op]
            return [str(exe)], []

        if op == "run_cpp_tests":
            # Invoke custom target via CMake; fallback to ctest
            return ["cmake", "--build", ".", "--target", "run_cpp_tests"], []

        return None, []

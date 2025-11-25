import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .adapters import get_adapter


BACKENDS = ["python", "rust", "cpp", "java", "csharp", "js"]
IMAGE_EXTS = {".png", ".pgm", ".ppm", ".jpg", ".jpeg"}
ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_FILE = ROOT_DIR / "sample_series" / "IM-0001-0001.dcm"
DEFAULT_SERIES = ROOT_DIR / "sample_series"
OUTPUT_DIR = ROOT_DIR / "output"

# Supported ops per backend (only what each CLI advertises today)
BACKEND_OPS = {
    "python": ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump", "volume", "nifti", "echo", "custom"],
    "rust": ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump", "echo", "custom"],
    "cpp": [
        "info",
        "anonymize",
        "to_image",
        "transcode",
        "validate",
        "stats",
        "dump",
        "custom",
        "vtk_export",
        "vtk_nifti",
        "vtk_isosurface",
        "vtk_resample",
        "vtk_mask",
        "vtk_connectivity",
        "vtk_mip",
        "vtk_metadata",
        "vtk_stats",
        "vtk_viewer",
        "vtk_volume_render",
        "vtk_mpr_multi",
        "vtk_overlay",
        "vtk_stream",
        "test_vtk",
    ],
    "java": ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump", "echo"],
    "csharp": ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump", "echo"],
    "js": ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump", "volume", "nifti", "echo"],
}

BACKEND_LIBRARIES = {
    "python": {
        "dicom_reencoder": BACKEND_OPS["python"],
        "pydicom": ["info", "anonymize", "to_image", "transcode", "validate", "dump", "stats"],
        "pynetdicom": ["echo"],
        "python-gdcm": ["to_image", "transcode", "validate"],
        "simpleitk": ["volume", "nifti", "to_image"],
        "dicom-numpy": ["volume", "nifti", "stats"],
    },
    "rust": {"dicom-rs": BACKEND_OPS["rust"]},
    "cpp": {
        "gdcm": ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump"],
        "dcmtk": ["info", "anonymize", "to_image", "transcode", "validate", "dump"],
        "itk": ["to_image", "validate", "stats"],
        "vtk": [
            "vtk_export",
            "vtk_nifti",
            "vtk_isosurface",
            "vtk_resample",
            "vtk_mask",
            "vtk_connectivity",
            "vtk_mip",
            "vtk_metadata",
            "vtk_stats",
            "vtk_viewer",
            "vtk_volume_render",
            "vtk_mpr_multi",
            "vtk_overlay",
            "vtk_stream",
            "test_vtk",
        ],
    },
    "java": {"dcm4che": BACKEND_OPS["java"]},
    "csharp": {"fo-dicom": BACKEND_OPS["csharp"]},
    "js": {
        "js-shim": BACKEND_OPS["js"],
        "cornerstone3d": ["info", "to_image", "volume", "nifti"],
    },
}

# Default recipes for each backend/op so the UI can run a full suite quickly
DEFAULTS = {
    "python": {
        "info": {"input": DEFAULT_FILE, "options": {"json": True}},
        "anonymize": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_python_anon.dcm"},
        "to_image": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_python.png", "options": {"format": "png", "frame": 0}},
        "transcode": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_python_explicit.dcm", "options": {"syntax": "explicit"}},
        "validate": {"input": DEFAULT_FILE},
        "stats": {"input": DEFAULT_FILE, "options": {"bins": 16}},
        "dump": {"input": DEFAULT_FILE, "options": {"max_value_len": 64}},
        "volume": {"input": DEFAULT_SERIES, "output": OUTPUT_DIR / "ui_python_volume.npy", "options": {"preview": False}},
        "nifti": {"input": DEFAULT_SERIES, "output": OUTPUT_DIR / "ui_python_volume.nii.gz"},
        "echo": {"input": "", "options": {"host": "127.0.0.1", "port": 11112}},
    },
    "rust": {
        "info": {"input": DEFAULT_FILE, "options": {"json": True}},
        "anonymize": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_rust_anon.dcm"},
        "to_image": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_rust.png", "options": {"format": "png"}},
        "transcode": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_rust_j2k.dcm", "options": {"syntax": "1.2.840.10008.1.2.4.90"}},
        "validate": {"input": DEFAULT_FILE},
        "stats": {"input": DEFAULT_FILE, "options": {"bins": 16}},
        "dump": {"input": DEFAULT_FILE, "options": {"max_value_len": 64}},
        "echo": {"input": "", "options": {"host": "127.0.0.1", "port": 11112}},
    },
    "cpp": {
        "info": {"input": DEFAULT_FILE},
        "anonymize": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_cpp_anon.dcm"},
        "to_image": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_cpp_preview.pgm"},
        "transcode": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_cpp_j2k.dcm", "options": {"syntax": "j2k"}},
        "validate": {"input": DEFAULT_FILE},
        "stats": {"input": DEFAULT_FILE},
        "dump": {"input": DEFAULT_FILE},
        "vtk_export": {"input": DEFAULT_SERIES, "output": OUTPUT_DIR},
        "vtk_nifti": {"input": DEFAULT_SERIES, "output": OUTPUT_DIR},
        "vtk_isosurface": {"input": DEFAULT_SERIES, "output": OUTPUT_DIR},
        "vtk_resample": {"input": DEFAULT_SERIES, "output": OUTPUT_DIR},
        "vtk_mask": {"input": DEFAULT_SERIES, "output": OUTPUT_DIR},
        "vtk_connectivity": {"input": DEFAULT_SERIES, "output": OUTPUT_DIR},
        "vtk_mip": {"input": DEFAULT_SERIES, "output": OUTPUT_DIR},
        "vtk_metadata": {"input": DEFAULT_SERIES, "output": OUTPUT_DIR},
        "vtk_stats": {"input": DEFAULT_SERIES, "output": OUTPUT_DIR},
        "vtk_viewer": {"input": DEFAULT_SERIES, "output": OUTPUT_DIR},
        "vtk_volume_render": {"input": DEFAULT_SERIES, "output": OUTPUT_DIR},
        "vtk_mpr_multi": {"input": DEFAULT_SERIES, "output": OUTPUT_DIR},
        "vtk_overlay": {"input": DEFAULT_SERIES, "output": OUTPUT_DIR},
        "vtk_stream": {"input": DEFAULT_SERIES, "output": OUTPUT_DIR},
        "test_vtk": {"input": DEFAULT_SERIES, "output": OUTPUT_DIR},
    },
    "java": {
        "info": {"input": DEFAULT_FILE, "options": {"json": True}},
        "anonymize": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_java_anon.dcm"},
        "to_image": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_java.png", "options": {"format": "png", "frame": 0}},
        "transcode": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_java_j2k.dcm", "options": {"syntax": "1.2.840.10008.1.2.4.90"}},
        "validate": {"input": DEFAULT_FILE},
        "stats": {"input": DEFAULT_FILE, "options": {"bins": 16}},
        "dump": {"input": DEFAULT_FILE, "options": {"max_width": 120}},
        "echo": {"input": "", "options": {"host": "127.0.0.1", "port": 11112}},
    },
    "csharp": {
        "info": {"input": DEFAULT_FILE, "options": {"json": True}},
        "anonymize": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_csharp_anon.dcm"},
        "to_image": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_csharp.png", "options": {"format": "png", "frame": 0}},
        "transcode": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_csharp_j2k.dcm", "options": {"syntax": "1.2.840.10008.1.2.4.90"}},
        "validate": {"input": DEFAULT_FILE},
        "stats": {"input": DEFAULT_FILE, "options": {"bins": 16}},
        "dump": {"input": DEFAULT_FILE, "options": {"depth": 6, "max_value_len": 64}},
        "echo": {"input": "", "options": {"host": "127.0.0.1", "port": 11112}},
    },
    "js": {
        "info": {"input": DEFAULT_FILE, "options": {"json": True}},
        "anonymize": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_js_anon.dcm"},
        "to_image": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_js.png", "options": {"format": "png", "frame": 0}},
        "transcode": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_js_j2k.dcm", "options": {"syntax": "1.2.840.10008.1.2.4.90"}},
        "validate": {"input": DEFAULT_FILE},
        "stats": {"input": DEFAULT_FILE, "options": {"bins": 16}},
        "dump": {"input": DEFAULT_FILE, "options": {"max_value_len": 64}},
        "volume": {"input": DEFAULT_SERIES, "output": OUTPUT_DIR / "ui_js_volume.npy", "options": {"preview": True}},
        "nifti": {"input": DEFAULT_SERIES, "output": OUTPUT_DIR / "ui_js_volume.nii.gz", "options": {"no_compress": False}},
        "echo": {"input": "", "options": {"host": "127.0.0.1", "port": 11112}},
    },
}

# Suites skip network-dependent echo by default to remain self-contained
SUITE_OPS = {
    "python": ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump", "volume", "nifti"],
    "rust": ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump"],
    "cpp": ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump"],
    "java": ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump"],
    "csharp": ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump"],
    "js": ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump", "volume", "nifti"],
}

CANONICAL_OP_SPECS = {
    "info": {
        "input": "file",
        "output": "display",
        "description": "Reads and prints DICOM metadata.",
        "option_keys": ["json", "verbose"],
        "has_options": True,
    },
    "anonymize": {
        "input": "file",
        "output": "file",
        "description": "Generates an anonymized copy of the file.",
        "option_keys": [],
        "has_options": False,
    },
    "to_image": {
        "input": "file",
        "output": "file",
        "description": "Exports a frame as an image (PNG/JPEG).",
        "option_keys": ["format", "frame"],
        "has_options": True,
    },
    "transcode": {
        "input": "file",
        "output": "file",
        "description": "Converts the DICOM transfer syntax.",
        "option_keys": ["syntax"],
        "has_options": True,
    },
    "validate": {
        "input": "file",
        "output": "display",
        "description": "Performs basic file validation.",
        "option_keys": [],
        "has_options": False,
    },
    "echo": {
        "input": "none",
        "output": "display",
        "description": "Sends a C-ECHO/Ping to a PACS (no file required).",
        "option_keys": ["host", "port", "calling_aet", "called_aet", "timeout"],
        "has_options": True,
    },
    "stats": {
        "input": "file",
        "output": "display",
        "description": "Pixel statistics/histogram.",
        "option_keys": ["bins", "frame", "json", "pretty"],
        "has_options": True,
    },
    "dump": {
        "input": "file",
        "output": "display",
        "description": "Textual dump of the dataset.",
        "option_keys": ["depth", "max_value_len", "max_width"],
        "has_options": True,
    },
    "volume": {
        "input": "directory",
        "output": "file",
        "description": "Reconstructs a 3D volume from a folder/series.",
        "option_keys": ["preview", "metadata"],
        "has_options": True,
    },
    "nifti": {
        "input": "directory",
        "output": "file",
        "description": "Exports a series (folder) to NIfTI.",
        "option_keys": ["series_uid", "metadata", "no_compress"],
        "has_options": True,
    },
    "custom": {
        "input": "optional",
        "output": "file",
        "description": "Executes a custom command (use {input}/{output}).",
        "option_keys": ["custom_cmd"],
        "has_options": True,
    },
}

BACKEND_SPEC_OVERRIDES = {
    "python": {
        "stats": {"option_keys": ["bins"], "description": "Quick histogram via Python."},
        "dump": {"option_keys": ["max_value_len"], "description": "Textual dump via the Python CLI."},
        "volume": {"option_keys": ["preview", "metadata"], "description": "Produces .npy and metadata.json."},
        "nifti": {"option_keys": ["series_uid", "metadata", "no_compress"]},
        "echo": {"option_keys": ["host", "port", "calling_aet", "called_aet", "timeout"]},
    },
    "rust": {
        "to_image": {
            "option_keys": [
                "format",
                "frame",
                "window_center",
                "window_width",
                "normalize",
                "disable_modality_lut",
                "disable_voi_lut",
                "force_8bit",
                "force_16bit",
            ],
            "description": "Exports an image with window and LUT adjustments.",
        },
        "stats": {"option_keys": [], "has_options": False},
        "dump": {"option_keys": ["max_depth", "max_value_len"]},
        "echo": {"option_keys": ["host", "port"]},
    },
    "cpp": {
        "info": {"output": "directory", "has_options": False, "option_keys": [], "description": "Generates dump.txt in the folder."},
        "dump": {"output": "directory", "has_options": False, "option_keys": [], "description": "Dumps GDCM output to a file."},
        "stats": {"output": "directory", "has_options": False, "option_keys": [], "description": "Writes pixel_stats.txt."},
        "validate": {"output": "directory", "has_options": False},
        "anonymize": {"output": "directory"},
        "to_image": {"output": "directory"},
        "transcode": {"output": "directory", "option_keys": ["syntax"], "has_options": True},
    },
    "java": {
        "info": {"option_keys": ["json"], "description": "Metadata via dcm4che."},
        "stats": {"option_keys": ["bins", "json", "pretty"]},
        "dump": {"option_keys": ["max_width"]},
        "echo": {"option_keys": ["host", "port", "calling_aet", "called_aet", "timeout"]},
    },
    "csharp": {
        "transcode": {"option_keys": ["syntax"], "description": "Sets the output transfer syntax."},
        "dump": {"option_keys": ["max_depth", "max_value_len"]},
        "stats": {"option_keys": ["frame"], "description": "Frame statistics (JSON)."},
        "histogram": {"option_keys": ["bins", "frame"], "description": "Histogram per frame (JSON)."},
    },
    "js": {
        "volume": {"description": "JS shim → Python; produces an optional .npy file."},
        "nifti": {"description": "JS shim → Python; produces a .nii.gz file."},
    },
}

VTK_OPS = [
    "vtk_export",
    "vtk_nifti",
    "vtk_isosurface",
    "vtk_resample",
    "vtk_mask",
    "vtk_connectivity",
    "vtk_mip",
    "vtk_metadata",
    "vtk_stats",
    "vtk_viewer",
    "vtk_volume_render",
    "vtk_mpr_multi",
    "vtk_overlay",
    "vtk_stream",
    "test_vtk",
]
for _vtk_op in VTK_OPS:
        BACKEND_SPEC_OVERRIDES.setdefault("cpp", {})[_vtk_op] = {
            "input": "directory",
            "output": "directory",
            "description": "VTK demo: series folder → artifacts in the output.",
            "option_keys": [],
            "has_options": False,
        }


def get_operation_spec(backend: str, op: str) -> dict:
    backend_key = backend.lower()
    base = CANONICAL_OP_SPECS.get(op, {})
    override = BACKEND_SPEC_OVERRIDES.get(backend_key, {}).get(op, {})
    spec = {**base, **override}
    spec.setdefault("input", "file")
    spec.setdefault("output", "file")
    spec.setdefault("description", "")
    option_keys = list(spec.get("option_keys") or [])
    if "options" not in spec:
        default_opts = DEFAULTS.get(backend_key, {}).get(op, {}).get("options")
        if default_opts is not None:
            spec["options"] = default_opts
            if not option_keys:
                option_keys = list(default_opts.keys())
    spec["option_keys"] = option_keys
    if "has_options" not in spec:
        spec["has_options"] = bool(option_keys or spec.get("options"))
    spec.setdefault("output_required", False)
    return spec


class TkApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Dicom Tools – Unified UI (CLI/JSON)")
        self.status_var = tk.StringVar(value="Ready")
        self.preview_img = None
        self._build_form()

    def _build_form(self) -> None:
        frm = ttk.Frame(self.root, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        ttk.Label(frm, text="Backend").grid(row=0, column=0, sticky="w")
        self.backend = ttk.Combobox(frm, values=BACKENDS, state="readonly")
        self.backend.bind("<<ComboboxSelected>>", self._update_operations)
        self.backend.set(BACKENDS[0])
        self.backend.grid(row=0, column=1, sticky="ew")

        ttk.Label(frm, text="Library").grid(row=1, column=0, sticky="w")
        self.library = ttk.Combobox(frm, state="readonly")
        self.library.bind("<<ComboboxSelected>>", self._on_library_change)
        self.library.grid(row=1, column=1, sticky="ew")

        ttk.Label(frm, text="Operation").grid(row=2, column=0, sticky="w")
        self.operation = ttk.Combobox(frm, state="readonly")
        self.operation.bind("<<ComboboxSelected>>", self._on_operation_change)
        self.operation.grid(row=2, column=1, sticky="ew")

        self.input_label = ttk.Label(frm, text="Input")
        self.input_label.grid(row=3, column=0, sticky="w")
        self.input_entry = ttk.Entry(frm)
        self.input_entry.grid(row=3, column=1, sticky="ew")
        self.input_browse_btn = ttk.Button(frm, text="Browse", command=self._browse_input)
        self.input_browse_btn.grid(row=3, column=2, padx=4)

        self.output_label = ttk.Label(frm, text="Output (optional)")
        self.output_label.grid(row=4, column=0, sticky="w")
        self.output_entry = ttk.Entry(frm)
        self.output_entry.grid(row=4, column=1, sticky="ew")
        self.output_browse_btn = ttk.Button(frm, text="Browse", command=self._browse_output)
        self.output_browse_btn.grid(row=4, column=2, padx=4)

        self.options_label = ttk.Label(frm, text="Options JSON (optional)")
        self.options_label.grid(row=5, column=0, sticky="w")
        self.options_text = tk.Text(frm, height=5, width=60)
        self.options_text.insert("1.0", "{}")
        self.options_text.grid(row=5, column=1, columnspan=2, sticky="nsew", pady=4)

        ttk.Label(frm, text="Custom command").grid(row=6, column=0, sticky="w")
        self.custom_cmd_entry = ttk.Entry(frm)
        self.custom_cmd_entry.grid(row=6, column=1, columnspan=2, sticky="ew")

        ttk.Button(frm, text="Load defaults", command=self._load_defaults).grid(row=6, column=0, sticky="w", pady=6)
        self.run_button = ttk.Button(frm, text="Run", command=self._run)
        self.run_button.grid(row=6, column=1, sticky="e", pady=6)
        ttk.Button(frm, text="Run full suite", command=self._run_suite).grid(row=6, column=2, sticky="e", pady=6)

        self.hint_label = ttk.Label(frm, text="", foreground="gray", wraplength=680)
        self.hint_label.grid(row=7, column=0, columnspan=3, sticky="w", pady=(2, 4))

        ttk.Label(frm, text="Result").grid(row=8, column=0, sticky="nw")
        self.result_text = tk.Text(frm, height=18, width=80)
        self.result_text.grid(row=8, column=1, columnspan=2, sticky="nsew")

        ttk.Label(frm, text="Status").grid(row=9, column=0, sticky="w")
        self.status_label = ttk.Label(frm, textvariable=self.status_var)
        self.status_label.grid(row=9, column=1, sticky="w")

        ttk.Label(frm, text="Preview (image)").grid(row=10, column=0, sticky="nw")
        self.preview_label = ttk.Label(frm)
        self.preview_label.grid(row=10, column=1, columnspan=2, sticky="w")

        for col in range(3):
            frm.columnconfigure(col, weight=1)
        frm.rowconfigure(8, weight=1)
        self._update_operations()

    def _browse_input(self) -> None:
        spec = self._current_spec()
        input_kind = spec.get("input")
        if input_kind == "none":
            return
        if input_kind == "directory":
            path = filedialog.askdirectory()
        else:
            path = filedialog.askopenfilename()
        if path:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, path)

    def _browse_output(self) -> None:
        spec = self._current_spec()
        output_kind = spec.get("output")
        if output_kind == "display":
            return
        if output_kind == "directory":
            path = filedialog.askdirectory()
        else:
            path = filedialog.asksaveasfilename()
        if path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, path)

    def _update_operations(self, *_args) -> None:
        backend = self.backend.get().lower()
        self._update_library_options(backend)
        self._update_operations_list(backend, self.library.get())

    def _update_library_options(self, backend: str) -> None:
        libs = BACKEND_LIBRARIES.get(backend, {})
        if len(libs) > 1:
            values = ["All"] + list(libs.keys())
            default = "All"
        elif libs:
            values = list(libs.keys())
            default = values[0]
        else:
            values = ["Default"]
            default = "Default"
        self.library["values"] = values
        if not self.library.get() or self.library.get() not in values:
            self.library.set(default)

    def _on_library_change(self, *_args) -> None:
        backend = self.backend.get().lower()
        self._update_operations_list(backend, self.library.get())

    def _ops_for_backend(self, backend: str, library: str | None) -> list[str]:
        libs = BACKEND_LIBRARIES.get(backend, {})
        if library and library not in {"All", "Default"}:
            return libs.get(library, [])
        if libs:
            ops: list[str] = []
            for items in libs.values():
                ops.extend(items)
            return list(dict.fromkeys(ops))  # preserve order
        return BACKEND_OPS.get(backend, [])

    def _update_operations_list(self, backend: str, library: str | None) -> None:
        ops = self._ops_for_backend(backend, library)
        self.operation["values"] = ops
        if ops:
            self.operation.set(ops[0])
        self._apply_operation_spec()

    def _on_operation_change(self, *_args) -> None:
        self._apply_operation_spec()

    def _current_spec(self) -> dict:
        backend = self.backend.get() if hasattr(self.backend, "get") else ""
        op = self.operation.get() if hasattr(self.operation, "get") else ""
        return get_operation_spec(backend, op)

    def _requires_input(self, spec: dict, op: str) -> bool:
        if op == "custom":
            return False
        return spec.get("input") not in {"none", "optional"}

    # Compatibilidade com testes antigos
    def _require_input(self, op: str) -> bool:
        backend = self.backend.get() if hasattr(self.backend, "get") else ""
        spec = get_operation_spec(backend, op)
        return self._requires_input(spec, op)

    def _op_uses_directory_input(self, op: str) -> bool:
        return get_operation_spec(self.backend.get(), op).get("input") == "directory"

    def _apply_operation_spec(self) -> None:
        spec = self._current_spec()
        self._toggle_custom_field()
        self._update_input_controls(spec)
        self._update_output_controls(spec)
        self._update_options_controls(spec)
        self._update_hint(spec)

    def _update_input_controls(self, spec: dict) -> None:
        input_kind = spec.get("input")
        label = "Input"
        if input_kind == "directory":
            label = "Input (folder/series)"
        elif input_kind == "file":
            label = "Input (file)"
        elif input_kind == "optional":
            label = "Input (optional)"
        elif input_kind == "none":
            label = "Input (not required)"
        self.input_label.configure(text=label)
        input_disabled = input_kind == "none"
        self.input_entry.configure(state="disabled" if input_disabled else "normal")
        self.input_browse_btn.state(["disabled"] if input_disabled else ["!disabled"])
        if input_disabled:
            self.input_entry.delete(0, tk.END)

    def _update_output_controls(self, spec: dict) -> None:
        output_kind = spec.get("output")
        label = "Output"
        if output_kind == "display":
            label = "Output (display only)"
            self.output_entry.delete(0, tk.END)
            self.output_entry.configure(state="disabled")
            self.output_browse_btn.state(["disabled"])
            self.preview_img = None
            self.preview_label.configure(image="", text="")
        elif output_kind == "directory":
            label = "Output (folder)"
            self.output_entry.configure(state="normal")
            self.output_browse_btn.state(["!disabled"])
        else:
            label = "Output (file"
            if not spec.get("output_required"):
                label += " optional"
            label += ")"
            self.output_entry.configure(state="normal")
            self.output_browse_btn.state(["!disabled"])
        self.output_label.configure(text=label)

    def _update_options_controls(self, spec: dict) -> None:
        option_keys = spec.get("option_keys") or []
        has_options = spec.get("has_options", False)
        if option_keys:
            label = f"Options JSON ({', '.join(option_keys)})"
        elif has_options:
            label = "Options JSON"
        else:
            label = "Options JSON (not applicable)"
        self.options_label.configure(text=label)
        if has_options:
            self.options_text.configure(state="normal")
            current_text = self.options_text.get("1.0", tk.END).strip()
            if current_text in ("", "{}") and spec.get("options") is not None:
                self._set_options_text(spec.get("options") or {})
        else:
            self._set_options_text({})
            self.options_text.configure(state="disabled")

    def _set_options_text(self, data: dict) -> None:
        self.options_text.configure(state="normal")
        self.options_text.delete("1.0", tk.END)
        self.options_text.insert("1.0", json.dumps(data or {}, indent=2))

    def _spec_hint(self, spec: dict) -> str:
        backend = self.backend.get() if hasattr(self.backend, "get") else ""
        library = self.library.get() if hasattr(self, "library") and hasattr(self.library, "get") else ""
        input_map = {
            "file": "Single file",
            "directory": "Folder/series (multiple files)",
            "none": "No input",
            "optional": "Optional input",
        }
        output_map = {"display": "Display only", "file": "Output file", "directory": "Output folder"}
        options = ", ".join(spec.get("option_keys") or []) or "no options"
        base = f"Input: {input_map.get(spec.get('input'), 'File/folder')} | Output: {output_map.get(spec.get('output'), 'File')}"
        desc = spec.get("description", "").strip()
        hint = f"{base} | Options: {options}"
        if desc:
            hint = f"{hint} | {desc}"
        prefix = []
        if backend:
            prefix.append(f"Backend: {backend}")
        if library and library not in {"All", "Default"}:
            prefix.append(f"Lib: {library}")
        if prefix:
            hint = f"{' · '.join(prefix)} | {hint}"
        return hint

    def _update_hint(self, spec: dict) -> None:
        self.hint_label.configure(text=self._spec_hint(spec))

    def _prepare_output_path(self, output: str | None, spec: dict) -> None:
        if not output:
            return
        out_path = Path(output)
        if spec.get("output") == "directory":
            out_path.mkdir(parents=True, exist_ok=True)
        else:
            out_path.parent.mkdir(parents=True, exist_ok=True)

    def _toggle_custom_field(self) -> None:
        op = self.operation.get()
        state = "normal" if op == "custom" else "disabled"
        self.custom_cmd_entry.configure(state=state)
        if op != "custom":
            self.custom_cmd_entry.delete(0, tk.END)

    def _normalize_output(self, op: str, input_path: str, output_path: str | None, spec: dict | None = None) -> str | None:
        """If the user selected a directory, infer a file name based on op and input."""
        if spec is None:
            backend = self.backend.get() if hasattr(self.backend, "get") else ""
            spec = get_operation_spec(backend, op)
        if not output_path or spec.get("output") == "display":
            return None
        if spec.get("output") == "directory":
            return str(Path(output_path))
        out = Path(output_path)
        if out.is_dir():
            stem = Path(input_path).stem or "output"
            if op == "to_image":
                return str(out / f"{stem}.png")
            if op == "anonymize":
                return str(out / f"{stem}_anon.dcm")
            if op == "transcode":
                return str(out / f"{stem}_transcoded.dcm")
            if op == "volume":
                return str(out / f"{stem}_volume.npy")
            if op == "nifti":
                return str(out / f"{stem}_volume.nii.gz")
            return str(out / stem)
        return str(out)

    def _parse_options(self) -> dict:
        text_widget = self.options_text
        state = "normal"
        if hasattr(text_widget, "cget"):
            try:
                state = str(text_widget.cget("state"))
            except Exception:
                state = "normal"
        if state == "disabled" and hasattr(text_widget, "configure"):
            text_widget.configure(state="normal")
            text = text_widget.get("1.0", tk.END).strip()
            text_widget.configure(state="disabled")
        else:
            text = text_widget.get("1.0", tk.END).strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            messagebox.showerror("Options JSON Error", str(exc))
            return {}

    def _run(self) -> None:
        backend = self.backend.get()
        op = self.operation.get()
        input_path = self.input_entry.get().strip()
        output_path = self.output_entry.get().strip() or None
        options = self._parse_options()
        spec = self._current_spec()

        if self._requires_input(spec, op) and not input_path:
            messagebox.showerror("Error", "Provide the input path")
            return
        if self._requires_input(spec, op) and not Path(input_path).exists():
            messagebox.showerror("Error", f"Input path does not exist:\n{input_path}")
            return
        if self._requires_input(spec, op) and spec.get("input") == "directory" and not Path(input_path).is_dir():
            messagebox.showerror("Error", "This operation expects a folder/series as input.")
            return
        if self._requires_input(spec, op) and spec.get("input") == "file" and Path(input_path).is_dir():
            messagebox.showerror("Error", "This operation expects a single file as input.")
            return
        if spec.get("input") == "none" and not input_path:
            input_path = ""

        if spec.get("output") == "directory" and output_path:
            existing = Path(output_path)
            if existing.exists() and existing.is_file():
                messagebox.showerror("Error", "Please select a folder for this operation's output.")
                return

        try:
            adapter = get_adapter(backend)
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return

        normalized_output = self._normalize_output(op, input_path, output_path, spec)
        self._prepare_output_path(normalized_output, spec)
        request = {
            "backend": backend,
            "op": op,
            "input": input_path,
            "output": normalized_output,
            "options": options,
        }
        if op == "custom":
            request["options"] = {**options, "custom_cmd": self.custom_cmd_entry.get().strip()}

        self._set_status("Running...")
        self.run_button.state(["disabled"])
        try:
            result = adapter.handle(request)
            self._render_result(result)
        except Exception as exc:
            messagebox.showerror("Execution error", str(exc))
            self._set_status("Failure")
        finally:
            self.run_button.state(["!disabled"])

    def _load_defaults(self) -> None:
        backend = self.backend.get().lower()
        op = self.operation.get()
        defaults = DEFAULTS.get(backend, {}).get(op)
        if not defaults:
            messagebox.showinfo("Info", "No defaults available for this combination.")
            return
        input_path = defaults.get("input")
        output_path = defaults.get("output")
        options = defaults.get("options", {})
        self.input_entry.delete(0, tk.END)
        if input_path:
            self.input_entry.insert(0, str(input_path))
        self.output_entry.delete(0, tk.END)
        if output_path:
            self.output_entry.insert(0, str(output_path))
        self._set_options_text(options)
        self._apply_operation_spec()
        self._set_status("Defaults loaded")

    def _run_suite(self) -> None:
        backend = self.backend.get().lower()
        ops = SUITE_OPS.get(backend, [])
        if not ops:
            messagebox.showinfo("Info", "No suite defined for this backend.")
            return
        try:
            adapter = get_adapter(backend)
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return

        suite_results = []
        self._set_status(f"Running suite ({backend})...")
        for op in ops:
            spec = get_operation_spec(backend, op)
            defaults = DEFAULTS.get(backend, {}).get(op, {})
            input_path = str(defaults.get("input", ""))
            output_path = defaults.get("output")
            options = defaults.get("options", {})

            if self._requires_input(spec, op):
                if not input_path or not Path(input_path).exists():
                    suite_results.append({"op": op, "ok": False, "error": f"Missing input for {op}"})
                    continue
                if spec.get("input") == "directory" and not Path(input_path).is_dir():
                    suite_results.append({"op": op, "ok": False, "error": f"Input must be a folder for {op}"})
                    continue
            elif spec.get("input") == "none" and not input_path:
                input_path = ""

            if spec.get("output") == "directory" and output_path:
                existing_out = Path(output_path)
                if existing_out.exists() and existing_out.is_file():
                    suite_results.append({"op": op, "ok": False, "error": "Output must be a folder"})
                    continue

            normalized_output = self._normalize_output(op, input_path, str(output_path) if output_path else None, spec)
            self._prepare_output_path(normalized_output, spec)

            request = {
                "backend": backend,
                "op": op,
                "input": input_path,
                "output": normalized_output,
                "options": options,
            }
            if op == "custom":
                request["options"] = {**options, "custom_cmd": self.custom_cmd_entry.get().strip()}

            try:
                result = adapter.handle(request)
                suite_results.append({"op": op, **(result.as_dict() if hasattr(result, "as_dict") else dict(result))})
            except Exception as exc:  # noqa: BLE001 - we want to capture any failure for the UI
                suite_results.append({"op": op, "ok": False, "error": str(exc)})

        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, json.dumps(suite_results, indent=2, ensure_ascii=False))
        failures = [r for r in suite_results if not r.get("ok", True)]
        if failures:
            self._set_status(f"Suite completed with failures ({len(failures)})")
            messagebox.showwarning("Suite failures", f"{len(failures)} operations failed. See details in the result.")
        else:
            self._set_status("Suite completed successfully")
            messagebox.showinfo("Success", f"Suite {backend} ran successfully.")

    def _render_result(self, result) -> None:
        payload = result.as_dict() if hasattr(result, "as_dict") else result
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, json.dumps(payload, indent=2, ensure_ascii=False))

        if not result.ok:
            messagebox.showwarning("Failure", f"Command returned exit code {result.returncode}")
            self._set_status("Failure")
        else:
            self._set_status("Success")
        self._render_preview(result)

    def _render_preview(self, result) -> None:
        # Show first generated image (png/pgm/ppm/jpeg)
        self.preview_img = None
        self.preview_label.configure(image="", text="")
        files = getattr(result, "output_files", []) or []
        for file in files:
            path = Path(file)
            if path.suffix.lower() in IMAGE_EXTS and path.exists():
                try:
                    self.preview_img = tk.PhotoImage(file=str(path))
                    self.preview_label.configure(image=self.preview_img, text="")
                except Exception:
                    self.preview_label.configure(text=f"Preview unavailable: {path.name}")
                break

    def _set_status(self, msg: str) -> None:
        self.status_var.set(msg)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    TkApp().run()

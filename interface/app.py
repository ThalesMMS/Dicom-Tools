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
    "python": ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump", "volume", "nifti", "echo"],
    "rust": ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump", "echo"],
    "cpp": ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump"],
    "java": ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump", "echo"],
    "csharp": ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump", "echo"],
    "js": ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump", "volume", "nifti", "echo"],
}

# Default recipes for each backend/op so the UI can run a full suite quickly
DEFAULTS = {
    "python": {
        "info": {"input": DEFAULT_FILE, "options": {"json": True}},
        "anonymize": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_python_anon.dcm"},
        "to_image": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_python.png", "options": {"format": "png", "frame": 0}},
        "transcode": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_python_j2k.dcm", "options": {"syntax": "1.2.840.10008.1.2.4.90"}},
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
        "transcode": {"input": DEFAULT_FILE, "output": OUTPUT_DIR / "ui_cpp_j2k.dcm", "options": {"syntax": "1.2.840.10008.1.2.4.90"}},
        "validate": {"input": DEFAULT_FILE},
        "stats": {"input": DEFAULT_FILE},
        "dump": {"input": DEFAULT_FILE},
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


class TkApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Dicom Tools – UI unificada (CLI/JSON)")
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

        ttk.Label(frm, text="Operação").grid(row=1, column=0, sticky="w")
        self.operation = ttk.Combobox(frm, state="readonly")
        self.operation.grid(row=1, column=1, sticky="ew")
        self._update_operations()

        ttk.Label(frm, text="Entrada").grid(row=2, column=0, sticky="w")
        self.input_entry = ttk.Entry(frm)
        self.input_entry.grid(row=2, column=1, sticky="ew")
        ttk.Button(frm, text="Selecionar", command=self._browse_input).grid(row=2, column=2, padx=4)

        ttk.Label(frm, text="Saída (opcional)").grid(row=3, column=0, sticky="w")
        self.output_entry = ttk.Entry(frm)
        self.output_entry.grid(row=3, column=1, sticky="ew")
        ttk.Button(frm, text="Selecionar", command=self._browse_output).grid(row=3, column=2, padx=4)

        ttk.Label(frm, text="Options JSON (opcional)").grid(row=4, column=0, sticky="w")
        self.options_text = tk.Text(frm, height=5, width=60)
        self.options_text.insert("1.0", "{}")
        self.options_text.grid(row=4, column=1, columnspan=2, sticky="nsew", pady=4)

        ttk.Button(frm, text="Carregar defaults", command=self._load_defaults).grid(row=5, column=0, sticky="w", pady=6)
        self.run_button = ttk.Button(frm, text="Executar", command=self._run)
        self.run_button.grid(row=5, column=1, sticky="e", pady=6)
        ttk.Button(frm, text="Rodar suíte completa", command=self._run_suite).grid(row=5, column=2, sticky="e", pady=6)

        ttk.Label(frm, text="Resultado").grid(row=6, column=0, sticky="nw")
        self.result_text = tk.Text(frm, height=18, width=80)
        self.result_text.grid(row=6, column=1, columnspan=2, sticky="nsew")

        ttk.Label(frm, text="Status").grid(row=7, column=0, sticky="w")
        self.status_label = ttk.Label(frm, textvariable=self.status_var)
        self.status_label.grid(row=7, column=1, sticky="w")

        ttk.Label(frm, text="Preview (imagem)").grid(row=8, column=0, sticky="nw")
        self.preview_label = ttk.Label(frm)
        self.preview_label.grid(row=8, column=1, columnspan=2, sticky="w")

        for col in range(3):
            frm.columnconfigure(col, weight=1)
        frm.rowconfigure(6, weight=1)

    def _browse_input(self) -> None:
        path = filedialog.askopenfilename()
        if path:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, path)

    def _browse_output(self) -> None:
        path = filedialog.asksaveasfilename()
        if path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, path)

    def _update_operations(self, *_args) -> None:
        backend = self.backend.get().lower()
        ops = BACKEND_OPS.get(backend, [])
        self.operation["values"] = ops
        if ops:
            self.operation.set(ops[0])

    def _require_input(self, op: str) -> bool:
        # echo não precisa de input; os demais sim (arquivo ou diretório)
        return op not in {"echo"}

    def _parse_options(self) -> dict:
        text = self.options_text.get("1.0", tk.END).strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            messagebox.showerror("Erro no JSON de options", str(exc))
            return {}

    def _run(self) -> None:
        backend = self.backend.get()
        op = self.operation.get()
        input_path = self.input_entry.get().strip()
        output_path = self.output_entry.get().strip() or None
        options = self._parse_options()

        if self._require_input(op) and not input_path:
            messagebox.showerror("Erro", "Informe o caminho de entrada")
            return

        if self._require_input(op) and not Path(input_path).exists():
            messagebox.showerror("Erro", f"Caminho de entrada não existe:\n{input_path}")
            return

        try:
            adapter = get_adapter(backend)
        except ValueError as exc:
            messagebox.showerror("Erro", str(exc))
            return

        request = {
            "backend": backend,
            "op": op,
            "input": input_path,
            "output": output_path,
            "options": options,
        }

        self._set_status("Executando...")
        self.run_button.state(["disabled"])
        try:
            result = adapter.handle(request)
            self._render_result(result)
        except Exception as exc:
            messagebox.showerror("Erro de execução", str(exc))
            self._set_status("Falha")
        finally:
            self.run_button.state(["!disabled"])

    def _load_defaults(self) -> None:
        backend = self.backend.get().lower()
        op = self.operation.get()
        defaults = DEFAULTS.get(backend, {}).get(op)
        if not defaults:
            messagebox.showinfo("Info", "Nenhum default disponível para esta combinação.")
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
        self.options_text.delete("1.0", tk.END)
        self.options_text.insert(tk.END, json.dumps(options, indent=2))
        self._set_status("Defaults carregados")

    def _run_suite(self) -> None:
        backend = self.backend.get().lower()
        ops = SUITE_OPS.get(backend, [])
        if not ops:
            messagebox.showinfo("Info", "Nenhuma suíte definida para este backend.")
            return
        try:
            adapter = get_adapter(backend)
        except ValueError as exc:
            messagebox.showerror("Erro", str(exc))
            return

        suite_results = []
        self._set_status(f"Rodando suíte ({backend})...")
        for op in ops:
            defaults = DEFAULTS.get(backend, {}).get(op, {})
            input_path = str(defaults.get("input", ""))
            output_path = defaults.get("output")
            options = defaults.get("options", {})

            if self._require_input(op):
                if not input_path or not Path(input_path).exists():
                    suite_results.append({"op": op, "ok": False, "error": f"Entrada ausente para {op}"})
                    continue
            if output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            request = {
                "backend": backend,
                "op": op,
                "input": input_path,
                "output": str(output_path) if output_path else None,
                "options": options,
            }

            try:
                result = adapter.handle(request)
                suite_results.append({"op": op, **(result.as_dict() if hasattr(result, "as_dict") else dict(result))})
            except Exception as exc:  # noqa: BLE001 - we want to capture any failure for the UI
                suite_results.append({"op": op, "ok": False, "error": str(exc)})

        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, json.dumps(suite_results, indent=2, ensure_ascii=False))
        failures = [r for r in suite_results if not r.get("ok", True)]
        if failures:
            self._set_status(f"Suíte finalizada com falhas ({len(failures)})")
            messagebox.showwarning("Suíte com falhas", f"{len(failures)} operações falharam. Ver detalhes no resultado.")
        else:
            self._set_status("Suíte finalizada com sucesso")
            messagebox.showinfo("Sucesso", f"Suíte {backend} executada com sucesso.")

    def _render_result(self, result) -> None:
        payload = result.as_dict() if hasattr(result, "as_dict") else result
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, json.dumps(payload, indent=2, ensure_ascii=False))

        if not result.ok:
            messagebox.showwarning("Falha", f"Comando retornou código {result.returncode}")
            self._set_status("Falha")
        else:
            self._set_status("Sucesso")
        self._render_preview(result)

    def _render_preview(self, result) -> None:
        # Exibe primeira imagem gerada (png/pgm/ppm/jpeg)
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
                    self.preview_label.configure(text=f"Pré-visualização indisponível: {path.name}")
                break

    def _set_status(self, msg: str) -> None:
        self.status_var.set(msg)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    TkApp().run()

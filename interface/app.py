import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from interface.adapters import get_adapter
from interface.config import BACKENDS, DEFAULT_FILE, DEFAULT_SERIES, IMAGE_EXTS, OUTPUT_DIR, ROOT_DIR
from interface.operations import (
    BACKEND_LIBRARIES,
    BACKEND_OPS,
    BACKEND_SPEC_OVERRIDES,
    CANONICAL_OP_SPECS,
    DEFAULTS,
    SUITE_OPS,
    VTK_OPS,
    build_spec_hint,
    get_operation_spec,
    normalize_output_path,
    requires_input,
    uses_directory_input,
)
from interface.services.execution import execute_operation, execute_suite, prepare_request, validate_request


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
        if libs:
            values = list(libs.keys())
            if len(values) > 1 and "Todos" not in values:
                values = ["Todos"] + values
            default = "Todos" if "Todos" in values else values[0]
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
        if library and library in libs:
            return libs.get(library, [])
        if library and library not in {"Todos", "All", "Default"}:
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
        return requires_input(spec, op)

    # Compatibilidade com testes antigos
    def _require_input(self, op: str) -> bool:
        backend = self.backend.get() if hasattr(self.backend, "get") else ""
        spec = get_operation_spec(backend, op)
        return self._requires_input(spec, op)

    def _op_uses_directory_input(self, op: str) -> bool:
        return uses_directory_input(get_operation_spec(self.backend.get(), op))

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
            label = "Output (file)"
            if not spec.get("output_required"):
                label = "Output (file optional)"
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
        return build_spec_hint(spec, backend, library)

    def _update_hint(self, spec: dict) -> None:
        self.hint_label.configure(text=self._spec_hint(spec))

    def _toggle_custom_field(self) -> None:
        op = self.operation.get()
        state = "normal" if op == "custom" else "disabled"
        self.custom_cmd_entry.configure(state=state)
        if op != "custom":
            self.custom_cmd_entry.delete(0, tk.END)

    def _normalize_output(self, op: str, input_path: str, output_path: str | None, spec: dict | None = None) -> str | None:
        if spec is None:
            backend = self.backend.get() if hasattr(self.backend, "get") else ""
            spec = get_operation_spec(backend, op)
        return normalize_output_path(op, input_path, output_path, spec)

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

        error = validate_request(op, input_path, output_path, spec)
        if error:
            messagebox.showerror("Error", error)
            return

        try:
            adapter = get_adapter(backend)
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return

        if op == "custom":
            options = {**options, "custom_cmd": self.custom_cmd_entry.get().strip()}
        request = prepare_request(backend, op, input_path, output_path, options, spec)

        self._set_status("Running...")
        self.run_button.state(["disabled"])
        try:
            result = execute_operation(adapter, request)
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

        self._set_status(f"Running suite ({backend})...")
        suite_results = execute_suite(backend, ops, lambda op: DEFAULTS.get(backend, {}).get(op, {}), adapter=adapter)

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

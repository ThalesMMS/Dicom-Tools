import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .adapters import get_adapter


BACKENDS = ["python", "rust", "cpp"]
OPERATIONS = ["info", "anonymize", "to_image", "transcode", "validate", "echo", "stats", "dump", "volume", "nifti"]
IMAGE_EXTS = {".png", ".pgm", ".ppm", ".jpg", ".jpeg"}


class TkApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Dicom Tools – UI unificada (CLI/JSON)")
        self.status_var = tk.StringVar(value="Pronto")
        self.preview_img = None
        self._build_form()

    def _build_form(self) -> None:
        frm = ttk.Frame(self.root, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        ttk.Label(frm, text="Backend").grid(row=0, column=0, sticky="w")
        self.backend = ttk.Combobox(frm, values=BACKENDS, state="readonly")
        self.backend.set(BACKENDS[0])
        self.backend.grid(row=0, column=1, sticky="ew")

        ttk.Label(frm, text="Operação").grid(row=1, column=0, sticky="w")
        self.operation = ttk.Combobox(frm, values=OPERATIONS, state="readonly")
        self.operation.set("info")
        self.operation.grid(row=1, column=1, sticky="ew")

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

        self.run_button = ttk.Button(frm, text="Executar", command=self._run)
        self.run_button.grid(row=5, column=1, sticky="e", pady=6)

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

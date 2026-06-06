#!/usr/bin/env python3
"""
Interactive interface to run Dicom-Tools-cpp tests.

- CLI mode: numeric menus to choose the library and test.
- GUI mode: simple Tkinter window (if available) with command selection.

Requires the compiled `DicomTools` binary (default: build/DicomTools).
"""

import argparse
import os
import shutil
import subprocess
import sys
import threading
from typing import Dict, List, Tuple

DEFAULT_EXECUTABLE = os.path.join("build", "DicomTools")
DEFAULT_INPUT = "input/dcm_series/IM-0001-0190.dcm"
DEFAULT_OUTPUT = "output"

COMMANDS: Dict[str, List[Tuple[str, str]]] = {
    "GDCM": [
        ("test-gdcm", "Run complete GDCM suite"),
        ("gdcm:tags", "Inspect basic tags"),
        ("gdcm:anonymize", "Anonymize patient"),
        ("gdcm:transcode-j2k", "Transcode JPEG2000"),
        ("gdcm:jpegls", "Transcode JPEG-LS"),
        ("gdcm:retag-uids", "Regenerate UIDs"),
        ("gdcm:dump", "Dump dataset to text"),
        ("gdcm:transcode-rle", "Transcode RLE"),
        ("gdcm:stats", "Pixel statistics"),
        ("gdcm:scan", "Index directory to CSV"),
        ("gdcm:preview", "Export PGM preview"),
    ],
    "DCMTK": [
        ("test-dcmtk", "Run complete DCMTK suite"),
        ("dcmtk:modify", "Modify basic tags"),
        ("dcmtk:ppm", "Export pixels (PPM)"),
        ("dcmtk:jpeg-lossless", "Reencode JPEG Lossless"),
        ("dcmtk:jpeg-baseline", "Reencode JPEG Baseline"),
        ("dcmtk:rle", "Reencode RLE"),
        ("dcmtk:raw-dump", "Dump raw buffer"),
        ("dcmtk:explicit-vr", "Rewrite Explicit VR"),
        ("dcmtk:metadata", "Export metadata"),
        ("dcmtk:bmp", "Preview BMP"),
        ("dcmtk:dicomdir", "Generate DICOMDIR"),
        ("dcmtk:seg", "Generate synthetic SEG"),
    ],
    "ITK": [
        ("test-itk", "Run complete ITK suite"),
        ("itk:canny", "Canny edge detection"),
        ("itk:gaussian", "Gaussian smoothing"),
        ("itk:median", "Median filter"),
        ("itk:threshold", "Threshold segmentation"),
        ("itk:otsu", "Otsu segmentation"),
        ("itk:connected-threshold", "Region growing"),
        ("itk:resample", "Resample to 1mm"),
        ("itk:aniso", "Anisotropic denoise"),
        ("itk:histogram", "Adaptive equalization"),
        ("itk:mip", "MIP axial"),
        ("itk:slice", "Central slice PNG"),
        ("itk:nrrd", "Export NRRD"),
        ("itk:nifti", "Export NIfTI"),
    ],
    "VTK": [
        ("test-vtk", "Run complete VTK suite"),
        ("vtk:export", "Export VTI"),
        ("vtk:nifti", "Export NIfTI"),
        ("vtk:isosurface", "Generate STL via marching cubes"),
        ("vtk:resample", "Resample to 1mm"),
        ("vtk:mask", "Threshold mask"),
        ("vtk:connectivity", "Label connectivity"),
        ("vtk:mip", "MIP axial"),
        ("vtk:metadata", "Export metadata"),
        ("vtk:stats", "Volume statistics"),
        ("vtk:viewer", "Snapshot viewer"),
    ],
}


def resolve_executable(path: str) -> str:
    expanded = os.path.expanduser(path)
    if os.path.exists(expanded):
        return expanded
    which = shutil.which(path)
    if which:
        return which
    alt = shutil.which("DicomTools")
    if alt:
        return alt
    raise FileNotFoundError(f"DicomTools executable not found at {path}")


def build_command(executable: str, command: str, input_path: str, output_dir: str, verbose: bool) -> List[str]:
    cmd = [executable, command]
    if input_path:
        cmd += ["-i", input_path]
    if output_dir:
        cmd += ["-o", output_dir]
    if verbose:
        cmd.append("-v")
    return cmd


def run_once(executable: str, command: str, input_path: str, output_dir: str, verbose: bool) -> int:
    cmd = build_command(executable, command, input_path, output_dir, verbose)
    print(f"\n> {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, check=False)
    except FileNotFoundError:
        print("Error: could not call binary. Confirm path in --exe.")
        return 1
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())
    if result.returncode == 0:
        print("Status: OK")
    else:
        print(f"Status: FAILED (code {result.returncode})")
    return result.returncode


def cli_menu(executable: str, input_path: str, output_dir: str, verbose: bool) -> None:
    print("CLI Interface - choose library and test.")
    print(f"Using binary: {executable}")
    print(f"Default input: {input_path}")
    print(f"Default output: {output_dir}")
    print("Type 'q' to exit at any time.")
    modules = list(COMMANDS.keys())
    while True:
        print("\nLibraries:")
        for idx, mod in enumerate(modules, start=1):
            print(f"  {idx}) {mod}")
        print("  0) Run all (command 'all')")
        choice = input("Select option: ").strip().lower()
        if choice in ("q", "quit", "exit"):
            return
        if choice == "0":
            run_once(executable, "all", input_path, output_dir, verbose)
            continue
        try:
            module = modules[int(choice) - 1]
        except (ValueError, IndexError):
            print("Invalid option.")
            continue
        commands = COMMANDS[module]
        while True:
            print(f"\n{module} - commands:")
            for idx, (cmd, desc) in enumerate(commands, start=1):
                print(f"  {idx}) {cmd:20} - {desc}")
            print("  0) Back")
            cmd_choice = input("Choose the command: ").strip().lower()
            if cmd_choice in ("q", "quit", "exit"):
                return
            if cmd_choice == "0":
                break
            try:
                cmd_name = commands[int(cmd_choice) - 1][0]
            except (ValueError, IndexError):
                print("Invalid option.")
                continue
            run_once(executable, cmd_name, input_path, output_dir, verbose)


def start_gui(executable: str, input_path: str, output_dir: str, verbose: bool) -> int:
    try:
        import tkinter as tk
        from tkinter import messagebox, ttk
    except Exception as exc:  # noqa: BLE001
        print(f"Tkinter unavailable ({exc}); use CLI mode.")
        return 1

    root = tk.Tk()
    root.title("Dicom-Tools Test Runner")
    root.geometry("680x520")

    module_var = tk.StringVar(value="GDCM")
    verbose_var = tk.BooleanVar(value=verbose)

    input_var = tk.StringVar(value=input_path)
    output_var = tk.StringVar(value=output_dir)
    exe_var = tk.StringVar(value=executable)

    def update_commands() -> None:
        listbox.delete(0, tk.END)
        for cmd, desc in COMMANDS[module_var.get()]:
            listbox.insert(tk.END, f"{cmd} | {desc}")
        listbox.selection_set(0)

    def log(msg: str) -> None:
        log_box.configure(state="normal")
        log_box.insert(tk.END, msg + "\n")
        log_box.see(tk.END)
        log_box.configure(state="disabled")

    def run_selected(command: str) -> None:
        resolved_exe = resolve_executable(exe_var.get())
        cmd = build_command(
            resolved_exe,
            command,
            os.path.expanduser(input_var.get()),
            os.path.expanduser(output_var.get()),
            verbose_var.get(),
        )

        def task() -> None:
            log(f"> {' '.join(cmd)}")
            try:
                result = subprocess.run(cmd, text=True, capture_output=True, check=False)
                output = (result.stdout or "").strip()
                error = (result.stderr or "").strip()
                status = "OK" if result.returncode == 0 else f"FAILED ({result.returncode})"
            except FileNotFoundError:
                output = ""
                error = "Could not find the binary. Adjust the Executable field."
                status = "FAILED"

            def finish() -> None:
                if output:
                    log(output)
                if error:
                    log(error)
                log(f"Status: {status}\n")
                if status.startswith("FAILED"):
                    messagebox.showerror("Execution error", error or status)
            root.after(0, finish)

        threading.Thread(target=task, daemon=True).start()

    def on_run_command() -> None:
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("Select a command", "Choose a command from the list.")
            return
        selected_text = listbox.get(selection[0])
        command = selected_text.split(" | ")[0]
        run_selected(command)

    def on_run_suite() -> None:
        module = module_var.get()
        suite_cmd = COMMANDS[module][0][0]
        run_selected(suite_cmd)

    def on_run_all() -> None:
        run_selected("all")

    top_frame = ttk.Frame(root, padding=10)
    top_frame.pack(fill="x")

    ttk.Label(top_frame, text="Executable").grid(row=0, column=0, sticky="w")
    ttk.Entry(top_frame, textvariable=exe_var, width=50).grid(row=0, column=1, sticky="we", padx=5)

    ttk.Label(top_frame, text="Input (-i)").grid(row=1, column=0, sticky="w")
    ttk.Entry(top_frame, textvariable=input_var, width=50).grid(row=1, column=1, sticky="we", padx=5)

    ttk.Label(top_frame, text="Output (-o)").grid(row=2, column=0, sticky="w")
    ttk.Entry(top_frame, textvariable=output_var, width=50).grid(row=2, column=1, sticky="we", padx=5)

    ttk.Checkbutton(top_frame, text="Verbose (-v)", variable=verbose_var).grid(row=3, column=1, sticky="w", pady=5)

    top_frame.columnconfigure(1, weight=1)

    middle_frame = ttk.Frame(root, padding=10)
    middle_frame.pack(fill="both", expand=True)

    ttk.Label(middle_frame, text="Library").grid(row=0, column=0, sticky="w")
    module_menu = ttk.OptionMenu(middle_frame, module_var, module_var.get(), *COMMANDS.keys(), command=lambda _: update_commands())
    module_menu.grid(row=0, column=1, sticky="w")

    listbox = tk.Listbox(middle_frame, height=12)
    listbox.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=5)
    scrollbar = ttk.Scrollbar(middle_frame, orient="vertical", command=listbox.yview)
    scrollbar.grid(row=1, column=2, sticky="ns")
    listbox.configure(yscrollcommand=scrollbar.set)

    button_frame = ttk.Frame(middle_frame)
    button_frame.grid(row=2, column=0, columnspan=2, sticky="we", pady=5)
    ttk.Button(button_frame, text="Run selected command", command=on_run_command).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Run library suite", command=on_run_suite).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Run ALL", command=on_run_all).pack(side="left", padx=5)

    middle_frame.rowconfigure(1, weight=1)
    middle_frame.columnconfigure(1, weight=1)

    log_frame = ttk.Frame(root, padding=10)
    log_frame.pack(fill="both", expand=True)
    ttk.Label(log_frame, text="Log").pack(anchor="w")
    log_box = tk.Text(log_frame, height=10, state="disabled")
    log_box.pack(fill="both", expand=True)

    update_commands()
    root.mainloop()
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interactive interface for Dicom-Tools-cpp.")
    parser.add_argument("--exe", default=DEFAULT_EXECUTABLE, help="Path to the DicomTools binary.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Path to the DICOM file/directory for -i.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output directory for -o.")
    parser.add_argument("--verbose", action="store_true", help="Enable the binary's -v flag.")
    parser.add_argument("--gui", action="store_true", help="Open the Tkinter GUI (if available).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        executable = resolve_executable(args.exe)
    except FileNotFoundError as exc:
        print(exc)
        return 1

    if args.gui:
        return start_gui(executable, args.input, args.output, args.verbose)

    cli_menu(executable, args.input, args.output, args.verbose)
    return 0


if __name__ == "__main__":
    sys.exit(main())

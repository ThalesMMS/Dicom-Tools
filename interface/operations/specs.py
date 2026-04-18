from pathlib import Path

from .catalog import BACKEND_SPEC_OVERRIDES, CANONICAL_OP_SPECS, DEFAULTS


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


def requires_input(spec: dict, op: str) -> bool:
    if op == "custom":
        return False
    return spec.get("input") not in {"none", "optional"}


def uses_directory_input(spec: dict) -> bool:
    return spec.get("input") == "directory"


def normalize_output_path(op: str, input_path: str, output_path: str | None, spec: dict) -> str | None:
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


def build_spec_hint(spec: dict, backend: str, library: str) -> str:
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

from pathlib import Path

from ..adapters import get_adapter
from ..operations import get_operation_spec, normalize_output_path, requires_input, uses_directory_input


def validate_request(op: str, input_path: str, output_path: str | None, spec: dict) -> str | None:
    if spec.get("output_required") and not output_path:
        return "Provide the output path for this operation."
    if requires_input(spec, op):
        if not input_path:
            return "Provide the input path"
        p = Path(input_path)
        if not p.exists():
            return f"Input path does not exist:\n{input_path}"
        if uses_directory_input(spec) and not p.is_dir():
            return "This operation expects a folder/series as input."
        if spec.get("input") == "file" and p.is_dir():
            return "This operation expects a single file as input."
    if spec.get("output") == "directory" and output_path:
        existing = Path(output_path)
        if existing.exists() and existing.is_file():
            return "Please select a folder for this operation's output."
    return None


def prepare_request(backend: str, op: str, input_path: str, output_path: str | None, options: dict, spec: dict) -> dict:
    request_input = input_path
    if spec.get("input") == "none" and not request_input:
        request_input = ""
    normalized_output = normalize_output_path(op, request_input, output_path, spec)
    if normalized_output:
        out_path = Path(normalized_output)
        if spec.get("output") == "directory":
            out_path.mkdir(parents=True, exist_ok=True)
        else:
            out_path.parent.mkdir(parents=True, exist_ok=True)
    return {
        "backend": backend,
        "op": op,
        "input": request_input,
        "output": normalized_output,
        "options": options,
    }


def execute_operation(adapter, request: dict):
    return adapter.handle(request)


def execute_suite(backend: str, ops: list[str], get_defaults_fn, adapter=None) -> list[dict]:
    backend_key = backend.lower()
    if not ops:
        return []
    adapter = adapter or get_adapter(backend_key)
    suite_results = []
    for op in ops:
        spec = get_operation_spec(backend_key, op)
        defaults = get_defaults_fn(op) or {}
        input_path = str(defaults.get("input", ""))
        output_path = defaults.get("output")
        output_value = str(output_path) if output_path is not None else None
        options = dict(defaults.get("options", {}))

        error = validate_request(op, input_path, output_value, spec)
        if error:
            suite_results.append({"op": op, "ok": False, "error": error})
            continue

        request = prepare_request(backend_key, op, input_path, output_value, options, spec)
        try:
            result = execute_operation(adapter, request)
            payload = result.as_dict() if hasattr(result, "as_dict") else dict(result)
            suite_results.append({"op": op, **payload})
        except Exception as exc:  # noqa: BLE001 - the UI wants a per-op failure entry
            suite_results.append({"op": op, "ok": False, "error": str(exc)})
    return suite_results
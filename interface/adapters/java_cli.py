import os
from pathlib import Path
from typing import Any, Dict, List

from .runner import RunResult, parse_json_maybe, run_process


class JavaCliAdapter:
    """Adapter para CLI Java (dcm4che). Usa o jar em java/dcm4che-tests/target/dcm4che-tests.jar."""

    def __init__(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        default_cmd = os.environ.get("JAVA_DICOM_TOOLS_CMD") or str(
            self.root / "java" / "dcm4che-tests" / "target" / "dcm4che-tests.jar"
        )
        # Assume java -jar <jar> <args>
        self.base_cmd: List[str] = ["java", "-jar", default_cmd]

    def handle(self, request: Dict[str, Any]) -> RunResult:
        op = request.get("op")
        options = request.get("options", {}) or {}
        input_path = request.get("input")
        output = request.get("output")

        no_input_ops = {"echo", "custom", "worklist", "qido", "wado"}
        requires_input = op not in no_input_ops
        if not op or (requires_input and not input_path):
            return RunResult(False, 1, "", "op e input são obrigatórios", [], None)

        cmd = self._build_cmd(op, input_path, output, options)
        if cmd is None:
            return RunResult(False, 1, "", f"operação não suportada pelo backend Java: {op}", [], None)

        result = run_process(cmd, cwd=self.root / "java")
        meta = parse_json_maybe(result.stdout)
        if meta is not None:
            result.metadata = meta
        result.backend = "java"
        result.operation = op
        if output:
            result.output_files.append(str(Path(output)))
        elif op == "wado":
            inferred_output = Path(input_path or "wado").with_suffix(".dcm")
            result.output_files.append(str(inferred_output))
        return result

    def _build_cmd(self, op: str, input_path: str, output: str | None, options: Dict[str, Any]) -> List[str] | None:
        if op == "info":
            return [*self.base_cmd, "info", input_path, "--json"]
        if op == "anonymize":
            inferred_output = output or str(Path(input_path).with_name(f"{Path(input_path).stem}_anon.dcm"))
            return [*self.base_cmd, "anonymize", input_path, "--output", inferred_output]
        if op == "to_image":
            inferred_output = output or str(Path(input_path).with_suffix(".png"))
            cmd = [*self.base_cmd, "to-image", input_path, "--output", inferred_output]
            if options.get("format"):
                cmd.extend(["--format", str(options["format"])])
            if options.get("frame") is not None:
                cmd.extend(["--frame", str(options["frame"])])
            return cmd
        if op == "transcode":
            inferred_output = output or str(Path(input_path).with_name(f"{Path(input_path).stem}_explicit.dcm"))
            syntax = options.get("syntax", "explicit")
            return [*self.base_cmd, "transcode", input_path, "--output", inferred_output, "--syntax", str(syntax)]
        if op == "validate":
            return [*self.base_cmd, "validate", input_path]
        if op == "echo":
            host = options.get("host", "127.0.0.1")
            port = options.get("port", 104)
            timeout = options.get("timeout", 2000)
            calling = options.get("calling_aet", "ECHO-SCU")
            called = options.get("called_aet", "ANY-SCP")
            return [
                *self.base_cmd,
                "echo",
                f"{host}:{port}",
                "--timeout",
                str(timeout),
                "--calling",
                calling,
                "--called",
                called,
            ]
        if op == "dump":
            cmd = [*self.base_cmd, "dump", input_path]
            if options.get("max_width") is not None:
                cmd.extend(["--max-width", str(options["max_width"])])
            return cmd
        if op == "stats":
            bins = options.get("bins", 256)
            cmd = [*self.base_cmd, "stats", input_path, "--bins", str(bins)]
            if options.get("json", True):
                cmd.append("--json")
            if options.get("pretty"):
                cmd.append("--pretty")
            return cmd
        if op == "histogram":
            bins = options.get("bins", 256)
            cmd = [*self.base_cmd, "stats", input_path, "--bins", str(bins), "--json"]
            if options.get("pretty"):
                cmd.append("--pretty")
            return cmd
        if op == "store_scu":
            host = options.get("host", "127.0.0.1")
            port = options.get("port", 11112)
            calling = options.get("calling_aet", "STORE-SCU")
            called = options.get("called_aet", "STORE-SCP")
            timeout = options.get("timeout", 2000)
            target = f"{host}:{port}"
            cmd = [*self.base_cmd, "store-scu", input_path, "--target", target, "--calling", calling, "--called", called]
            if timeout:
                cmd.extend(["--timeout", str(timeout)])
            return cmd
        if op == "worklist":
            host = options.get("host", "127.0.0.1")
            port = options.get("port", 11112)
            calling = options.get("calling_aet", "MWL-SCU")
            called = options.get("called_aet", "MWL-SCP")
            patient = options.get("patient")
            target = f"{host}:{port}"
            cmd = [*self.base_cmd, "mwl", target, "--calling", calling, "--called", called]
            if patient:
                cmd.extend(["--patient", str(patient)])
            return cmd
        if op == "qido":
            url = options.get("url") or "http://localhost:8080/dicomweb"
            return [*self.base_cmd, "qido", url]
        if op == "stow":
            url = options.get("url") or "http://localhost:8080/dicomweb"
            return [*self.base_cmd, "stow", url, input_path]
        if op == "wado":
            url = options.get("url") or "http://localhost:8080/dicomweb/wado"
            inferred_output = output or str(Path(input_path or "wado").with_suffix(".dcm"))
            return [*self.base_cmd, "wado", url, "--output", inferred_output]
        if op == "sr_summary":
            return [*self.base_cmd, "sr-summary", input_path]
        if op == "rt_check":
            plan = options.get("plan") or input_path
            if not plan:
                return None
            cmd = [*self.base_cmd, "rt-check", "--plan", str(plan)]
            if options.get("dose"):
                cmd.extend(["--dose", str(options["dose"])])
            if options.get("struct"):
                cmd.extend(["--struct", str(options["struct"])])
            return cmd
        if op == "custom":
            custom_cmd = options.get("custom_cmd")
            if not custom_cmd:
                return None
            parts = str(custom_cmd).split()
            parts = [str(input_path) if p == "{input}" else str(output) if p == "{output}" else p for p in parts]
            return [*self.base_cmd, *parts]
        return None

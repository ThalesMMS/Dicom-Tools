import json
import sys
from pathlib import Path

from interface import contract_runner
from interface.adapters.runner import RunResult


def test_load_request_from_args_file(tmp_path):
    payload = {"backend": "python", "op": "info", "input": "file.dcm"}
    req_file = tmp_path / "req.json"
    req_file.write_text(json.dumps(payload))

    args = contract_runner.argparse.Namespace(
        request_file=str(req_file), backend=None, op=None, input=None, output=None, options=None
    )
    req = contract_runner.load_request_from_args(args)
    assert req == payload


def test_load_request_from_stdin(monkeypatch):
    data = json.dumps({"backend": "python", "op": "info", "input": "file.dcm"})
    monkeypatch.setattr(contract_runner.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(contract_runner.sys.stdin, "read", lambda: data)
    args = contract_runner.argparse.Namespace(request_file=None, backend=None, op=None, input=None, output=None, options=None)
    req = contract_runner.load_request_from_args(args)
    assert req["op"] == "info"


def test_main_success_with_stub(monkeypatch, tmp_path, capsys):
    sample = tmp_path / "sample.dcm"
    sample.write_text("dcm")

    class StubAdapter:
        def handle(self, request):
            return RunResult(ok=True, returncode=0, stdout="", stderr="", output_files=["out"], metadata={})

    monkeypatch.setattr(contract_runner, "get_adapter", lambda backend: StubAdapter())
    monkeypatch.setattr(contract_runner.sys.stdin, "isatty", lambda: True)

    # Bypass argparse parsing to keep test deterministic
    monkeypatch.setattr(
        contract_runner.argparse.ArgumentParser,
        "parse_args",
        lambda self: contract_runner.argparse.Namespace(
            request_file=None, backend="python", op="info", input=str(sample), output=None, options=None
        ),
    )

    rc = contract_runner.main()
    captured = capsys.readouterr()
    assert rc == 0, f"stderr={captured.err!r} stdout={captured.out!r}"
    data = json.loads(captured.out)
    assert data["ok"] is True

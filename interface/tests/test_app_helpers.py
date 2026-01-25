import json

import pytest

from interface import app


class DummyText:
    def __init__(self, initial: str = "") -> None:
        self.value = initial

    def get(self, *args, **kwargs):  # noqa: ANN001
        return self.value

    def delete(self, *_args, **_kwargs):
        self.value = ""

    def insert(self, _index, text):  # noqa: ANN001
        self.value = str(text)


class DummyVar:
    def __init__(self) -> None:
        self.value = ""

    def set(self, val):  # noqa: ANN001
        self.value = val


class DummyLabel:
    def __init__(self) -> None:
        self.kwargs = {}

    def configure(self, **kwargs):
        self.kwargs.update(kwargs)


class DummyEntry(DummyText):
    def set(self, val):  # noqa: ANN001
        self.value = val


def make_dummy_app(monkeypatch):
    # Build a TkApp without invoking Tk constructors
    inst = app.TkApp.__new__(app.TkApp)
    inst.backend = DummyEntry("python")
    inst.operation = DummyEntry("info")
    inst.library = DummyEntry("Todos")
    inst.input_entry = DummyEntry()
    inst.output_entry = DummyEntry()
    inst.options_text = DummyText("{}")
    inst.custom_cmd_entry = DummyEntry()
    inst.result_text = DummyText()
    inst.status_var = DummyVar()
    inst.preview_label = DummyLabel()
    inst.preview_img = None
    inst.run_button = type("Btn", (), {"state": lambda self, args=None: None})()
    monkeypatch.setattr(app, "messagebox", type("MB", (), {"showerror": lambda *a, **k: None, "showinfo": lambda *a, **k: None, "showwarning": lambda *a, **k: None})())
    monkeypatch.setattr(app, "tk", type("TK", (), {"PhotoImage": lambda *a, **k: object(), "END": "end"})())
    return inst


def test_normalize_output_infers_by_op(monkeypatch, tmp_path):
    inst = make_dummy_app(monkeypatch)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    assert inst._normalize_output("to_image", "input.dcm", str(out_dir)) == str(out_dir / "input.png")
    assert inst._normalize_output("anonymize", "input.dcm", str(out_dir)) == str(out_dir / "input_anon.dcm")
    assert inst._normalize_output("transcode", "input.dcm", str(out_dir)) == str(out_dir / "input_transcoded.dcm")
    assert inst._normalize_output("volume", "input.dcm", str(out_dir)) == str(out_dir / "input_volume.npy")
    assert inst._normalize_output("nifti", "input.dcm", str(out_dir)) == str(out_dir / "input_volume.nii.gz")


def test_parse_options_handles_invalid_json(monkeypatch):
    inst = make_dummy_app(monkeypatch)
    inst.options_text.value = "{bad json"
    assert inst._parse_options() == {}
    inst.options_text.value = json.dumps({"a": 1})
    assert inst._parse_options() == {"a": 1}


def test_render_result_sets_status(monkeypatch):
    inst = make_dummy_app(monkeypatch)

    class Result:
        def __init__(self, ok=True):
            self.ok = ok
            self.returncode = 0 if ok else 1
            self.output_files = []

        def as_dict(self):
            return {"ok": self.ok, "returncode": self.returncode, "output_files": []}

    inst._render_result(Result(ok=True))
    assert inst.status_var.value == "Success"
    inst._render_result(Result(ok=False))
    assert inst.status_var.value == "Failure"


def test_require_and_directory_detection(monkeypatch):
    inst = make_dummy_app(monkeypatch)
    assert inst._require_input("info") is True
    assert inst._require_input("echo") is False
    assert inst._require_input("histogram") is True
    assert inst._require_input("store_scu") is True
    assert inst._require_input("stow") is True
    assert inst._require_input("worklist") is False
    assert inst._require_input("qido") is False
    assert inst._require_input("wado") is False
    assert inst._require_input("sr_summary") is True
    assert inst._require_input("rt_check") is True
    assert inst._op_uses_directory_input("volume") is True
    assert inst._op_uses_directory_input("info") is False
    inst.backend.value = "cpp"
    assert inst._op_uses_directory_input("vtk_export") is True


def test_run_handles_missing_input(monkeypatch, tmp_path):
    inst = make_dummy_app(monkeypatch)
    inst.input_entry.value = ""
    inst.backend.value = "python"
    inst.operation.value = "info"
    called = {"adapter": False}
    monkeypatch.setattr(app, "get_adapter", lambda backend: called.__setitem__("adapter", True))
    inst._run()
    assert called["adapter"] is False


def test_run_success(monkeypatch, tmp_path):
    inst = make_dummy_app(monkeypatch)
    sample = tmp_path / "sample.dcm"
    sample.write_text("dcm")
    inst.input_entry.value = str(sample)
    inst.backend.value = "python"
    inst.operation.value = "info"
    inst.output_entry.value = ""
    result = type(
        "Res",
        (),
        {
            "ok": True,
            "returncode": 0,
            "output_files": [],
            "as_dict": lambda self=None: {"ok": True, "returncode": 0, "output_files": []},
        },
    )()
    monkeypatch.setattr(app, "get_adapter", lambda backend: type("Stub", (), {"handle": lambda self, req: result})())
    inst._run()
    assert inst.status_var.value == "Success"


def test_run_suite_with_stub(monkeypatch, tmp_path):
    inst = make_dummy_app(monkeypatch)
    sample = tmp_path / "sample.dcm"
    sample.write_text("dcm")
    inst.backend.value = "python"
    inst.operation.value = "info"

    monkeypatch.setattr(app, "DEFAULTS", {"python": {"info": {"input": sample, "output": None, "options": {}}}})
    monkeypatch.setattr(app, "SUITE_OPS", {"python": ["info"]})

    result = type(
        "Res",
        (),
        {
            "ok": True,
            "returncode": 0,
            "output_files": [],
            "as_dict": lambda self=None: {"ok": True, "returncode": 0, "output_files": []},
        },
    )()
    monkeypatch.setattr(app, "get_adapter", lambda backend: type("Stub", (), {"handle": lambda self, req: result})())
    inst._run_suite()
    assert "Suite completed" in inst.status_var.value

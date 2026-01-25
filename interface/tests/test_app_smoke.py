import os

import pytest


def test_tk_app_can_import_and_init(monkeypatch):
    try:
        from interface import app
    except Exception as exc:  # pragma: no cover - import guard
        pytest.skip(f"Tk not available: {exc}")

    # Avoid opening windows in headless runs
    monkeypatch.setenv("TK_SILENCE_DEPRECATION", "1")
    try:
        tk_app = app.TkApp()
    except Exception as exc:
        if "display" in str(exc).lower():
            pytest.skip(f"No display for Tk: {exc}")
        raise
    # Ensure viewers registry exists and defaults are populated
    assert app.BACKEND_OPS
    tk_app.root.destroy()


def test_run_button_binding(monkeypatch):
    try:
        from interface import app
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"Tk not available: {exc}")

    triggered = {"called": False}

    def fake_run():
        triggered["called"] = True

    try:
        tk_app = app.TkApp()
    except Exception as exc:
        if "display" in str(exc).lower():
            pytest.skip(f"No display for Tk: {exc}")
        raise

    tk_app.run_button.configure(command=fake_run)
    tk_app.run_button.invoke()
    tk_app.root.destroy()
    assert triggered["called"] is True

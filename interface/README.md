# Unified interface (Tkinter + CLI/JSON contract)

This directory contains the Tkinter UI and the adapters that call the C++/Python/Rust backends through subprocesses, exchanging requests/responses in the format described in `CONTRACT.md`.

## Requirements
- Python 3 installed.
- Compiled/installed backends:
  - Python: `pip install -e python` or use `python -m DICOM_reencoder.cli` directly (cwd `python/`).
  - Rust: `cargo build --release` in `rust/` (produces `rust/target/release/dicom-tools`).
  - C++: `cmake --build .` in `cpp/build` (produces `cpp/build/DicomTools`).

Optional env vars to point binaries:
- `PYTHON_DICOM_TOOLS_CMD` (default `python -m DICOM_reencoder.cli`, cwd `python/`)
- `RUST_DICOM_TOOLS_CMD` (overrides the Rust binary) or `RUST_DICOM_TOOLS_BIN` (default `rust/target/release/dicom-tools`; fallback `cargo run --release --`)
- `CPP_DICOM_TOOLS_BIN` (default `cpp/build/DicomTools`)
- `CS_DICOM_TOOLS_CMD` (default `cs/bin/Release/net8.0/DicomTools.Cli` or Debug fallback)
- `JAVA_DICOM_TOOLS_CMD` (default `java/dcm4che-tests/target/dcm4che-tests.jar` via `java -jar`)
- `JS_DICOM_TOOLS_CMD` (default `node js/contract-cli/index.js`)

## Using the Tkinter UI
```bash
python -m interface.app
```
Choose the backend, operation, input/output paths, and optionally a JSON options payload. The result appears as JSON in the lower panel.

## Using the headless runner (without UI)
```bash
# With flags
python -m interface.contract_runner --backend python --op info --input /path/to/file.dcm

# With a JSON file
python -m interface.contract_runner --request-file request.json

# Via pipe
echo '{"backend":"rust","op":"dump","input":"file.dcm"}' | python -m interface.contract_runner
```

## Contract
The request/response format and the minimum operation mapping live in `CONTRACT.md`. Runner responses always include `ok`, `returncode`, `stdout/stderr`, `artifacts` (aliases for `output_files`), `metadata`, plus `backend` and `operation` to make debugging easier.

## Reactive UI architecture
- Event bus + Command pattern (`interface/input/event_bus.py`) keep the UI and engine decoupled.
- `ToolManager` centralizes tools (scroll/zoom/pan/WL/ROI/overlay/MPR) and emits `frame_requested` to the render loop.
- `RenderLoop` (`interface/components/render_loop.py`) consumes requests and emits `frame_ready` as soon as the core finishes.
- Viewers (`TwoDViewer`, `MPRViewer`, `VolumeViewer`) only react to `frame_ready` and render overlays through `OverlayManager`.
- Target pipeline: `UI Input → Command → Core → Frame → Viewer → UI`.

The render loop has reentrancy protection: `frame_ready` events that trigger new `frame_requested` events are ignored while a frame is being generated, preventing infinite loops.

For headless / testable usage:
```python
from interface.runtime import InterfaceRuntime
from interface.state.frames import Frame

class DummyEngine:
    def render(self, request):
        return Frame(viewer=request.viewer, slice_index=request.slice_index, width=256, height=256)

runtime = InterfaceRuntime.create(DummyEngine())
runtime.inputs.scroll("2d", 1)
```

## Standardized events/inputs
All viewers share the same commands: `onScroll`, `onZoom`, `onPan`, `onWindowLevel`, `onChangeSeries`, `onToggleOverlay`, `onSelectROI`, `onDrag`, `onRebuildMPR`. The adapters in `interface/input/adapters.py` handle the mapping from mouse/keyboard/gestures to those commands.

## Overlays
`OverlayManager` (`interface/overlays/manager.py`) centralizes WL/WW, image index, location, thickness, timestamp, series name, active tool, and orientation markers. The UI only calls `overlay.render(context, state)`.

## Folder structure
- `components/`: reactive viewers + render loop.
- `input/`: event bus, unified controller, 2D/MPR/Volume adapters, `ToolManager`.
- `overlays/`: `OverlayManager` and default overlays.
- `state/`: `UIState`, `ViewerState`, `FrameRequest/Frame`.
- `utils/`: geometry helpers (pan/zoom/transform, ROI clipping, bounding boxes).

## Coordinate conventions
- Pan/zoom operate in canvas coordinates (origin at the top-left corner).
- `window_center/window_width` follow numeric frame values (without coupling to a graphics toolkit).
- 2D transforms keep a 3x3 (translate/scale) matrix in `ViewerState`.

## Tests
```bash
python3 -m pytest interface/tests
# or with coverage
python3 -m pytest interface/tests --cov=interface --cov-report=term-missing
```
Dev dependencies (pytest, pytest-cov, coverage) live in `interface/requirements-dev.txt`.
Coverage includes the contract runner and UI interactions (scroll, zoom, pan, WL, overlays, viewer switching, MPR rebuild).

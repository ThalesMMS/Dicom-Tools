# JS Layer (Cornerstone Gateway & Contract CLI)

This folder contains the project's JS artifacts. It includes the Cornerstone3D gateway used by the web viewer and a CLI shim for the shared contract.

## Structure
- `viewer-gateway/`: Vite app + Cornerstone3D gateway and Vitest tests.
- `contract-cli/`: Node shim that forwards contract calls to the Python backend.
- `new_features.md`: suggestions / status for automated tests.
- `INTEGRATION.md`, `TASKS.md`: quick integration notes and task lists.

## Prerequisites
- Node 18+.
- `sample_series/` at the repo root (used in tests and the demo).

## Viewer Gateway
```bash
cd js/viewer-gateway
npm install
npm run dev        # Vite demo; serve sample_series at http://localhost:8080/sample_series
npm run build      # production build
npm test           # Vitest (gateway + MPR/MIP/overlay via sample_series)
npm test -- --coverage   # V8 coverage (depends on @vitest/coverage-v8)
npm run test:coverage    # alias for coverage + tests (used in CI)
```

- New utilities:
  - `createVolumeViewport` initializes orthographic (MIP) or 3D viewports with axial/sagittal/coronal orientation, blend mode, and slab thickness.
  - `volumeUtils` includes spacing/origin/orientation, index↔world transforms (crosshair), ROI stats, and labelmap/segmentation helpers.
  - `dicomWeb.ts` builds `wadors:` imageIds through `dicomweb-client` (QIDO→WADO-RS), aligned with the servers used by dcm4che/fo-dicom/dicom-rs.
  - `src/main.ts` now demonstrates stack (WADO-URI), MIP/3D volume rendering, and a third DICOMweb panel: configure `VITE_DICOMWEB_BASE`, `VITE_DICOMWEB_STUDY`, `VITE_DICOMWEB_SERIES`, or `window.DICOMWEB_CONFIG` to exercise real WADO-RS flows.

## Contract CLI
```bash
node js/contract-cli/index.js --op info --input sample_series/IM-0001-0001.dcm --options "{}"
```
- Uses `BACKING_CMD` (env) to redirect to another backend, defaulting to `python -m DICOM_reencoder.cli`.

## Quick notes
- Tests use `sample_series` locally, so check the path when running in CI/containers.
- The gateway builds `wadouri:` imageIds for series served over HTTP, see `viewer-gateway/src/imageIds.ts`.

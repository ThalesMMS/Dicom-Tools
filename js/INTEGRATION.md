# JS / Cornerstone3D – Integration Notes

We no longer keep the cloned repository; we use the published packages in the `js/viewer-gateway` app.
- `cd js/viewer-gateway && npm install`
- `npm run dev` for the Vite demo (points to `/sample_series` over HTTP served by you)
- `npm test` (Vitest) to verify the gateway and `sample_series` integrity.

## Loading `sample_series` in Cornerstone3D (browser, HTTP)
Minimal example using the published packages (serve files over HTTP, not `file://`):

```ts
import {
  RenderingEngine,
  Enums,
  setUseCPURendering,
  cache,
} from '@cornerstonejs/core';
import * as cornerstoneTools from '@cornerstonejs/tools';
import dicomImageLoader from '@cornerstonejs/dicom-image-loader';

// Register the WADO-URI loader (files served through static HTTP)
dicomImageLoader.external.cornerstone = { // minimum required
  pageToDOM: () => undefined,
};
dicomImageLoader.configure({
  useWebWorkers: true,
});

// Build imageIds for the local series served at /sample_series
function buildImageIds(count: number) {
  return Array.from({ length: count }, (_, i) => {
    const num = String(i + 1).padStart(4, '0');
    return `wadouri:http://localhost:8080/sample_series/IM-0001-${num}.dcm`;
  });
}

async function renderStack(element: HTMLDivElement) {
  setUseCPURendering(false); // GPU when available
  const renderingEngine = new RenderingEngine('engine');
  const viewportId = 'stack';
  renderingEngine.enableElement({
    viewportId,
    element,
    type: Enums.ViewportType.STACK,
  });

  const imageIds = buildImageIds(174); // size of the provided series
  const viewport = renderingEngine.getViewport(viewportId);
  await viewport.setStack(imageIds);
  viewport.render();
}
```

Notes:
- Serve `sample_series` through local HTTP (for example, `npx serve .` at the `js/` root or `yarn serve` in a static server). The WADO-URI loader needs HTTP URLs.
- The loader already includes WASM codecs for typical transfer syntaxes; the official tests exercise several encodings.

## Suggested Wrapper/Gateway
Expected contract: backends provide a set of paths/URLs for DICOM instances in a series (or an object with metadata + frame list). The wrapper should:
1. Normalize paths into WADO-URI `imageIds` (`wadouri:http://.../file.dcm`) or data URIs.
2. Create/manage `RenderingEngine` + viewports (STACK or VOLUME).
3. Expose progress/loading and error callbacks.
4. Optionally map presets (VOI/LUT) and overlays from the contract.

Proposed high-level API (browser):
```ts
import { createViewer } from './viewerGateway';

const viewer = await createViewer({
  element: document.getElementById('viewport'),
  series: { imageUrls: urlsFromBackend },
  presets: { windowLevel: { center: 40, width: 400 } },
});

viewer.setSlice(42);
viewer.setVOI(400, 40);
viewer.destroy();
```

Implementation: use `@cornerstonejs/core` + `@cornerstonejs/tools` + `@cornerstonejs/dicom-image-loader`; hide wiring (loader registration, engine/viewport creation, setStack/setVolumes) and expose simple methods (`setSlice`, `setVOI`, `setToolMode`).

## Quick Notes
- Vitest tests live in `js/viewer-gateway/tests`: `viewerGateway*.test.ts` (gateway/API) and `sampleSeries.integration.test.ts` (series consistency through `dicom-parser`).
- Serve `sample_series` through local HTTP (for example, `npx serve .` at the repository root or `npx http-server . -p 8080`) for the Vite viewer.
- Ask for an additional React/Angular/Vue example if needed.

## DICOMweb Demo (WADO-RS)
- Configure a DICOMweb server (for example, the same one used by the dcm4che/fo-dicom tests) accessible over HTTP.
- Set the environment values (or `window.DICOMWEB_CONFIG` in the browser):
  - `VITE_DICOMWEB_BASE` — DICOMweb base URL (for example, `http://localhost:8042/dicom-web`)
  - `VITE_DICOMWEB_STUDY` — StudyInstanceUID
  - `VITE_DICOMWEB_SERIES` — SeriesInstanceUID
- Run `npm run dev` in `js/viewer-gateway` and open the Vite demo: it will show three viewports (Stack WADO-URI, local Volume MIP/3D, and DICOMweb WADO-RS using `fetchDicomWebImageIds` + `createVolumeViewport`).

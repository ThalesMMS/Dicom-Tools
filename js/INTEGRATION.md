# JS / Cornerstone3D – Notas de Integração

Não mantemos mais o repositório clonado; usamos os pacotes publicados no app `js/viewer-gateway`.
- `cd js/viewer-gateway && npm install`
- `npm run dev` para demo Vite (aponta para `/sample_series` via HTTP que você servir)
- `npm test` (Vitest) para verificar gateway + integridade da `sample_series`.

## Carregar a `sample_series` no Cornerstone3D (browser, HTTP)
Exemplo mínimo usando os pacotes publicados (sirva os arquivos via HTTP, não `file://`):

```ts
import {
  RenderingEngine,
  Enums,
  setUseCPURendering,
  cache,
} from '@cornerstonejs/core';
import * as cornerstoneTools from '@cornerstonejs/tools';
import dicomImageLoader from '@cornerstonejs/dicom-image-loader';

// Registra o loader WADO-URI (arquivos servidos por HTTP estático)
dicomImageLoader.external.cornerstone = { // mínimo requerido
  pageToDOM: () => undefined,
};
dicomImageLoader.configure({
  useWebWorkers: true,
});

// Constrói imageIds para a série local servida em /sample_series
function buildImageIds(count: number) {
  return Array.from({ length: count }, (_, i) => {
    const num = String(i + 1).padStart(4, '0');
    return `wadouri:http://localhost:8080/sample_series/IM-0001-${num}.dcm`;
  });
}

async function renderStack(element: HTMLDivElement) {
  setUseCPURendering(false); // GPU quando disponível
  const renderingEngine = new RenderingEngine('engine');
  const viewportId = 'stack';
  renderingEngine.enableElement({
    viewportId,
    element,
    type: Enums.ViewportType.STACK,
  });

  const imageIds = buildImageIds(174); // tamanho da série fornecida
  const viewport = renderingEngine.getViewport(viewportId);
  await viewport.setStack(imageIds);
  viewport.render();
}
```

Notas:
- Sirva `sample_series` via HTTP local (ex.: `npx serve .` na raiz `js/` ou `yarn serve` em um servidor estático). O loader WADO-URI precisa de URLs HTTP.
- O loader já inclui codecs WASM para transfer syntaxes típicas; os testes oficiais exercitam vários encodings.

## Wrapper/Gateway sugerido
Contrato esperado: backends entregam um conjunto de caminhos/URLs de instâncias DICOM de uma série (ou um objeto com metadados + lista de frames). O wrapper deve:
1. Normalizar paths para `imageIds` WADO-URI (`wadouri:http://.../file.dcm`) ou data URI.
2. Criar/gerenciar `RenderingEngine` + viewports (STACK ou VOLUME).
3. Expor callbacks de progresso/carregamento e erros.
4. Opcional: mapear presets (VOI/LUT) e overlays vindos do contrato.

API de alto nível proposta (browser):
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

Implementação: usar `@cornerstonejs/core` + `@cornerstonejs/tools` + `@cornerstonejs/dicom-image-loader`; esconder wiring (registro de loaders, criação de engine/viewport, setStack/setVolumes) e oferecer métodos simples (`setSlice`, `setVOI`, `setToolMode`).

## Observações rápidas
- Testes Vitest em `js/viewer-gateway/tests`: `viewerGateway*.test.ts` (gateway/API) e `sampleSeries.integration.test.ts` (consistência da série via `dicom-parser`).
- Sirva `sample_series` via HTTP local (ex.: `npx serve ..` na raiz do repo ou `npx http-server .. -p 8080`) para o viewer Vite.
- Se quiser um exemplo adicional (React/Angular/Vue), só pedir. 

## Demo DICOMweb (WADO-RS)
- Configure um servidor DICOMweb (ex.: o mesmo usado pelos testes dcm4che/fo-dicom) acessível em HTTP.
- Defina no ambiente (ou `window.DICOMWEB_CONFIG` no browser) os valores:
  - `VITE_DICOMWEB_BASE` — URL base DICOMweb (ex.: `http://localhost:8042/dicom-web`)
  - `VITE_DICOMWEB_STUDY` — StudyInstanceUID
  - `VITE_DICOMWEB_SERIES` — SeriesInstanceUID
- Rode `npm run dev` em `js/viewer-gateway` e abra a demo Vite: haverá três viewports (Stack WADO-URI, Volume MIP/3D local, DICOMweb WADO-RS usando `fetchDicomWebImageIds` + `createVolumeViewport`).

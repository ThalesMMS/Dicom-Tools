import './style.css';
import { buildImageIds, createStackViewer, createVolumeViewport } from './viewerGateway';
import { fetchDicomWebImageIds, DicomWebConfig } from './dicomWeb';

function createViewportSection(root: HTMLElement, title: string) {
  const section = document.createElement('section');
  const heading = document.createElement('h3');
  heading.textContent = title;

  const viewport = document.createElement('div');
  viewport.style.width = '512px';
  viewport.style.height = '512px';
  viewport.style.background = 'black';

  const info = document.createElement('p');

  section.appendChild(heading);
  section.appendChild(viewport);
  section.appendChild(info);
  root.appendChild(section);

  return { viewport, info };
}

function resolveDicomWebConfig(): DicomWebConfig | null {
  const metaEnv = (import.meta as any).env || {};
  const env = { ...process.env, ...metaEnv };
  const win = typeof window !== 'undefined' ? (window as any) : undefined;
  const globalCfg = win?.DICOMWEB_CONFIG || win?.__DICOMWEB_CONFIG__;

  if (globalCfg?.baseUrl && globalCfg?.studyInstanceUID && globalCfg?.seriesInstanceUID) {
    return globalCfg as DicomWebConfig;
  }

  if (env.VITE_DICOMWEB_BASE && env.VITE_DICOMWEB_STUDY && env.VITE_DICOMWEB_SERIES) {
    return {
      baseUrl: env.VITE_DICOMWEB_BASE,
      studyInstanceUID: env.VITE_DICOMWEB_STUDY,
      seriesInstanceUID: env.VITE_DICOMWEB_SERIES,
    };
  }

  return null;
}

const root = document.getElementById('app') as HTMLDivElement;

// Adjust base URL to wherever you serve sample_series over HTTP
const baseUrl = 'http://localhost:8080/sample_series';
const imageIds = buildImageIds(baseUrl, 174);

const stack = createViewportSection(root, 'Stack (WADO-URI)');
stack.info.textContent = 'Loading sample_series via wadouri...';

createStackViewer({
  element: stack.viewport,
  imageIds,
})
  .then(() => {
    stack.info.textContent = `Loaded ${imageIds.length} slices from ${baseUrl}`;
  })
  .catch((err) => {
    console.error(err);
    stack.info.textContent = `Failed to load series: ${String(err)}`;
  });

const volume = createViewportSection(root, 'Volume (MIP/3D)');
volume.info.textContent = 'Loading volume MIP...';

createVolumeViewport({
  element: volume.viewport,
  imageIds,
  mode: 'mip',
  orientation: 'axial',
  slabThickness: 25,
})
  .then(() => {
    volume.info.textContent = `Volume MIP ready from ${imageIds.length} slices`;
  })
  .catch((err) => {
    console.error(err);
    volume.info.textContent = `Failed to init volume: ${String(err)}`;
  });

const dicomweb = createViewportSection(root, 'DICOMweb (WADO-RS)');
const dicomwebConfig = resolveDicomWebConfig();

if (!dicomwebConfig) {
  dicomweb.info.textContent = 'Skip DICOMweb demo (configure VITE_DICOMWEB_* or window.DICOMWEB_CONFIG).';
} else {
  dicomweb.info.textContent = 'Loading via dicomweb-client (QIDO/WADO-RS)...';
  fetchDicomWebImageIds(dicomwebConfig)
    .then(({ imageIds: wadorsIds }) =>
      createVolumeViewport({
        element: dicomweb.viewport,
        imageIds: wadorsIds,
        mode: 'volume',
        orientation: 'axial',
      }),
    )
    .then((viewer) => {
      dicomweb.info.textContent = 'Loaded from DICOMweb (volume render)';
      return viewer;
    })
    .catch((err) => {
      console.error(err);
      dicomweb.info.textContent = `Failed DICOMweb load: ${String(err)}`;
    });
}

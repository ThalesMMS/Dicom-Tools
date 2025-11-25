import './style.css';
import { buildImageIds, createStackViewer, createVolumeViewport } from './viewerGateway';
import { fetchDicomWebImageIds, DicomWebConfig } from './dicomWeb';
import { loadDemoConfig } from './config';
import { applyVoiPreset, VOI_PRESETS } from './presets';
import { reportStatus } from './logging';

type StackHandle = Awaited<ReturnType<typeof createStackViewer>>;
type VolumeHandle = Awaited<ReturnType<typeof createVolumeViewport>>;

const config = loadDemoConfig();

function createViewportSection(root: HTMLElement, title: string) {
  const section = document.createElement('section');
  section.className = 'viewport-section';
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

function createControls(root: HTMLElement) {
  const section = document.createElement('section');
  section.className = 'controls';
  const heading = document.createElement('h3');
  heading.textContent = 'Controls';
  section.appendChild(heading);

  const orientationSelect = document.createElement('select');
  ['axial', 'sagittal', 'coronal'].forEach((o) => {
    const opt = document.createElement('option');
    opt.value = o;
    opt.textContent = o;
    orientationSelect.appendChild(opt);
  });

  const modeSelect = document.createElement('select');
  [
    { value: 'mip', label: 'MIP' },
    { value: 'volume', label: 'Volume render' },
  ].forEach((m) => {
    const opt = document.createElement('option');
    opt.value = m.value;
    opt.textContent = m.label;
    modeSelect.appendChild(opt);
  });

  const slabInput = document.createElement('input');
  slabInput.type = 'number';
  slabInput.min = '1';
  slabInput.value = '25';

  const voiCenter = document.createElement('input');
  voiCenter.type = 'number';
  voiCenter.value = '40';

  const voiWidth = document.createElement('input');
  voiWidth.type = 'number';
  voiWidth.value = '400';

  const applyBtn = document.createElement('button');
  applyBtn.textContent = 'Apply orientation/mode/slab';

  const voiBtn = document.createElement('button');
  voiBtn.textContent = 'Apply VOI';

  const presetButtons = (['soft', 'bone', 'lung'] as const).map((key) => {
    const btn = document.createElement('button');
    btn.textContent = `Preset ${key}`;
    btn.dataset.preset = key;
    return btn;
  });

  const dicomwebForm = document.createElement('div');
  const dicomBase = document.createElement('input');
  dicomBase.placeholder = 'DICOMweb Base URL';
  const dicomStudy = document.createElement('input');
  dicomStudy.placeholder = 'StudyInstanceUID';
  const dicomSeries = document.createElement('input');
  dicomSeries.placeholder = 'SeriesInstanceUID';
  const dicomBtn = document.createElement('button');
  dicomBtn.textContent = 'Load DICOMweb';

  [dicomBase, dicomStudy, dicomSeries].forEach((el) => (el.size = 40));

  dicomwebForm.append('DICOMweb: ', dicomBase, dicomStudy, dicomSeries, dicomBtn);

  const voiRow = document.createElement('div');
  voiRow.append('VOI center/width: ', voiCenter, voiWidth, voiBtn, ...presetButtons);

  const volumeRow = document.createElement('div');
  volumeRow.append('Orientation: ', orientationSelect, ' Mode: ', modeSelect, ' Slab: ', slabInput, applyBtn);

  section.append(volumeRow, voiRow, dicomwebForm);
  root.appendChild(section);

  return {
    orientationSelect,
    modeSelect,
    slabInput,
    voiCenter,
    voiWidth,
    applyBtn,
    voiBtn,
    presetButtons,
    dicomBase,
    dicomStudy,
    dicomSeries,
    dicomBtn,
  };
}

async function bootstrap() {
  const root = document.getElementById('app') as HTMLDivElement;
  const controls = createControls(root);

  const stackSection = createViewportSection(root, 'Stack (WADO-URI)');
  const volumeSection = createViewportSection(root, 'Volume (MIP/3D)');
  const dicomwebSection = createViewportSection(root, 'DICOMweb (WADO-RS)');

  let stackHandle: StackHandle | null = null;
  let volumeHandle: VolumeHandle | null = null;
  let dicomwebHandle: VolumeHandle | null = null;

  const imageIds = buildImageIds(config.sampleBaseUrl, config.sampleCount);
  reportStatus(stackSection.info, 'info', 'Loading sample_series via WADO-URI...');

  createStackViewer({ element: stackSection.viewport, imageIds, useCPU: config.useCPU })
    .then((viewer) => {
      stackHandle = viewer;
      reportStatus(stackSection.info, 'info', `Loaded ${imageIds.length} slices from ${config.sampleBaseUrl}`);
    })
    .catch((err) => {
      reportStatus(stackSection.info, 'error', `Failed to load series: ${String(err)}`, err);
    });

  reportStatus(volumeSection.info, 'info', 'Loading volume MIP...');
  createVolumeViewport({
    element: volumeSection.viewport,
    imageIds,
    mode: 'mip',
    orientation: 'axial',
    slabThickness: Number(controls.slabInput.value) || 25,
    useCPU: config.useCPU,
  })
    .then((viewer) => {
      volumeHandle = viewer;
      reportStatus(volumeSection.info, 'info', `Volume MIP ready from ${imageIds.length} slices`);
    })
    .catch((err) => {
      reportStatus(volumeSection.info, 'error', `Failed to init volume: ${String(err)}`, err);
    });

  async function loadDicomweb(dConfig: DicomWebConfig) {
    if (dicomwebHandle && typeof dicomwebHandle.destroy === 'function') {
      dicomwebHandle.destroy();
    }
    reportStatus(dicomwebSection.info, 'info', 'Loading via dicomweb-client (QIDO/WADO-RS)...');
    try {
      const { imageIds: wadorsIds } = await fetchDicomWebImageIds(dConfig);
      const viewer = await createVolumeViewport({
        element: dicomwebSection.viewport,
        imageIds: wadorsIds,
        mode: 'volume',
        orientation: 'axial',
        useCPU: config.useCPU,
      });
      dicomwebHandle = viewer;
      reportStatus(dicomwebSection.info, 'info', 'Loaded from DICOMweb (volume render)');
    } catch (err) {
      reportStatus(dicomwebSection.info, 'error', `Failed DICOMweb load: ${String(err)}`, err);
    }
  }

  if (config.dicomweb) {
    controls.dicomBase.value = config.dicomweb.baseUrl;
    controls.dicomStudy.value = config.dicomweb.studyInstanceUID;
    controls.dicomSeries.value = config.dicomweb.seriesInstanceUID;
    loadDicomweb(config.dicomweb);
  } else {
    reportStatus(dicomwebSection.info, 'info', 'Skip DICOMweb demo (configure VITE_DICOMWEB_* or window.DICOMWEB_CONFIG).');
  }

  controls.applyBtn.addEventListener('click', () => {
    if (!volumeHandle || typeof volumeHandle.setOrientation !== 'function' || typeof volumeHandle.setBlendMode !== 'function') return;
    volumeHandle.setOrientation(controls.orientationSelect.value as any);
    volumeHandle.setBlendMode(controls.modeSelect.value as any);
    const slab = Number(controls.slabInput.value);
    if (slab > 0 && volumeHandle.setSlabThickness) {
      volumeHandle.setSlabThickness(slab);
    }
  });

  controls.voiBtn.addEventListener('click', () => {
    if (!stackHandle || typeof stackHandle.setVOI !== 'function') return;
    const center = Number(controls.voiCenter.value);
    const width = Number(controls.voiWidth.value);
    stackHandle.setVOI(center, width);
  });

  controls.presetButtons.forEach((btn) =>
    btn.addEventListener('click', () => {
      if (!stackHandle || typeof stackHandle.setVOI !== 'function') return;
      const key = btn.dataset.preset as keyof typeof VOI_PRESETS;
      const preset = VOI_PRESETS[key];
      applyVoiPreset(stackHandle, preset);
      controls.voiCenter.value = String(preset.center);
      controls.voiWidth.value = String(preset.width);
    }),
  );

  controls.dicomBtn.addEventListener('click', () => {
    const baseUrl = controls.dicomBase.value.trim();
    const studyInstanceUID = controls.dicomStudy.value.trim();
    const seriesInstanceUID = controls.dicomSeries.value.trim();
    if (baseUrl && studyInstanceUID && seriesInstanceUID) {
      loadDicomweb({ baseUrl, studyInstanceUID, seriesInstanceUID });
    }
  });
}

bootstrap();

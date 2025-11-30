import './style.css';
import { buildImageIds, createStackViewer, createVolumeViewport } from './viewerGateway';
import { fetchDicomWebImageIds, DicomWebConfig } from './dicomWeb';
import { loadDemoConfig } from './config';
import { applyVoiPreset, VOI_PRESETS } from './presets';
import { reportStatus } from './logging';
import {
  computeAIP,
  computeHistogram,
  computeMIP,
  computeMinIP,
  extractAxialSlice,
  resampleSlice,
  Slice2D,
  VolumeData,
  windowLevelSlice,
} from './volumeUtils';

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

function createAnalysisSection(root: HTMLElement) {
  const section = document.createElement('section');
  section.className = 'analysis';
  const heading = document.createElement('h3');
  heading.textContent = 'TS Volume Utils (MIP/MinIP/AIP, Histogram, VOI)';
  const info = document.createElement('div');

  const projectionRow = document.createElement('div');
  const mipBtn = document.createElement('button');
  mipBtn.textContent = 'CPU MIP';
  const minipBtn = document.createElement('button');
  minipBtn.textContent = 'CPU MinIP';
  const aipBtn = document.createElement('button');
  aipBtn.textContent = 'CPU AIP';
  projectionRow.append('Projeções: ', mipBtn, minipBtn, aipBtn);

  const voiSliceBtn = document.createElement('button');
  voiSliceBtn.textContent = 'Window/Level axial';

  const resampleRow = document.createElement('div');
  const resampleW = document.createElement('input');
  resampleW.type = 'number';
  resampleW.value = '256';
  resampleW.min = '1';
  resampleW.size = 4;
  const resampleH = document.createElement('input');
  resampleH.type = 'number';
  resampleH.value = '256';
  resampleH.min = '1';
  resampleH.size = 4;
  const resampleBtn = document.createElement('button');
  resampleBtn.textContent = 'Resample axial slice';
  resampleRow.append('Resample alvo: ', resampleW, ' x ', resampleH, resampleBtn, ' ', voiSliceBtn);

  const histogramRow = document.createElement('div');
  const binsInput = document.createElement('input');
  binsInput.type = 'number';
  binsInput.min = '16';
  binsInput.step = '16';
  binsInput.value = '256';
  binsInput.size = 5;
  const histogramBtn = document.createElement('button');
  histogramBtn.textContent = 'Calcular histograma';
  histogramRow.append('Bins: ', binsInput, histogramBtn);

  const previewCanvas = document.createElement('canvas');
  previewCanvas.width = 512;
  previewCanvas.height = 512;
  previewCanvas.className = 'preview-canvas';

  const histogramCanvas = document.createElement('canvas');
  histogramCanvas.width = 480;
  histogramCanvas.height = 160;
  histogramCanvas.className = 'histogram-canvas';
  const histogramInfo = document.createElement('div');

  section.append(heading, info, projectionRow, resampleRow, previewCanvas, histogramRow, histogramCanvas, histogramInfo);
  root.appendChild(section);

  return {
    section,
    info,
    mipBtn,
    minipBtn,
    aipBtn,
    voiSliceBtn,
    resampleBtn,
    resampleW,
    resampleH,
    histogramBtn,
    binsInput,
    previewCanvas,
    histogramCanvas,
    histogramInfo,
  };
}

type NumericSlice = Slice2D<Float32Array | Uint8Array>;

function renderSliceToCanvas(slice: NumericSlice, canvas: HTMLCanvasElement, opts?: { window?: { center: number; width: number } }) {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  canvas.width = slice.width;
  canvas.height = slice.height;

  let data: Uint8Array;
  if (opts?.window && slice.data instanceof Float32Array) {
    const windowed = windowLevelSlice(slice, opts.window.center, opts.window.width);
    data = windowed.data;
  } else if (slice.data instanceof Uint8Array) {
    data = slice.data;
  } else {
    let min = Infinity;
    let max = -Infinity;
    for (let i = 0; i < slice.data.length; i++) {
      const v = slice.data[i];
      if (v < min) min = v;
      if (v > max) max = v;
    }
    const range = max - min || 1;
    data = new Uint8Array(slice.data.length);
    for (let i = 0; i < slice.data.length; i++) {
      data[i] = Math.min(255, Math.max(0, Math.round(((slice.data[i] - min) / range) * 255)));
    }
  }

  const image = ctx.createImageData(slice.width, slice.height);
  for (let i = 0; i < data.length; i++) {
    const v = data[i];
    const idx = i * 4;
    image.data[idx] = v;
    image.data[idx + 1] = v;
    image.data[idx + 2] = v;
    image.data[idx + 3] = 255;
  }

  ctx.putImageData(image, 0, 0);
}

function drawHistogram(hist: ReturnType<typeof computeHistogram>, canvas: HTMLCanvasElement) {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  const { bins } = hist;

  const width = Math.max(320, bins.length * 2);
  const height = canvas.height;
  canvas.width = width;

  const maxCount = bins.reduce((m, v) => (v > m ? v : m), 0) || 1;

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = '#f4f6fa';
  ctx.fillRect(0, 0, width, height);

  ctx.fillStyle = '#2c6cff';
  const barWidth = width / bins.length;
  bins.forEach((v, i) => {
    const barHeight = (v / maxCount) * (height - 12);
    const x = i * barWidth;
    const y = height - barHeight;
    ctx.fillRect(x, y, Math.max(1, barWidth - 1), barHeight);
  });
}

function extractVolumeDataFromCornerstone(volumeHandle: VolumeHandle | null): VolumeData | null {
  if (!volumeHandle?.volume) return null;
  const volumeAny: any = volumeHandle.volume as any;
  const imageData = volumeAny.imageData || volumeAny.getImageData?.();
  const dims: number[] | undefined = imageData?.getDimensions?.();
  const spacing: number[] | undefined = imageData?.getSpacing?.();
  const origin: number[] | undefined = imageData?.getOrigin?.();
  const direction: number[] | undefined = imageData?.getDirection?.();
  const pointData = imageData?.getPointData?.();
  const scalars = pointData?.getScalars?.();
  const rawData: ArrayBufferView | undefined = scalars?.getData?.() ?? scalars?.getArray?.();

  if (!dims || dims.length < 3 || !rawData) return null;

  const voxelData = rawData instanceof Float32Array ? rawData : new Float32Array(rawData as any);

  const orientation = direction && direction.length >= 6 ? { row: [direction[0], direction[1], direction[2]] as [number, number, number], col: [direction[3], direction[4], direction[5]] as [number, number, number] } : undefined;

  return {
    cols: dims[0],
    rows: dims[1],
    slices: dims[2],
    voxelData,
    spacing: spacing ? { col: spacing[0], row: spacing[1], slice: spacing[2] } : undefined,
    origin: origin && origin.length >= 3 ? [origin[0], origin[1], origin[2]] : undefined,
    orientation,
  };
}

async function bootstrap() {
  const root = document.getElementById('app') as HTMLDivElement;
  const controls = createControls(root);
  const analysis = createAnalysisSection(root);

  const stackSection = createViewportSection(root, 'Stack (WADO-URI)');
  const volumeSection = createViewportSection(root, 'Volume (MIP/3D)');
  const dicomwebSection = createViewportSection(root, 'DICOMweb (WADO-RS)');

  let stackHandle: StackHandle | null = null;
  let volumeHandle: VolumeHandle | null = null;
  let dicomwebHandle: VolumeHandle | null = null;
  let cachedVolumeData: VolumeData | null = null;

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
      cachedVolumeData = null;
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
      cachedVolumeData = null;
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

  async function ensureVolumeData() {
    if (cachedVolumeData) return cachedVolumeData;
    const sourceHandle = volumeHandle ?? dicomwebHandle;
    const extracted = extractVolumeDataFromCornerstone(sourceHandle);
    if (!extracted) {
      reportStatus(analysis.info, 'error', 'Volume ainda não carregado ou sem dados escalar.');
      return null;
    }
    cachedVolumeData = extracted;
    return extracted;
  }

  async function renderProjection(kind: 'mip' | 'minip' | 'aip') {
    const volumeData = await ensureVolumeData();
    if (!volumeData) return;

    let slice: NumericSlice;
    if (kind === 'mip') slice = computeMIP(volumeData);
    else if (kind === 'minip') slice = computeMinIP(volumeData);
    else slice = computeAIP(volumeData);

    renderSliceToCanvas(slice, analysis.previewCanvas, {
      window: { center: Number(controls.voiCenter.value), width: Number(controls.voiWidth.value) },
    });
    reportStatus(analysis.info, 'info', `Renderizou ${kind.toUpperCase()} em ${slice.width}x${slice.height}`);
  }

  analysis.mipBtn.addEventListener('click', () => renderProjection('mip'));
  analysis.minipBtn.addEventListener('click', () => renderProjection('minip'));
  analysis.aipBtn.addEventListener('click', () => renderProjection('aip'));

  analysis.voiSliceBtn.addEventListener('click', async () => {
    const volumeData = await ensureVolumeData();
    if (!volumeData) return;
    const sliceIndex = Math.floor(volumeData.slices / 2);
    const center = Number(controls.voiCenter.value);
    const width = Number(controls.voiWidth.value);
    const slice = extractAxialSlice(volumeData, sliceIndex);
    const windowed = windowLevelSlice(slice, center, width);
    renderSliceToCanvas(windowed, analysis.previewCanvas);
    reportStatus(analysis.info, 'info', `Window/Level no corte axial ${sliceIndex} (C=${center}, W=${width})`);
  });

  analysis.resampleBtn.addEventListener('click', async () => {
    const volumeData = await ensureVolumeData();
    if (!volumeData) return;
    const sliceIndex = Math.floor(volumeData.slices / 2);
    const slice = extractAxialSlice(volumeData, sliceIndex);
    const targetW = Math.max(1, Number(analysis.resampleW.value) || 256);
    const targetH = Math.max(1, Number(analysis.resampleH.value) || 256);
    const resampled = resampleSlice(slice, targetW, targetH, 'bilinear');
    renderSliceToCanvas(resampled, analysis.previewCanvas, {
      window: { center: Number(controls.voiCenter.value), width: Number(controls.voiWidth.value) },
    });
    reportStatus(analysis.info, 'info', `Resample axial ${sliceIndex} para ${targetW}x${targetH}`);
  });

  analysis.histogramBtn.addEventListener('click', async () => {
    const volumeData = await ensureVolumeData();
    if (!volumeData) return;
    const bins = Math.max(16, Number(analysis.binsInput.value) || 256);
    const hist = computeHistogram(volumeData, bins);
    drawHistogram(hist, analysis.histogramCanvas);
    analysis.histogramInfo.textContent = `Range: [${hist.min.toFixed(1)}, ${hist.max.toFixed(1)}], binWidth=${hist.binWidth.toFixed(2)} (bins=${bins})`;
    reportStatus(analysis.info, 'info', `Histograma gerado com ${bins} bins`);
  });
}

bootstrap();

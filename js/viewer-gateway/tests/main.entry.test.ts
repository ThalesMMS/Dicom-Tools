import { describe, it, expect, vi, beforeEach } from 'vitest';

const viewerMocks = vi.hoisted(() => {
  const buildImageIds = vi.fn((base: string, count: number) => Array.from({ length: count }, (_, i) => `wadouri:${base}/IM-${i + 1}`));
  const createStackViewer = vi.fn(() => Promise.resolve({ setSlice: vi.fn(), setVOI: vi.fn(), destroy: vi.fn() }));
  const createVolumeViewport = vi.fn(() =>
    Promise.resolve({
      setBlendMode: vi.fn(),
      setOrientation: vi.fn(),
      setSlabThickness: vi.fn(),
      destroy: vi.fn(),
    }),
  );
  return { buildImageIds, createStackViewer, createVolumeViewport };
});

vi.mock('../src/viewerGateway', () => viewerMocks);
vi.mock('../src/dicomWeb', () => ({
  fetchDicomWebImageIds: vi.fn(),
}));

type HarnessOptions = {
  dicomwebConfig?: { baseUrl: string; studyInstanceUID: string; seriesInstanceUID: string };
  dicomwebResult?: { imageIds: string[]; instances: any[] };
  dicomwebError?: Error;
};

async function runMain(opts: HarnessOptions = {}) {
  const rootAppend = vi.fn();
  const created: any[] = [];
  const root = { appendChild: rootAppend };

  const docStub = {
    getElementById: vi.fn(() => root),
    createElement: vi.fn((tag: string) => {
      const el: any = { tagName: tag, style: {}, dataset: {}, textContent: '', children: [] as any[], value: '' };
      el.appendChild = vi.fn((child) => el.children.push(child));
      el.append = vi.fn((...nodes: any[]) => el.children.push(...nodes));
      el._handlers = {};
      el.addEventListener = vi.fn((event: string, cb: any) => {
        el._handlers[event] = cb;
      });
      created.push(el);
      return el;
    }),
  };

  vi.stubGlobal('document', docStub as any);
  if (opts.dicomwebConfig) {
    vi.stubGlobal('window', { DICOMWEB_CONFIG: opts.dicomwebConfig } as any);
  }

  const dicomWebModule = await import('../src/dicomWeb');
  if (opts.dicomwebResult) {
    (dicomWebModule.fetchDicomWebImageIds as any).mockResolvedValue(opts.dicomwebResult);
  } else if (opts.dicomwebError) {
    (dicomWebModule.fetchDicomWebImageIds as any).mockRejectedValue(opts.dicomwebError);
  } else {
    (dicomWebModule.fetchDicomWebImageIds as any).mockResolvedValue({ imageIds: [], instances: [] });
  }

  await import('../src/main');
  await Promise.resolve();
  await Promise.resolve(); // settle chained thens

  const viewerGateway = await import('../src/viewerGateway');
  return { created, docStub, viewerGateway };
}

describe('main entrypoint wiring', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
    vi.unstubAllGlobals();
    viewerMocks.createStackViewer.mockResolvedValue({});
    viewerMocks.createVolumeViewport.mockResolvedValue({});
  });

  it('mounts stack/volume viewports and skips dicomweb when not configured', async () => {
    const { created, docStub } = await runMain();

    expect(docStub.getElementById).toHaveBeenCalledWith('app');
    expect(viewerMocks.buildImageIds).toHaveBeenCalledWith('http://localhost:8080/sample_series', 174);
    expect(viewerMocks.createStackViewer).toHaveBeenCalledTimes(1);
    expect(viewerMocks.createVolumeViewport).toHaveBeenCalledTimes(1);

    const infoParagraphs = created.filter((el) => el.tagName === 'p');
    expect(infoParagraphs[0].textContent).toContain('Loaded 174 slices from http://localhost:8080/sample_series');
    expect(infoParagraphs[1].textContent).toContain('Volume MIP ready');
    expect(infoParagraphs[2].textContent).toContain('Skip DICOMweb demo');

    const applyBtn = created.find((el) => el.tagName === 'button' && el.textContent?.includes('Apply orientation'));
    applyBtn?._handlers.click?.({});
    const voiBtn = created.find((el) => el.tagName === 'button' && el.textContent?.includes('Apply VOI'));
    voiBtn?._handlers.click?.({});
    const presetSoft = created.find((el) => el.tagName === 'button' && el.textContent?.includes('Preset soft'));
    presetSoft?._handlers.click?.({});
  });

  it('runs dicomweb flow when config is provided', async () => {
    const dicomwebResult = { imageIds: ['wadors:a', 'wadors:b'], instances: [] };
    const { created } = await runMain({
      dicomwebConfig: { baseUrl: 'http://dw', studyInstanceUID: 's', seriesInstanceUID: 'se' },
      dicomwebResult,
    });

    const dicomwebArgs = (viewerMocks.createVolumeViewport as any).mock.calls.at(-1)[0];
    expect(viewerMocks.createVolumeViewport.mock.calls.length).toBeGreaterThanOrEqual(2);
    expect(dicomwebArgs.mode).toBe('volume');
    expect(dicomwebArgs.imageIds).toEqual(dicomwebResult.imageIds);

    const infoParagraphs = created.filter((el) => el.tagName === 'p');
    expect(infoParagraphs[2].textContent).toContain('Loaded from DICOMweb');

    // simulate manual DICOMweb reload
    const dicomBtn = created.find((el) => el.tagName === 'button' && el.textContent?.includes('Load'));
    const baseInput = created.find((el) => el.tagName === 'input' && el.placeholder?.includes('DICOMweb Base URL'));
    const studyInput = created.find((el) => el.tagName === 'input' && el.placeholder?.includes('StudyInstanceUID'));
    const seriesInput = created.find((el) => el.tagName === 'input' && el.placeholder?.includes('SeriesInstanceUID'));
    if (baseInput && studyInput && seriesInput && dicomBtn) {
      baseInput.value = 'http://dw';
      studyInput.value = 's';
      seriesInput.value = 'se';
      dicomBtn._handlers.click?.({});
    }
  });

  it('reads dicomweb config from env variables', async () => {
    const prev = {
      base: process.env.VITE_DICOMWEB_BASE,
      study: process.env.VITE_DICOMWEB_STUDY,
      series: process.env.VITE_DICOMWEB_SERIES,
    };
    process.env.VITE_DICOMWEB_BASE = 'http://env-base';
    process.env.VITE_DICOMWEB_STUDY = 'env-study';
    process.env.VITE_DICOMWEB_SERIES = 'env-series';

    try {
      const dicomwebResult = { imageIds: ['wadors:env'], instances: [] };
      const { created } = await runMain({ dicomwebResult });

      expect(viewerMocks.createVolumeViewport.mock.calls.length).toBeGreaterThanOrEqual(2);
      const infoParagraphs = created.filter((el) => el.tagName === 'p');
      expect(infoParagraphs[2].textContent).toContain('Loaded from DICOMweb');
    } finally {
      process.env.VITE_DICOMWEB_BASE = prev.base;
      process.env.VITE_DICOMWEB_STUDY = prev.study;
      process.env.VITE_DICOMWEB_SERIES = prev.series;
    }
  });

  it('shows dicomweb failure message when fetch fails', async () => {
    const { created } = await runMain({
      dicomwebConfig: { baseUrl: 'http://dw', studyInstanceUID: 's', seriesInstanceUID: 'se' },
      dicomwebError: new Error('boom'),
    });

    expect(viewerMocks.createVolumeViewport).toHaveBeenCalledTimes(1); // only stack+volume
    const infoParagraphs = created.filter((el) => el.tagName === 'p');
    expect(infoParagraphs[2].textContent).toContain('Failed DICOMweb load');
  });

  it('surfaces stack/volume failures via status text', async () => {
    viewerMocks.createStackViewer.mockRejectedValueOnce(new Error('stackfail'));
    viewerMocks.createVolumeViewport.mockRejectedValueOnce(new Error('volfail'));

    const { created } = await runMain();
    const infoParagraphs = created.filter((el) => el.tagName === 'p');
    expect(infoParagraphs[0].textContent).toContain('Failed to load series');
    expect(infoParagraphs[1].textContent).toContain('Failed to init volume');
  });
});

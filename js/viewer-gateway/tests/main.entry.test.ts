import { describe, it, expect, vi, beforeEach } from 'vitest';

const viewerMocks = vi.hoisted(() => {
  const buildImageIds = vi.fn((base: string, count: number) => Array.from({ length: count }, (_, i) => `wadouri:${base}/IM-${i + 1}`));
  const createStackViewer = vi.fn(() => Promise.resolve({}));
  const createVolumeViewport = vi.fn(() => Promise.resolve({}));
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
      const el: any = { tagName: tag, style: {}, appendChild: vi.fn(), textContent: '' };
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
    const { created, docStub, viewerGateway } = await runMain();

    expect(docStub.getElementById).toHaveBeenCalledWith('app');
    expect(docStub.createElement).toHaveBeenCalledWith('div');
    expect(docStub.createElement).toHaveBeenCalledWith('p');

    expect(viewerGateway.buildImageIds).toHaveBeenCalledWith('http://localhost:8080/sample_series', 174);
    expect(viewerGateway.createStackViewer).toHaveBeenCalledTimes(1);
    expect(viewerGateway.createVolumeViewport).toHaveBeenCalledTimes(1);

    const infoParagraphs = created.filter((el) => el.tagName === 'p');
    expect(infoParagraphs[0].textContent).toContain('Loaded 174 slices from http://localhost:8080/sample_series');
    expect(infoParagraphs[1].textContent).toContain('Volume MIP ready');
    expect(infoParagraphs[2].textContent).toContain('Skip DICOMweb demo');
  });

  it('runs dicomweb flow when config is provided', async () => {
    const dicomwebResult = { imageIds: ['wadors:a', 'wadors:b'], instances: [] };
    const { created, viewerGateway } = await runMain({
      dicomwebConfig: { baseUrl: 'http://dw', studyInstanceUID: 's', seriesInstanceUID: 'se' },
      dicomwebResult,
    });

    expect(viewerGateway.createVolumeViewport).toHaveBeenCalledTimes(2);
    const dicomwebArgs = (viewerGateway.createVolumeViewport as any).mock.calls[1][0];
    expect(dicomwebArgs.mode).toBe('volume');
    expect(dicomwebArgs.imageIds).toEqual(dicomwebResult.imageIds);

    const infoParagraphs = created.filter((el) => el.tagName === 'p');
    expect(infoParagraphs[2].textContent).toContain('Loaded from DICOMweb');
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
      const { created, viewerGateway } = await runMain({ dicomwebResult });

      expect(viewerGateway.createVolumeViewport).toHaveBeenCalledTimes(2);
      const infoParagraphs = created.filter((el) => el.tagName === 'p');
      expect(infoParagraphs[2].textContent).toContain('Loaded from DICOMweb');
    } finally {
      process.env.VITE_DICOMWEB_BASE = prev.base;
      process.env.VITE_DICOMWEB_STUDY = prev.study;
      process.env.VITE_DICOMWEB_SERIES = prev.series;
    }
  });

  it('shows dicomweb failure message when fetch fails', async () => {
    const { created, viewerGateway } = await runMain({
      dicomwebConfig: { baseUrl: 'http://dw', studyInstanceUID: 's', seriesInstanceUID: 'se' },
      dicomwebError: new Error('boom'),
    });

    expect(viewerGateway.createVolumeViewport).toHaveBeenCalledTimes(1); // only stack+volume
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

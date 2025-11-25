import { describe, it, expect, vi, beforeEach } from 'vitest';

const engineMocks = vi.hoisted(() => {
  const enableElement = vi.fn();
  const render = vi.fn();
  const setVolumes = vi.fn(async () => {});
  const setBlendMode = vi.fn();
  const setOrientation = vi.fn();
  const setSlabThickness = vi.fn();
  const destroy = vi.fn();
  const getViewport = vi.fn(() => ({
    setVolumes,
    setBlendMode,
    setOrientation,
    setSlabThickness,
    render,
  }));
  const RenderingEngine = vi.fn(() => ({ enableElement, getViewport, destroy }));
  const setUseCPURendering = vi.fn();
  return { enableElement, render, setVolumes, setBlendMode, setOrientation, setSlabThickness, destroy, getViewport, RenderingEngine, setUseCPURendering };
});

const volumeMocks = vi.hoisted(() => {
  const load = vi.fn(async () => {});
  const createAndCacheVolume = vi.fn(async () => ({ volumeId: 'volume-vol', load }));
  return { load, createAndCacheVolume };
});

vi.mock('@cornerstonejs/core', () => ({
  Enums: {
    ViewportType: { ORTHOGRAPHIC: 'orthographic', VOLUME_3D: 'volume3d' },
    OrientationAxis: { AXIAL: 'axial', SAGITTAL: 'sagittal', CORONAL: 'coronal' },
    BlendModes: { COMPOSITE: 'composite', MAXIMUM_INTENSITY_BLEND: 'mip' },
  },
  RenderingEngine: engineMocks.RenderingEngine,
  setUseCPURendering: engineMocks.setUseCPURendering,
}));

vi.mock('@cornerstonejs/core/loaders', () => ({
  volumeLoader: {
    createAndCacheVolume: volumeMocks.createAndCacheVolume,
  },
}));

vi.mock('@cornerstonejs/dicom-image-loader', () => ({
  default: {
    external: {},
    configure: vi.fn(),
  },
}));

vi.mock('dicom-parser', () => ({ default: {} }));

import { createVolumeViewport } from '../src/viewerGateway';

describe('createVolumeViewport', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes an orthographic MIP viewport with orientation and slab thickness', async () => {
    const element = { id: 'mip-el' } as any;
    const imageIds = ['wadors:a', 'wadors:b'];

    const result = await createVolumeViewport({
      element,
      imageIds,
      viewportId: 'vp-mip',
      mode: 'mip',
      orientation: 'sagittal',
      slabThickness: 25,
      useCPU: true,
    });

    expect(engineMocks.setUseCPURendering).toHaveBeenCalledWith(true);
    expect(engineMocks.RenderingEngine).toHaveBeenCalledWith('engine-vp-mip');
    expect(engineMocks.enableElement).toHaveBeenCalledWith({
      viewportId: 'vp-mip',
      element,
      type: 'orthographic',
    });
    expect(volumeMocks.createAndCacheVolume).toHaveBeenCalledWith('volume-vp-mip', { imageIds });
    expect(volumeMocks.load).toHaveBeenCalled();

    const viewport = engineMocks.getViewport.mock.results[0].value;
    expect(engineMocks.setVolumes).toHaveBeenCalledWith([{ volumeId: 'volume-vp-mip' }]);
    expect(engineMocks.setOrientation).toHaveBeenCalledWith('sagittal');
    expect(engineMocks.setBlendMode).toHaveBeenCalledWith('mip');
    expect(engineMocks.setSlabThickness).toHaveBeenCalledWith(25);
    expect(engineMocks.render).toHaveBeenCalled();

    result.setBlendMode('volume');
    expect(engineMocks.setBlendMode).toHaveBeenCalledWith('composite');
    result.setOrientation('coronal');
    expect(engineMocks.setOrientation).toHaveBeenCalledWith('coronal');

    result.destroy();
    expect(engineMocks.destroy).toHaveBeenCalled();
  });

  it('initializes a 3D volume viewport with composite rendering', async () => {
    const element = { id: 'vol-el' } as any;
    const imageIds = ['wadors:c', 'wadors:d'];

    await createVolumeViewport({ element, imageIds, mode: 'volume' });

    expect(engineMocks.enableElement).toHaveBeenCalledWith({
      viewportId: 'volume',
      element,
      type: 'volume3d',
    });
    expect(engineMocks.setOrientation).toHaveBeenCalledWith('axial');
    expect(engineMocks.setBlendMode).toHaveBeenCalledWith('composite');
  });
});

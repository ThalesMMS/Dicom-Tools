import { describe, it, expect, vi } from 'vitest';
import { loadSampleSeriesVolume } from './helpers/sampleSeriesVolume';

const coreMocks = vi.hoisted(() => {
  const enableElement = vi.fn();
  const render = vi.fn();
  const setSlice = vi.fn();
  const setProperties = vi.fn();
  const setStack = vi.fn(async () => {});
  const destroy = vi.fn();
  const getViewport = vi.fn(() => ({ setStack, render, setSlice, setProperties }));
  const RenderingEngine = vi.fn(() => ({ enableElement, getViewport, destroy }));
  const setUseCPURendering = vi.fn();
  return { enableElement, render, setSlice, setProperties, setStack, destroy, getViewport, RenderingEngine, setUseCPURendering };
});

vi.mock('@cornerstonejs/core', () => ({
  Enums: { ViewportType: { STACK: 'stack' } },
  RenderingEngine: coreMocks.RenderingEngine,
  setUseCPURendering: coreMocks.setUseCPURendering,
}));

vi.mock('@cornerstonejs/dicom-image-loader', () => ({
  default: {
    external: {},
    configure: vi.fn(),
  },
}));

import { buildImageIds, createStackViewer } from '../src/viewerGateway';
import { getVoxel } from '../src/volumeUtils';

describe('sample_series volume loading', () => {
  it('loads stack with expected dimensions and passes imageIds to the viewer', async () => {
    const volume = loadSampleSeriesVolume();
    const imageIds = buildImageIds('http://localhost:8080/sample_series', volume.slices);

    const element = { id: 'vol-el' } as any;
    const viewer = await createStackViewer({ element, imageIds, useCPU: true, viewportId: 'vol' });

    expect(coreMocks.setUseCPURendering).toHaveBeenCalledWith(true);
    expect(coreMocks.RenderingEngine).toHaveBeenCalledWith('engine-vol');
    expect(coreMocks.enableElement).toHaveBeenCalledWith({ viewportId: 'vol', element, type: 'stack' });
    expect(coreMocks.setStack).toHaveBeenCalledWith(imageIds);
    expect(coreMocks.render).toHaveBeenCalled();

    expect(volume.rows).toBe(512);
    expect(volume.cols).toBe(512);
    expect(volume.slices).toBe(174);
    expect(volume.spacing?.row).toBeCloseTo(0.48828, 5);
    expect(volume.spacing?.col).toBeCloseTo(0.48828, 5);
    expect(volume.spacing?.slice).toBeCloseTo(1.0, 3);

    const center = getVoxel(volume, Math.floor(volume.slices / 2), Math.floor(volume.rows / 2), Math.floor(volume.cols / 2));
    expect(center).toBeCloseTo(34, 4);

    await viewer.setSlice(1);
    expect(coreMocks.setSlice).toHaveBeenCalledWith(1);
    viewer.setVOI(40, 400);
    expect(coreMocks.setProperties).toHaveBeenCalledWith({ voiRange: { center: 40, width: 400 } });
    viewer.destroy();
    expect(coreMocks.destroy).toHaveBeenCalled();
  });
});

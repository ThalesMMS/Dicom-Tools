import { describe, it, expect, vi } from 'vitest';

vi.mock('@cornerstonejs/core', () => {
  const enableElement = vi.fn();
  const render = vi.fn();
  const setStack = vi.fn();
  const setSlice = vi.fn();
  const setProperties = vi.fn();
  const destroy = vi.fn();
  const getViewport = vi.fn(() => ({
    setStack,
    render,
    setSlice,
    setProperties,
  }));
  const RenderingEngine = vi.fn(() => ({
    enableElement,
    getViewport,
    destroy,
  }));
  return {
    Enums: { ViewportType: { STACK: 'stack' } },
    RenderingEngine,
    setUseCPURendering: vi.fn(),
  };
});

vi.mock('@cornerstonejs/dicom-image-loader', () => ({
  default: {
    external: {},
    configure: vi.fn(),
  },
}));

vi.mock('dicom-parser', () => ({ default: {} }));

import { createStackViewer } from '../src/viewerGateway';

describe('createStackViewer', () => {
  it('configures loader and initializes stack viewport', async () => {
    const element = { id: 'fake-element' } as any;
    const imageIds = ['wadouri:http://host/a.dcm', 'wadouri:http://host/b.dcm'];

    const result = await createStackViewer({ element, imageIds, useCPU: true, viewportId: 'vp1' });

    const core = await import('@cornerstonejs/core');
    const loader = (await import('@cornerstonejs/dicom-image-loader')).default;

    expect(loader.configure).toHaveBeenCalled();
    expect(core.setUseCPURendering).toHaveBeenCalledWith(true);
    expect(core.RenderingEngine).toHaveBeenCalledWith('engine-vp1');

    const instance = (core.RenderingEngine as any).mock.results[0].value;
    expect(instance.enableElement).toHaveBeenCalledWith({
      viewportId: 'vp1',
      element,
      type: 'stack',
    });

    // setStack/render called on viewport
    const viewport = instance.getViewport();
    expect(viewport.setStack).toHaveBeenCalledWith(imageIds);
    expect(viewport.render).toHaveBeenCalled();

    // returned API
    await result.setSlice(1);
    expect(viewport.setSlice).toHaveBeenCalledWith(1);
    result.setVOI(40, 400);
    expect(viewport.setProperties).toHaveBeenCalledWith({ voiRange: { center: 40, width: 400 } });
    result.destroy();
    expect(instance.destroy).toHaveBeenCalled();
  });
});

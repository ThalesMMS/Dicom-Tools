import { describe, it, expect, vi } from 'vitest';

const coreMocks = vi.hoisted(() => {
  const createStackViewer = vi.fn(async () => ({
    setSlice: vi.fn(async () => {}),
    setVOI: vi.fn(),
    destroy: vi.fn(),
  }));
  const createVolumeViewport = vi.fn(async () => ({
    setBlendMode: vi.fn(),
    setOrientation: vi.fn(),
    setSlabThickness: vi.fn(),
    destroy: vi.fn(),
  }));
  return { createStackViewer, createVolumeViewport };
});

vi.mock('../src/viewerGateway', () => coreMocks);

import { createHeadlessViewer } from '../src/viewerAdapter';

describe('headless viewer adapter', () => {
  it('emits progress and slice change events', async () => {
    const onProgress = vi.fn();
    const onError = vi.fn();
    const onSliceChange = vi.fn();

    const viewer = await createHeadlessViewer({
      stack: { element: {} as any, imageIds: ['a'] },
      volume: { element: {} as any, imageIds: ['a'], mode: 'mip' },
      events: { onProgress, onError, onSliceChange },
    });

    expect(onProgress).toHaveBeenCalledWith('stack', 'initializing');
    expect(onProgress).toHaveBeenCalledWith('stack', 'ready');
    expect(onProgress).toHaveBeenCalledWith('volume', 'ready');
    expect(onError).not.toHaveBeenCalled();

    await viewer.stack?.setSlice(3);
    expect(onSliceChange).toHaveBeenCalledWith(3);

    viewer.destroy();
  });

  it('bubbles errors when stack fails', async () => {
    coreMocks.createStackViewer.mockRejectedValueOnce(new Error('fail-stack'));
    const onError = vi.fn();
    await expect(
      createHeadlessViewer({
        stack: { element: {} as any, imageIds: ['a'] },
        events: { onError },
      }),
    ).rejects.toThrow('fail-stack');
    expect(onError).toHaveBeenCalled();
  });
});

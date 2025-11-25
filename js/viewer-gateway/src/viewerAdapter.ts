import { createStackViewer, createVolumeViewport, ViewerOptions, VolumeViewportOptions } from './viewerGateway';

export type ViewerEventHandlers = {
  onProgress?: (phase: 'stack' | 'volume' | 'dicomweb', message: string) => void;
  onError?: (phase: 'stack' | 'volume' | 'dicomweb', error: unknown) => void;
  onSliceChange?: (index: number) => void;
};

export type HeadlessOptions = {
  stack?: ViewerOptions;
  volume?: VolumeViewportOptions;
  events?: ViewerEventHandlers;
};

export type HeadlessViewer = {
  stack?: Awaited<ReturnType<typeof createStackViewer>>;
  volume?: Awaited<ReturnType<typeof createVolumeViewport>>;
  destroy: () => void;
};

export async function createHeadlessViewer(options: HeadlessOptions): Promise<HeadlessViewer> {
  const { stack: stackOpts, volume: volumeOpts, events } = options;
  let stackViewer: Awaited<ReturnType<typeof createStackViewer>> | undefined;
  let volumeViewer: Awaited<ReturnType<typeof createVolumeViewport>> | undefined;

  if (stackOpts) {
    events?.onProgress?.('stack', 'initializing');
    try {
      stackViewer = await createStackViewer(stackOpts);
      events?.onProgress?.('stack', 'ready');
    } catch (err) {
      events?.onError?.('stack', err);
      throw err;
    }
  }

  if (volumeOpts) {
    events?.onProgress?.('volume', 'initializing');
    try {
      volumeViewer = await createVolumeViewport(volumeOpts);
      events?.onProgress?.('volume', 'ready');
    } catch (err) {
      events?.onError?.('volume', err);
      throw err;
    }
  }

  const wrappedStack =
    stackViewer &&
    ({
      ...stackViewer,
      setSlice: async (index: number) => {
        await stackViewer!.setSlice(index);
        events?.onSliceChange?.(index);
      },
    } as typeof stackViewer);

  const viewer: HeadlessViewer = {
    stack: wrappedStack ?? undefined,
    volume: volumeViewer ?? undefined,
    destroy: () => {
      stackViewer?.destroy();
      volumeViewer?.destroy();
    },
  };

  return viewer;
}

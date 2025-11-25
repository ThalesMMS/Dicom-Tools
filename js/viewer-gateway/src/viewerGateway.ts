import * as cornerstoneCore from '@cornerstonejs/core';
import { RenderingEngine, Enums, setUseCPURendering } from '@cornerstonejs/core';
import { volumeLoader } from '@cornerstonejs/core/loaders';
import dicomImageLoader from '@cornerstonejs/dicom-image-loader';
import dicomParser from 'dicom-parser';
import { buildImageIds } from './imageIds';

export type ViewerOptions = {
  element: HTMLElement;
  imageIds: string[];
  viewportId?: string;
  useCPU?: boolean;
};

export type VolumeViewportOptions = {
  element: HTMLElement;
  imageIds: string[];
  viewportId?: string;
  useCPU?: boolean;
  mode?: 'mip' | 'volume';
  orientation?: 'axial' | 'sagittal' | 'coronal';
  slabThickness?: number;
};

function configureLoaders() {
  dicomImageLoader.external.cornerstone = cornerstoneCore as any;
  dicomImageLoader.external.dicomParser = dicomParser;
  dicomImageLoader.configure({
    useWebWorkers: true,
  });
}

export async function createStackViewer(options: ViewerOptions) {
  const { element, imageIds, viewportId = 'stack', useCPU = false } = options;

  configureLoaders();
  setUseCPURendering(useCPU);

  const renderingEngine = new RenderingEngine(`engine-${viewportId}`);
  renderingEngine.enableElement({
    viewportId,
    element,
    type: Enums.ViewportType.STACK,
  });

  const viewport = renderingEngine.getViewport(viewportId);
  await viewport.setStack(imageIds);
  viewport.render();

  return {
    setSlice: async (index: number) => {
      await viewport.setSlice(index);
      viewport.render();
    },
    setVOI: (center: number, width: number) => {
      viewport.setProperties({ voiRange: { center, width } });
      viewport.render();
    },
    destroy: () => renderingEngine.destroy(),
    engine: renderingEngine,
    viewport,
  };
}

export async function createVolumeViewport(options: VolumeViewportOptions) {
  const {
    element,
    imageIds,
    viewportId = 'volume',
    useCPU = false,
    mode = 'volume',
    orientation = 'axial',
    slabThickness,
  } = options;

  configureLoaders();
  setUseCPURendering(useCPU);

  const renderingEngine = new RenderingEngine(`engine-${viewportId}`);
  const viewportType = mode === 'volume' ? Enums.ViewportType.VOLUME_3D : Enums.ViewportType.ORTHOGRAPHIC;

  renderingEngine.enableElement({
    viewportId,
    element,
    type: viewportType,
  });

  const volumeId = `volume-${viewportId}`;
  const volume = await volumeLoader.createAndCacheVolume(volumeId, { imageIds });
  await volume.load();

  const viewport = renderingEngine.getViewport(viewportId) as any;
  if (!viewport?.setVolumes) {
    throw new Error('Volume viewport type not available on rendering engine');
  }

  await viewport.setVolumes([{ volumeId }]);

  const orientationAxis = {
    axial: Enums.OrientationAxis.AXIAL,
    sagittal: Enums.OrientationAxis.SAGITTAL,
    coronal: Enums.OrientationAxis.CORONAL,
  }[orientation];

  if (viewport.setOrientation) {
    viewport.setOrientation(orientationAxis);
  }

  const blendMode = mode === 'mip' ? Enums.BlendModes.MAXIMUM_INTENSITY_BLEND : Enums.BlendModes.COMPOSITE;
  if (viewport.setBlendMode) {
    viewport.setBlendMode(blendMode);
  }

  if (slabThickness && viewport.setSlabThickness) {
    viewport.setSlabThickness(slabThickness);
  }

  viewport.render?.();

  return {
    viewport,
    engine: renderingEngine,
    volume,
    setBlendMode: (nextMode: 'mip' | 'volume') => {
      const next = nextMode === 'mip' ? Enums.BlendModes.MAXIMUM_INTENSITY_BLEND : Enums.BlendModes.COMPOSITE;
      viewport.setBlendMode?.(next);
      viewport.render?.();
    },
    setOrientation: (nextOrientation: 'axial' | 'sagittal' | 'coronal') => {
      const nextAxis = {
        axial: Enums.OrientationAxis.AXIAL,
        sagittal: Enums.OrientationAxis.SAGITTAL,
        coronal: Enums.OrientationAxis.CORONAL,
      }[nextOrientation];
      viewport.setOrientation?.(nextAxis);
      viewport.render?.();
    },
    destroy: () => renderingEngine.destroy(),
  };
}

export { buildImageIds };

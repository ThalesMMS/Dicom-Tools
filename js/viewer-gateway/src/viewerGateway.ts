import * as cornerstoneCore from '@cornerstonejs/core';
import { RenderingEngine, Enums, setUseCPURendering } from '@cornerstonejs/core';
import dicomImageLoader from '@cornerstonejs/dicom-image-loader';
import dicomParser from 'dicom-parser';

export type ViewerOptions = {
  element: HTMLElement;
  imageIds: string[];
  viewportId?: string;
  useCPU?: boolean;
};

// Convert local/relative paths into wadouri: imageIds
export function buildImageIds(baseUrl: string, count: number) {
  const normalizedBase = baseUrl.replace(/\/$/, '');
  return Array.from({ length: count }, (_, i) => {
    const num = String(i + 1).padStart(4, '0');
    return `wadouri:${normalizedBase}/IM-0001-${num}.dcm`;
  });
}

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

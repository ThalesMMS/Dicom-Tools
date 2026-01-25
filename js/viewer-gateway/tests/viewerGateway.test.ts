import { describe, it, expect, vi } from 'vitest';

vi.mock('@cornerstonejs/dicom-image-loader', () => ({
  default: {
    external: {},
    configure: vi.fn(),
  },
}));

vi.mock('@cornerstonejs/core', () => ({
  Enums: { ViewportType: { STACK: 'stack' } },
  RenderingEngine: vi.fn(),
  setUseCPURendering: vi.fn(),
}));

vi.mock('dicom-parser', () => ({ default: {} }));
import { buildImageIds } from '../src/viewerGateway';

describe('buildImageIds', () => {
  it('builds wadouri imageIds with zero-padded numbers', () => {
    const ids = buildImageIds('http://localhost:8080/sample_series', 3);
    expect(ids).toEqual([
      'wadouri:http://localhost:8080/sample_series/IM-0001-0001.dcm',
      'wadouri:http://localhost:8080/sample_series/IM-0001-0002.dcm',
      'wadouri:http://localhost:8080/sample_series/IM-0001-0003.dcm',
    ]);
  });

  it('strips trailing slash from base url', () => {
    const ids = buildImageIds('http://localhost:8080/sample_series/', 1);
    expect(ids[0]).toBe('wadouri:http://localhost:8080/sample_series/IM-0001-0001.dcm');
  });
});

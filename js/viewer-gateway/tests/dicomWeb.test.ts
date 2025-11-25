import { describe, it, expect, vi } from 'vitest';

const searchForInstances = vi.fn();

vi.mock('dicomweb-client', () => ({
  DICOMwebClient: vi.fn().mockImplementation(() => ({
    searchForInstances,
  })),
}));

import { buildWadorsImageId, fetchDicomWebImageIds, parseQidoInstances } from '../src/dicomWeb';

describe('dicomweb-client integration helpers', () => {
  it('parses QIDO responses and sorts by instance number', () => {
    const qido = [
      { '00080018': { Value: ['1.2.3.4.3'] }, '00200013': { Value: ['3'] } },
      { '00080018': { Value: ['1.2.3.4.1'] }, '00200013': { Value: ['1'] } },
      { '00080018': { Value: ['1.2.3.4.2'] }, '00200013': { Value: ['2'] } },
    ];

    const parsed = parseQidoInstances(qido);
    expect(parsed[0].sopInstanceUID).toBe('1.2.3.4.3');
    expect(parsed[0].instanceNumber).toBe(3);
  });

  it('builds wadors imageIds with encoded UIDs', () => {
    const id = buildWadorsImageId('http://server/dicom-web/', '1.2.3', '4.5.6', '7.8.9', 2);
    expect(id).toBe('wadors:http://server/dicom-web/studies/1.2.3/series/4.5.6/instances/7.8.9/frames/2');
  });

  it('fetches wadors imageIds via dicomweb-client, matching dcm4che/dicom-rs endpoints', async () => {
    const qido = [
      { '00080018': { Value: ['sop-2'] }, '00200013': { Value: ['20'] } },
      { '00080018': { Value: ['sop-1'] }, '00200013': { Value: ['10'] } },
      { '00080018': { Value: ['sop-3'] }, '00200013': { Value: [] } },
    ];
    searchForInstances.mockResolvedValueOnce(qido);

    const result = await fetchDicomWebImageIds({
      baseUrl: 'http://server/dicom-web/',
      studyInstanceUID: '1.2.3',
      seriesInstanceUID: '4.5.6',
    });

    expect(searchForInstances).toHaveBeenCalledWith({ studyInstanceUID: '1.2.3', seriesInstanceUID: '4.5.6' });
    expect(result.instances.map((i) => i.instanceNumber)).toEqual([10, 20, Number.POSITIVE_INFINITY]);
    expect(result.imageIds).toEqual([
      'wadors:http://server/dicom-web/studies/1.2.3/series/4.5.6/instances/sop-1/frames/1',
      'wadors:http://server/dicom-web/studies/1.2.3/series/4.5.6/instances/sop-2/frames/1',
      'wadors:http://server/dicom-web/studies/1.2.3/series/4.5.6/instances/sop-3/frames/1',
    ]);
  });
});

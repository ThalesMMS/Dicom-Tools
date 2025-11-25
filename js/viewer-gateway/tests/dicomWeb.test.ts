import { describe, it, expect, vi, beforeEach } from 'vitest';

const searchForInstances = vi.fn();

beforeEach(() => {
  searchForInstances.mockReset();
});

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

  it('ignores entries without SOPInstanceUID and defaults instance number when missing', () => {
    const qido = [
      { '00200013': { Value: ['5'] } }, // missing SOP
      { '00080018': { Value: ['with-uid'] }, '00200013': { Value: [] } }, // missing instance
      { '00080018': { Value: ['upper-uid'] }, '00200013': { Value: [''] } },
    ];

    const parsed = parseQidoInstances(qido);
    expect(parsed).toHaveLength(2);
    expect(parsed[0].sopInstanceUID).toBe('with-uid');
    expect(parsed[0].instanceNumber).toBe(Number.POSITIVE_INFINITY);
    expect(parsed[1].sopInstanceUID).toBe('upper-uid');
    expect(parsed[1].instanceNumber).toBe(0);
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

  it('sorts equal instance numbers lexicographically when fetching imageIds', async () => {
    const qido = [
      { '00080018': { Value: ['uid-b'] }, '00200013': { Value: ['5'] } },
      { '00080018': { Value: ['uid-a'] }, '00200013': { Value: ['5'] } },
    ];
    searchForInstances.mockResolvedValueOnce(qido);

    const result = await fetchDicomWebImageIds({
      baseUrl: 'http://server/dicom-web/',
      studyInstanceUID: '1.2.3',
      seriesInstanceUID: '4.5.6',
    });

    expect(result.imageIds[0]).toContain('uid-a');
    expect(result.imageIds[1]).toContain('uid-b');
  });

  it('stable sorts equal instance numbers lexicographically by UID', () => {
    const qido = [
      { '00080018': { Value: ['uid-b'] }, '00200013': { Value: ['1'] } },
      { '00080018': { Value: ['uid-a'] }, '00200013': { Value: ['1'] } },
    ];

    const parsed = parseQidoInstances(qido);
    const sorted = [...parsed].sort((a, b) => (a.instanceNumber === b.instanceNumber ? a.sopInstanceUID.localeCompare(b.sopInstanceUID) : a.instanceNumber - b.instanceNumber));
    expect(sorted[0].sopInstanceUID).toBe('uid-a');
    expect(sorted[1].sopInstanceUID).toBe('uid-b');
  });

  it('keeps numeric instance numbers without coercion', () => {
    const parsed = parseQidoInstances([{ '00080018': { Value: ['uid-num'] }, '00200013': { Value: [7] } }]);
    expect(parsed[0].instanceNumber).toBe(7);
  });
});

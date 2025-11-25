import { QidoInstance } from '../../src/dicomWeb';

export const qidoMinimal: QidoInstance[] = [
  { '00080018': { Value: ['sop-1'] }, '00200013': { Value: ['1'] } },
  { '00080018': { Value: ['sop-2'] }, '00200013': { Value: ['2'] } },
];

export const qidoWithMissing: QidoInstance[] = [
  { '00200013': { Value: ['5'] } },
  { '00080018': { Value: ['with-uid'] }, '00200013': { Value: [] } },
];

export const qidoEqualNumbers: QidoInstance[] = [
  { '00080018': { Value: ['uid-b'] }, '00200013': { Value: ['1'] } },
  { '00080018': { Value: ['uid-a'] }, '00200013': { Value: ['1'] } },
];

import { api as dicomwebApi } from 'dicomweb-client';

export type DicomWebConfig = {
  baseUrl: string;
  studyInstanceUID: string;
  seriesInstanceUID: string;
};

export type QidoInstance = Record<string, { Value?: unknown[] }>;

export type ParsedInstance = {
  sopInstanceUID: string;
  instanceNumber: number;
};

function normalizeBaseUrl(baseUrl: string) {
  return baseUrl.replace(/\/+$/, '');
}

function getTagValue(dataset: QidoInstance, tag: string) {
  const entry = dataset[tag] || (dataset as any)[tag.toUpperCase()];
  if (!entry || !Array.isArray(entry.Value) || entry.Value.length === 0) return undefined;
  return entry.Value[0];
}

export function buildWadorsImageId(baseUrl: string, studyInstanceUID: string, seriesInstanceUID: string, sopInstanceUID: string, frame = 1) {
  const base = normalizeBaseUrl(baseUrl);
  return `wadors:${base}/studies/${encodeURIComponent(studyInstanceUID)}/series/${encodeURIComponent(seriesInstanceUID)}/instances/${encodeURIComponent(sopInstanceUID)}/frames/${frame}`;
}

export function parseQidoInstances(instances: QidoInstance[]): ParsedInstance[] {
  return instances
    .map((dataset) => {
      const sopInstanceUID = String(getTagValue(dataset, '00080018') || '');
      const instanceNumberRaw = getTagValue(dataset, '00200013');
      const instanceNumber = typeof instanceNumberRaw === 'number' ? instanceNumberRaw : Number(instanceNumberRaw);
      return {
        sopInstanceUID,
        instanceNumber: Number.isFinite(instanceNumber) ? instanceNumber : Number.POSITIVE_INFINITY,
      };
    })
    .filter((entry) => entry.sopInstanceUID.length > 0);
}

export async function fetchDicomWebImageIds(config: DicomWebConfig) {
  const ctor = (dicomwebApi as any).DICOMwebClient;
  const client = new ctor({ url: normalizeBaseUrl(config.baseUrl) });
  const instances = await client.searchForInstances({
    studyInstanceUID: config.studyInstanceUID,
    seriesInstanceUID: config.seriesInstanceUID,
  });

  const parsed = parseQidoInstances(instances).sort((a, b) => {
    if (a.instanceNumber === b.instanceNumber) {
      return a.sopInstanceUID.localeCompare(b.sopInstanceUID);
    }
    return a.instanceNumber - b.instanceNumber;
  });

  const imageIds = parsed.map((entry) => buildWadorsImageId(config.baseUrl, config.studyInstanceUID, config.seriesInstanceUID, entry.sopInstanceUID));
  return { imageIds, instances: parsed };
}

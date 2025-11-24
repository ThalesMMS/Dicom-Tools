import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import dicomParser from 'dicom-parser';
import { buildImageIds } from '../src/imageIds';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const seriesDir = path.resolve(__dirname, '..', '..', '..', 'sample_series');

function readDataset(fileName: string) {
  const filePath = path.join(seriesDir, fileName);
  const buffer = fs.readFileSync(filePath);
  return dicomParser.parseDicom(buffer);
}

function getFiles() {
  return fs
    .readdirSync(seriesDir)
    .filter((f) => f.endsWith('.dcm'))
    .sort();
}

describe('sample_series integrity (app-level)', () => {
  const files = getFiles();

  it('has expected count and builds imageIds', () => {
    expect(files.length).toBeGreaterThan(0);
    const ids = buildImageIds('http://localhost:8080/sample_series', files.length);
    expect(ids[0]).toContain('IM-0001-0001.dcm');
    expect(ids[ids.length - 1]).toContain('IM-0001-0174.dcm');
  });

  it('keeps series metadata consistent and ordered', () => {
    const datasets = files.map((file) => ({ file, data: readDataset(file) }));
    const first = datasets[0].data;

    const patientName = first.string('x00100010');
    const seriesUID = first.string('x0020000e');
    const studyUID = first.string('x0020000d');
    const modality = first.string('x00080060');
    const rows = first.uint16('x00280010');
    const cols = first.uint16('x00280011');
    const spacingStr = first.string('x00280030');
    const [psX, psY] = spacingStr.split('\\').map(Number);

    const zPositions: number[] = [];
    const instances: number[] = [];

    for (const { data } of datasets) {
      expect(data.string('x00100010')).toBe(patientName);
      expect(data.string('x0020000e')).toBe(seriesUID);
      expect(data.string('x0020000d')).toBe(studyUID);
      expect(data.string('x00080060')).toBe(modality);
      expect(data.uint16('x00280010')).toBe(rows);
      expect(data.uint16('x00280011')).toBe(cols);

      const [sx, sy] = data
        .string('x00280030')
        .split('\\')
        .map(Number);
      expect(sx).toBeCloseTo(psX, 5);
      expect(sy).toBeCloseTo(psY, 5);

      const instance = Number(data.string('x00200013'));
      instances.push(instance);

      const posStr = data.string('x00200032');
      const z = Number(posStr.split('\\')[2]);
      zPositions.push(z);
    }

    // Instances must be strictly increasing
    const sortedInstances = [...instances].sort((a, b) => a - b);
    expect(sortedInstances).toEqual(instances);

    // Z spacing should be ~1mm
    for (let i = 1; i < zPositions.length; i++) {
      const delta = zPositions[i] - zPositions[i - 1];
      expect(Math.abs(delta - 1)).toBeLessThan(1e-3);
    }
  });
});

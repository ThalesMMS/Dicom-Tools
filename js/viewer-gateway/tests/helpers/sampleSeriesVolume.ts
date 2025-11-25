import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import dicomParser from 'dicom-parser';
import { VolumeData } from '../../src/volumeUtils';

let cached: VolumeData | null = null;

function resolveSeriesDir() {
  const __dirname = path.dirname(fileURLToPath(import.meta.url));
  return path.resolve(__dirname, '..', '..', '..', '..', 'sample_series');
}

function computeSliceSpacing(zPositions: number[], fallback: number) {
  if (zPositions.length < 2) return fallback;
  let total = 0;
  for (let i = 1; i < zPositions.length; i++) {
    total += Math.abs(zPositions[i] - zPositions[i - 1]);
  }
  return total / (zPositions.length - 1);
}

export function loadSampleSeriesVolume(): VolumeData {
  if (cached) return cached;

  const seriesDir = resolveSeriesDir();
  const files = fs.readdirSync(seriesDir).filter((f) => f.endsWith('.dcm')).sort();
  if (files.length === 0) throw new Error('sample_series folder is empty');

  const firstDataset = dicomParser.parseDicom(fs.readFileSync(path.join(seriesDir, files[0])));
  const rows = firstDataset.uint16('x00280010');
  const cols = firstDataset.uint16('x00280011');
  const pixelCount = rows * cols;

  const spacingTokens = firstDataset.string('x00280030')?.split('\\').map(Number) || [1, 1];
  const spacingRow = spacingTokens[0] ?? 1;
  const spacingCol = spacingTokens[1] ?? 1;
  const voxelData = new Float32Array(pixelCount * files.length);
  const zPositions: number[] = [];

  files.forEach((file, sliceIndex) => {
    const dataset = sliceIndex === 0 ? firstDataset : dicomParser.parseDicom(fs.readFileSync(path.join(seriesDir, file)));
    const pixelData = dataset.elements.x7fe00010;
    if (!pixelData) throw new Error(`PixelData missing for ${file}`);

    const sliceSlope = parseFloat(dataset.floatString('x00281053') || '1');
    const sliceIntercept = parseFloat(dataset.floatString('x00281052') || '0');
    const representation = dataset.uint16('x00280103');
    const view = representation === 0
      ? new Uint16Array(dataset.byteArray.buffer, pixelData.dataOffset, pixelCount)
      : new Int16Array(dataset.byteArray.buffer, pixelData.dataOffset, pixelCount);

    const offset = sliceIndex * pixelCount;
    for (let i = 0; i < pixelCount; i++) {
      voxelData[offset + i] = view[i] * sliceSlope + sliceIntercept;
    }

    const position = dataset.string('x00200032');
    if (position) {
      const parts = position.split('\\');
      const z = Number(parts[2]);
      if (!Number.isNaN(z)) zPositions.push(z);
    }
  });

  const spacingSlice = computeSliceSpacing(zPositions, parseFloat(firstDataset.floatString('x00180050') || '1'));

  cached = {
    rows,
    cols,
    slices: files.length,
    spacing: {
      row: spacingRow,
      col: spacingCol,
      slice: spacingSlice,
    },
    voxelData,
  };

  return cached;
}

import { describe, it, expect } from 'vitest';
import { extractLabelSlice, VolumeData } from '../src/volumeUtils';
import { loadSampleSeriesVolume } from './helpers/sampleSeriesVolume';

function buildCenterPatchMask(volume: VolumeData) {
  const labels = new Uint8Array(volume.rows * volume.cols * volume.slices);
  const midRow = Math.floor(volume.rows / 2);
  const midCol = Math.floor(volume.cols / 2);
  const midSlice = Math.floor(volume.slices / 2);

  const offsets = [-1, 0, 1];
  for (const dr of offsets) {
    for (const dc of offsets) {
      const row = midRow + dr;
      const col = midCol + dc;
      const idx = midSlice * volume.rows * volume.cols + row * volume.cols + col;
      labels[idx] = 1;
    }
  }
  return labels;
}

function countLabels(data: Uint8Array) {
  return data.reduce((acc, value) => acc + (value > 0 ? 1 : 0), 0);
}

describe('segmentation overlay projections', () => {
  it('projects the same mask coherently across axial/sagittal/coronal views', () => {
    const volume = loadSampleSeriesVolume();
    const labels = buildCenterPatchMask(volume);

    const labelVolume = { rows: volume.rows, cols: volume.cols, slices: volume.slices, labels };
    const midRow = Math.floor(volume.rows / 2);
    const midCol = Math.floor(volume.cols / 2);
    const midSlice = Math.floor(volume.slices / 2);

    const axial = extractLabelSlice(labelVolume, 'axial', midSlice);
    expect(axial.width).toBe(volume.cols);
    expect(axial.height).toBe(volume.rows);
    expect(axial.data[midRow * axial.width + midCol]).toBe(1);
    expect(countLabels(axial.data)).toBe(9);
    expect(axial.data[0]).toBe(0);

    const sagittal = extractLabelSlice(labelVolume, 'sagittal', midCol);
    expect(sagittal.width).toBe(volume.slices);
    expect(sagittal.height).toBe(volume.rows);
    expect(sagittal.data[midRow * sagittal.width + midSlice]).toBe(1);
    expect(countLabels(sagittal.data)).toBe(3);
    expect(sagittal.data[0]).toBe(0);

    const coronal = extractLabelSlice(labelVolume, 'coronal', midRow);
    expect(coronal.width).toBe(volume.cols);
    expect(coronal.height).toBe(volume.slices);
    expect(coronal.data[midSlice * coronal.width + midCol]).toBe(1);
    expect(countLabels(coronal.data)).toBe(3);
    expect(coronal.data[0]).toBe(0);
  });
});

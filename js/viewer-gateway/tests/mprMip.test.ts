import { describe, it, expect } from 'vitest';
import { computeMIP, extractCoronalSlice, extractSagittalSlice } from '../src/volumeUtils';
import { loadSampleSeriesVolume } from './helpers/sampleSeriesVolume';

describe('MPR and MIP derivations', () => {
  it('generates sagittal and coronal slices with expected central values', () => {
    const volume = loadSampleSeriesVolume();
    const midCol = Math.floor(volume.cols / 2);
    const midRow = Math.floor(volume.rows / 2);
    const midSlice = Math.floor(volume.slices / 2);

    const sagittal = extractSagittalSlice(volume, midCol);
    expect(sagittal.width).toBe(volume.slices);
    expect(sagittal.height).toBe(volume.rows);

    const sagCenter = sagittal.data[midRow * sagittal.width + midSlice];
    const sagStart = sagittal.data[midRow * sagittal.width];
    const sagEnd = sagittal.data[midRow * sagittal.width + (volume.slices - 1)];
    expect(sagCenter).toBeCloseTo(34, 4);
    expect(sagStart).toBeCloseTo(59, 3);
    expect(sagEnd).toBeCloseTo(-1001, 3);

    const coronal = extractCoronalSlice(volume, midRow);
    expect(coronal.width).toBe(volume.cols);
    expect(coronal.height).toBe(volume.slices);

    const corCenter = coronal.data[midSlice * coronal.width + midCol];
    const corFirst = coronal.data[0 * coronal.width + midCol];
    const corEdge = coronal.data[midSlice * coronal.width];
    expect(corCenter).toBeCloseTo(34, 4);
    expect(corFirst).toBeCloseTo(59, 3);
    expect(corEdge).toBeCloseTo(-1006, 2);
  });

  it('computes a MIP volume projection with stable anchor pixels', () => {
    const volume = loadSampleSeriesVolume();
    const mip = computeMIP(volume);

    expect(mip.width).toBe(volume.cols);
    expect(mip.height).toBe(volume.rows);

    const midRow = Math.floor(mip.height / 2);
    const midCol = Math.floor(mip.width / 2);
    const centerVal = mip.data[midRow * mip.width + midCol];
    const edgeVal = mip.data[0];
    const offAxisVal = mip.data[100 * mip.width + 200];

    expect(centerVal).toBeCloseTo(2248, 3);
    expect(edgeVal).toBeCloseTo(-991, 3);
    expect(offAxisVal).toBeCloseTo(3058, 0);
  });
});

import { describe, it, expect } from 'vitest';
import {
  buildThresholdLabelMap,
  computeRoiStats,
  countLabelVoxels,
  extractAxialSlice,
  extractCoronalSlice,
  extractSagittalSlice,
  getVoxel,
  indexToWorld,
  worldToIndex,
  cropSlice,
} from '../src/volumeUtils';
import { loadSampleSeriesVolume } from './helpers/sampleSeriesVolume';

describe('sample_series physical metadata and measurements', () => {
  const volume = loadSampleSeriesVolume();

  it('exposes spacing/origin/orientation consistent with ITK/VTK baselines', () => {
    expect(volume.spacing?.row).toBeCloseTo(0.48828125, 6);
    expect(volume.spacing?.col).toBeCloseTo(0.48828125, 6);
    expect(volume.spacing?.slice).toBeCloseTo(1.0, 6);
    expect(volume.origin).toEqual([-124.755859375, -335.755859375, 30.5]);
    expect(volume.orientation?.row).toEqual([1, 0, 0]);
    expect(volume.orientation?.col).toEqual([0, 1, 0]);

    const midRow = Math.floor(volume.rows / 2);
    const midCol = Math.floor(volume.cols / 2);
    const midSlice = Math.floor(volume.slices / 2);
    const world = indexToWorld(volume, midSlice, midRow, midCol);
    expect(world[0]).toBeCloseTo(0.244140625, 6);
    expect(world[1]).toBeCloseTo(-210.755859375, 6);
    expect(world[2]).toBeCloseTo(117.5, 6);
  });

  it('round-trips index/world coordinates for crosshair alignment across viewports', () => {
    const point = { row: 120, col: 240, slice: 50 };
    const world = indexToWorld(volume, point.slice, point.row, point.col);
    const indices = worldToIndex(volume, world);

    expect(indices.row).toBeCloseTo(point.row, 4);
    expect(indices.col).toBeCloseTo(point.col, 4);
    expect(indices.slice).toBeCloseTo(point.slice, 4);

    const axialValue = getVoxel(volume, point.slice, point.row, point.col);
    const sagittal = extractSagittalSlice(volume, Math.round(indices.col));
    const sagittalValue = sagittal.data[Math.round(indices.row) * sagittal.width + Math.round(indices.slice)];
    const coronal = extractCoronalSlice(volume, Math.round(indices.row));
    const coronalValue = coronal.data[Math.round(indices.slice) * coronal.width + Math.round(indices.col)];

    expect(sagittalValue).toBeCloseTo(axialValue, 3);
    expect(coronalValue).toBeCloseTo(axialValue, 3);
  });

  it('computes ROI stats in line with SimpleITK/VTK reference values', () => {
    const midSlice = Math.floor(volume.slices / 2);
    const slice = extractAxialSlice(volume, midSlice);
    const side = 32;
    const startRow = Math.floor(volume.rows / 2 - side / 2);
    const startCol = Math.floor(volume.cols / 2 - side / 2);
    const roi = cropSlice(slice, startRow, startCol, side, side);

    const stats = computeRoiStats(roi, volume.spacing);
    expect(stats.count).toBe(side * side);
    expect(stats.mean).toBeCloseTo(33.4267, 3);
    expect(stats.std).toBeCloseTo(7.2134, 3);
    expect(stats.min).toBe(10);
    expect(stats.max).toBe(55);
    expect(stats.area).toBeCloseTo(244.140625, 6);
  });

  it('counts segmentation label voxels consistently with dicom-numpy baselines', () => {
    const labelVolume = buildThresholdLabelMap(volume, [
      { label: 2, predicate: (value) => value >= 300 },
      { label: 1, predicate: (value) => value > 30 },
    ]);
    const counts = countLabelVoxels(labelVolume);

    expect(counts.get(0)).toBe(37613474);
    expect(counts.get(1)).toBe(5063114);
    expect(counts.get(2)).toBe(2936468);
  });
});

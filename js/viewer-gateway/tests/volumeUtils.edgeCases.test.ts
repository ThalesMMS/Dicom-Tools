import { describe, it, expect } from 'vitest';
import {
  buildThresholdLabelMap,
  computeRoiStats,
  countLabelVoxels,
  cropSlice,
  indexToWorld,
  worldToIndex,
  VolumeData,
  Slice2D,
} from '../src/volumeUtils';

function makeVolume(): VolumeData {
  return {
    rows: 2,
    cols: 2,
    slices: 2,
    voxelData: new Float32Array([0, 10, 20, 30, 40, 50, 60, 70]),
    spacing: { row: 2, col: 3, slice: 4 },
    origin: [10, 20, 30],
    orientation: { row: [1, 0, 0], col: [0, 1, 0] },
  };
}

function sliceFrom(array: number[], width: number): Slice2D {
  return { width, height: array.length / width, data: new Float32Array(array) };
}

describe('volumeUtils edge cases', () => {
  it('computes index/world round-trip with custom spacing/origin', () => {
    const volume = makeVolume();
    const world = indexToWorld(volume, 1, 1, 1);
    expect(world).toEqual([12, 23, 34]);

    const indices = worldToIndex(volume, world);
    expect(indices.row).toBeCloseTo(1);
    expect(indices.col).toBeCloseTo(1);
    expect(indices.slice).toBeCloseTo(1);
  });

  it('returns zeroed ROI stats for empty slices', () => {
    const stats = computeRoiStats({ width: 0, height: 0, data: new Float32Array([]) });
    expect(stats).toEqual({ count: 0, mean: 0, std: 0, min: 0, max: 0, area: 0 });
  });

  it('crops ROI and computes stats with spacing-aware area', () => {
    const slice = sliceFrom([1, 2, 3, 4], 2);
    const cropped = cropSlice(slice, 0, 0, 1, 2);
    expect(Array.from(cropped.data)).toEqual([1, 2]);

    const stats = computeRoiStats(cropped, { row: 0.5, col: 2 });
    expect(stats.count).toBe(2);
    expect(stats.mean).toBe(1.5);
    expect(stats.std).toBeCloseTo(0.5);
    expect(stats.area).toBeCloseTo(2);
  });

  it('builds threshold label map with default and custom buffers', () => {
    const volume = makeVolume();
    const thresholds = [
      { label: 2, predicate: (v: number) => v >= 50 },
      { label: 1, predicate: (v: number) => v >= 20 },
    ];
    const map = buildThresholdLabelMap(volume, thresholds);
    expect(countLabelVoxels(map).get(2)).toBe(3);
    expect(countLabelVoxels(map).get(1)).toBe(3);
    expect(countLabelVoxels(map).get(0)).toBe(2);

    const target = new Uint8Array(volume.voxelData.length);
    const mapWithTarget = buildThresholdLabelMap(volume, thresholds, target);
    expect(mapWithTarget.labels).toBe(target);
  });

  it('throws when target label map has incorrect length', () => {
    const volume = makeVolume();
    const badTarget = new Uint8Array(3);
    expect(() => buildThresholdLabelMap(volume, [], badTarget)).toThrow(/size does not match/);
  });
});

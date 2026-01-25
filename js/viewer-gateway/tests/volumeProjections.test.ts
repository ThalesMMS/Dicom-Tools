import { describe, it, expect } from 'vitest';
import { computeMIP, computeMinIP, computeAIP, extractAxialSlice } from '../src/volumeUtils';
import { loadSampleSeriesVolume } from './helpers/sampleSeriesVolume';

describe('Volume projection modes', () => {
  const volume = loadSampleSeriesVolume();

  describe('Maximum Intensity Projection (MIP)', () => {
    it('selects the maximum voxel value along the projection ray', () => {
      const mip = computeMIP(volume);

      expect(mip.width).toBe(volume.cols);
      expect(mip.height).toBe(volume.rows);

      // MIP values should always be >= any individual slice value at same position
      const midSlice = extractAxialSlice(volume, Math.floor(volume.slices / 2));
      const midRow = Math.floor(volume.rows / 2);
      const midCol = Math.floor(volume.cols / 2);

      const mipValue = mip.data[midRow * mip.width + midCol];
      const sliceValue = midSlice.data[midRow * midSlice.width + midCol];

      expect(mipValue).toBeGreaterThanOrEqual(sliceValue);
    });

    it('produces stable anchor pixel values', () => {
      const mip = computeMIP(volume);
      const centerVal = mip.data[Math.floor(mip.height / 2) * mip.width + Math.floor(mip.width / 2)];
      const edgeVal = mip.data[0];

      expect(centerVal).toBeCloseTo(2248, 3);
      expect(edgeVal).toBeCloseTo(-991, 3);
    });
  });

  describe('Minimum Intensity Projection (MinIP)', () => {
    it('selects the minimum voxel value along the projection ray', () => {
      const minip = computeMinIP(volume);

      expect(minip.width).toBe(volume.cols);
      expect(minip.height).toBe(volume.rows);

      // MinIP values should always be <= any individual slice value at same position
      const midSlice = extractAxialSlice(volume, Math.floor(volume.slices / 2));
      const midRow = Math.floor(volume.rows / 2);
      const midCol = Math.floor(volume.cols / 2);

      const minipValue = minip.data[midRow * minip.width + midCol];
      const sliceValue = midSlice.data[midRow * midSlice.width + midCol];

      expect(minipValue).toBeLessThanOrEqual(sliceValue);
    });

    it('produces values lower than or equal to MIP at every position', () => {
      const mip = computeMIP(volume);
      const minip = computeMinIP(volume);

      // Sample several positions to verify MinIP <= MIP
      const positions = [
        { r: 0, c: 0 },
        { r: Math.floor(volume.rows / 2), c: Math.floor(volume.cols / 2) },
        { r: volume.rows - 1, c: volume.cols - 1 },
        { r: 100, c: 200 },
      ];

      for (const { r, c } of positions) {
        const idx = r * volume.cols + c;
        expect(minip.data[idx]).toBeLessThanOrEqual(mip.data[idx]);
      }
    });

    it('produces stable anchor pixel values for air/dark structure detection', () => {
      const minip = computeMinIP(volume);
      const centerVal = minip.data[Math.floor(minip.height / 2) * minip.width + Math.floor(minip.width / 2)];
      const edgeVal = minip.data[0];

      // MinIP should show minimum values (useful for detecting airways, dark regions)
      expect(centerVal).toBeLessThan(0);
      expect(edgeVal).toBeLessThan(-900);
    });
  });

  describe('Average Intensity Projection (AIP)', () => {
    it('computes the average voxel value along the projection ray', () => {
      const aip = computeAIP(volume);

      expect(aip.width).toBe(volume.cols);
      expect(aip.height).toBe(volume.rows);
    });

    it('produces values between MinIP and MIP at every position', () => {
      const mip = computeMIP(volume);
      const minip = computeMinIP(volume);
      const aip = computeAIP(volume);

      const positions = [
        { r: 0, c: 0 },
        { r: Math.floor(volume.rows / 2), c: Math.floor(volume.cols / 2) },
        { r: volume.rows - 1, c: volume.cols - 1 },
        { r: 100, c: 200 },
      ];

      for (const { r, c } of positions) {
        const idx = r * volume.cols + c;
        expect(aip.data[idx]).toBeGreaterThanOrEqual(minip.data[idx]);
        expect(aip.data[idx]).toBeLessThanOrEqual(mip.data[idx]);
      }
    });

    it('verifies manual average calculation matches function output', () => {
      const aip = computeAIP(volume);
      const testRow = 256;
      const testCol = 256;

      // Manually compute average for this ray
      let sum = 0;
      for (let s = 0; s < volume.slices; s++) {
        const idx = s * volume.rows * volume.cols + testRow * volume.cols + testCol;
        sum += volume.voxelData[idx];
      }
      const manualAvg = sum / volume.slices;

      const aipValue = aip.data[testRow * aip.width + testCol];
      expect(aipValue).toBeCloseTo(manualAvg, 4);
    });
  });

  describe('Projection comparison for clinical use cases', () => {
    it('MIP highlights bone/contrast (high intensity structures)', () => {
      const mip = computeMIP(volume);
      const stats = {
        max: -Infinity,
        min: Infinity,
        sum: 0,
      };

      for (let i = 0; i < mip.data.length; i++) {
        const v = mip.data[i];
        if (v > stats.max) stats.max = v;
        if (v < stats.min) stats.min = v;
        stats.sum += v;
      }

      const mean = stats.sum / mip.data.length;

      // MIP should have high maximum values (bone/contrast)
      expect(stats.max).toBeGreaterThan(2000);
      expect(mean).toBeGreaterThan(-500);
    });

    it('MinIP highlights air/dark regions (low intensity structures)', () => {
      const minip = computeMinIP(volume);
      const stats = {
        max: -Infinity,
        min: Infinity,
      };

      for (let i = 0; i < minip.data.length; i++) {
        const v = minip.data[i];
        if (v > stats.max) stats.max = v;
        if (v < stats.min) stats.min = v;
      }

      // MinIP should have very low minimum values (air ~ -1000 HU)
      expect(stats.min).toBeLessThan(-900);
    });
  });
});

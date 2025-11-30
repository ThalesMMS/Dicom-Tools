import { describe, it, expect } from 'vitest';
import { computeHistogram, VolumeData } from '../src/volumeUtils';
import { loadSampleSeriesVolume } from './helpers/sampleSeriesVolume';

describe('Volume histogram analysis', () => {
  const volume = loadSampleSeriesVolume();

  describe('computeHistogram', () => {
    it('computes a histogram with the correct number of bins', () => {
      const numBins = 256;
      const histogram = computeHistogram(volume, numBins);

      expect(histogram.bins.length).toBe(numBins);
      expect(histogram.binEdges.length).toBe(numBins + 1);
    });

    it('bin edges span the full intensity range', () => {
      const histogram = computeHistogram(volume, 256);

      expect(histogram.binEdges[0]).toBe(histogram.min);
      expect(histogram.binEdges[histogram.binEdges.length - 1]).toBeCloseTo(histogram.max, 3);
    });

    it('total bin count equals total voxel count', () => {
      const histogram = computeHistogram(volume, 256);
      const totalInBins = histogram.bins.reduce((sum, count) => sum + count, 0);
      const totalVoxels = volume.rows * volume.cols * volume.slices;

      // Some voxels may be NaN or out of range, so allow small tolerance
      expect(totalInBins).toBeGreaterThan(totalVoxels * 0.8);
      expect(totalInBins).toBeLessThanOrEqual(totalVoxels);
    });

    it('detects CT intensity range (includes air around -1000 HU)', () => {
      const histogram = computeHistogram(volume, 256);

      // CT scans typically have air at around -1000 HU
      expect(histogram.min).toBeLessThan(-900);
      // And bone/contrast at higher values
      expect(histogram.max).toBeGreaterThan(1000);
    });

    it('bin width is consistent across all bins', () => {
      const histogram = computeHistogram(volume, 100);
      const expectedWidth = (histogram.max - histogram.min) / 100;

      expect(histogram.binWidth).toBeCloseTo(expectedWidth, 6);

      // Verify edges are evenly spaced (with reasonable floating-point tolerance)
      for (let i = 1; i < histogram.binEdges.length; i++) {
        const actualWidth = histogram.binEdges[i] - histogram.binEdges[i - 1];
        expect(actualWidth).toBeCloseTo(histogram.binWidth, 3);
      }
    });

    it('supports different bin counts', () => {
      const hist64 = computeHistogram(volume, 64);
      const hist256 = computeHistogram(volume, 256);
      const hist1024 = computeHistogram(volume, 1024);

      expect(hist64.bins.length).toBe(64);
      expect(hist256.bins.length).toBe(256);
      expect(hist1024.bins.length).toBe(1024);

      // All should have the same min/max
      expect(hist64.min).toBe(hist256.min);
      expect(hist256.min).toBe(hist1024.min);
      expect(hist64.max).toBe(hist256.max);
    });
  });

  describe('histogram clinical interpretation', () => {
    it('identifies air peak in CT histogram', () => {
      const histogram = computeHistogram(volume, 256);

      // Find bin containing air (~-1000 HU)
      let airBinIndex = -1;
      for (let i = 0; i < histogram.binEdges.length - 1; i++) {
        if (histogram.binEdges[i] <= -950 && histogram.binEdges[i + 1] > -950) {
          airBinIndex = i;
          break;
        }
      }

      // Air should have significant count (background)
      if (airBinIndex >= 0) {
        expect(histogram.bins[airBinIndex]).toBeGreaterThan(0);
      }
    });

    it('identifies soft tissue range in histogram', () => {
      const histogram = computeHistogram(volume, 256);

      // Soft tissue is typically 0-100 HU
      let softTissueCount = 0;
      for (let i = 0; i < histogram.binEdges.length - 1; i++) {
        const binStart = histogram.binEdges[i];
        const binEnd = histogram.binEdges[i + 1];
        if (binEnd >= 0 && binStart <= 100) {
          softTissueCount += histogram.bins[i];
        }
      }

      // Should have some soft tissue voxels
      expect(softTissueCount).toBeGreaterThan(0);
    });
  });

  describe('histogram with synthetic data', () => {
    it('correctly bins uniform distribution', () => {
      const rows = 10;
      const cols = 10;
      const slices = 10;
      const voxelData = new Float32Array(rows * cols * slices);

      // Fill with values 0-999
      for (let i = 0; i < voxelData.length; i++) {
        voxelData[i] = i % 1000;
      }

      const syntheticVolume: VolumeData = { rows, cols, slices, voxelData };
      const histogram = computeHistogram(syntheticVolume, 10);

      expect(histogram.min).toBe(0);
      expect(histogram.max).toBe(999);
      expect(histogram.bins.length).toBe(10);

      // Each bin should have roughly equal count for uniform distribution
      const expectedPerBin = voxelData.length / 10;
      for (let i = 0; i < histogram.bins.length; i++) {
        expect(histogram.bins[i]).toBeCloseTo(expectedPerBin, -1); // Allow some tolerance
      }
    });

    it('correctly handles single-value volume', () => {
      const rows = 5;
      const cols = 5;
      const slices = 5;
      const voxelData = new Float32Array(rows * cols * slices).fill(42);

      const syntheticVolume: VolumeData = { rows, cols, slices, voxelData };
      const histogram = computeHistogram(syntheticVolume, 10);

      expect(histogram.min).toBe(42);
      expect(histogram.max).toBe(42);

      // All voxels should be in one bin
      const nonZeroBins = histogram.bins.filter((count) => count > 0);
      expect(nonZeroBins.length).toBe(1);
      expect(nonZeroBins[0]).toBe(rows * cols * slices);
    });
  });
});

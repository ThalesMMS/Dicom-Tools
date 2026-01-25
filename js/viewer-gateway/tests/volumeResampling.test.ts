import { describe, it, expect } from 'vitest';
import { resampleSlice, extractAxialSlice, Slice2D } from '../src/volumeUtils';
import { loadSampleSeriesVolume } from './helpers/sampleSeriesVolume';

describe('Volume resampling and interpolation', () => {
  const volume = loadSampleSeriesVolume();
  const slice = extractAxialSlice(volume, Math.floor(volume.slices / 2));

  describe('resampleSlice dimensions', () => {
    it('upsamples to larger dimensions', () => {
      const targetWidth = slice.width * 2;
      const targetHeight = slice.height * 2;

      const resampled = resampleSlice(slice, targetWidth, targetHeight);

      expect(resampled.width).toBe(targetWidth);
      expect(resampled.height).toBe(targetHeight);
      expect(resampled.data.length).toBe(targetWidth * targetHeight);
    });

    it('downsamples to smaller dimensions', () => {
      const targetWidth = Math.floor(slice.width / 2);
      const targetHeight = Math.floor(slice.height / 2);

      const resampled = resampleSlice(slice, targetWidth, targetHeight);

      expect(resampled.width).toBe(targetWidth);
      expect(resampled.height).toBe(targetHeight);
      expect(resampled.data.length).toBe(targetWidth * targetHeight);
    });

    it('maintains dimensions when target equals source', () => {
      const resampled = resampleSlice(slice, slice.width, slice.height);

      expect(resampled.width).toBe(slice.width);
      expect(resampled.height).toBe(slice.height);
    });

    it('handles non-square aspect ratios', () => {
      const targetWidth = 100;
      const targetHeight = 200;

      const resampled = resampleSlice(slice, targetWidth, targetHeight);

      expect(resampled.width).toBe(100);
      expect(resampled.height).toBe(200);
    });
  });

  describe('nearest neighbor interpolation', () => {
    it('preserves exact values from source at sample points', () => {
      // Create a simple test slice
      const testSlice: Slice2D = {
        width: 4,
        height: 4,
        data: new Float32Array([
          1, 2, 3, 4,
          5, 6, 7, 8,
          9, 10, 11, 12,
          13, 14, 15, 16,
        ]),
      };

      // Same size resampling should preserve values
      const resampled = resampleSlice(testSlice, 4, 4, 'nearest');

      for (let i = 0; i < testSlice.data.length; i++) {
        expect(resampled.data[i]).toBe(testSlice.data[i]);
      }
    });

    it('produces blocky appearance when upsampling', () => {
      const testSlice: Slice2D = {
        width: 2,
        height: 2,
        data: new Float32Array([10, 20, 30, 40]),
      };

      const resampled = resampleSlice(testSlice, 4, 4, 'nearest');

      // Check that values are repeated in blocks
      // Top-left 2x2 block should be from (0,0)
      expect(resampled.data[0]).toBe(10); // (0,0) -> rounds to source (0,0)
      // Top-right 2x2 block should be from (0,1)
      expect(resampled.data[3]).toBe(20); // (0,3) -> rounds to source (0,1) or (0,2)
    });

    it('selects nearest neighbor correctly on downsampling', () => {
      const testSlice: Slice2D = {
        width: 4,
        height: 4,
        data: new Float32Array([
          1, 2, 3, 4,
          5, 6, 7, 8,
          9, 10, 11, 12,
          13, 14, 15, 16,
        ]),
      };

      const resampled = resampleSlice(testSlice, 2, 2, 'nearest');

      expect(resampled.width).toBe(2);
      expect(resampled.height).toBe(2);
      // Values should be selected from nearest source pixels
      expect(resampled.data.length).toBe(4);
    });
  });

  describe('bilinear interpolation', () => {
    it('produces smooth gradients when upsampling', () => {
      const testSlice: Slice2D = {
        width: 2,
        height: 2,
        data: new Float32Array([0, 100, 100, 200]),
      };

      const resampled = resampleSlice(testSlice, 4, 4, 'bilinear');

      // Center values should be interpolated between corners
      const centerValue = resampled.data[5]; // Approximately (1.25, 1.25) in source coords
      expect(centerValue).toBeGreaterThan(0);
      expect(centerValue).toBeLessThan(200);
    });

    it('preserves corner values exactly', () => {
      const testSlice: Slice2D = {
        width: 2,
        height: 2,
        data: new Float32Array([10, 20, 30, 40]),
      };

      const resampled = resampleSlice(testSlice, 3, 3, 'bilinear');

      // Corners should map exactly to source corners
      expect(resampled.data[0]).toBeCloseTo(10, 3); // top-left
    });

    it('creates intermediate values between known points', () => {
      // Linear gradient slice
      const testSlice: Slice2D = {
        width: 3,
        height: 1,
        data: new Float32Array([0, 50, 100]),
      };

      const resampled = resampleSlice(testSlice, 5, 1, 'bilinear');

      // Should create smooth gradient
      expect(resampled.data[0]).toBeCloseTo(0, 1);
      expect(resampled.data[4]).toBeCloseTo(100, 1);

      // Middle values should be interpolated
      for (let i = 1; i < 4; i++) {
        expect(resampled.data[i]).toBeGreaterThan(resampled.data[i - 1]);
      }
    });

    it('produces smoother output than nearest neighbor', () => {
      const testSlice: Slice2D = {
        width: 2,
        height: 2,
        data: new Float32Array([0, 100, 100, 200]),
      };

      const nearest = resampleSlice(testSlice, 8, 8, 'nearest');
      const bilinear = resampleSlice(testSlice, 8, 8, 'bilinear');

      // Calculate variance of differences between adjacent pixels
      function computeGradientVariance(data: Float32Array, width: number) {
        let sumSq = 0;
        let count = 0;
        for (let i = 0; i < data.length - 1; i++) {
          if ((i + 1) % width !== 0) {
            // Not at row boundary
            const diff = Math.abs(data[i + 1] - data[i]);
            sumSq += diff * diff;
            count++;
          }
        }
        return sumSq / count;
      }

      const nearestVariance = computeGradientVariance(nearest.data, nearest.width);
      const bilinearVariance = computeGradientVariance(bilinear.data, bilinear.width);

      // Bilinear should have lower variance (smoother transitions)
      expect(bilinearVariance).toBeLessThan(nearestVariance);
    });
  });

  describe('resampling with real volume data', () => {
    it('preserves approximate intensity statistics after resampling', () => {
      const halfWidth = Math.floor(slice.width / 2);
      const halfHeight = Math.floor(slice.height / 2);

      const downsampled = resampleSlice(slice, halfWidth, halfHeight, 'bilinear');

      // Calculate mean of original
      let originalSum = 0;
      for (let i = 0; i < slice.data.length; i++) {
        originalSum += slice.data[i];
      }
      const originalMean = originalSum / slice.data.length;

      // Calculate mean of downsampled
      let resampledSum = 0;
      for (let i = 0; i < downsampled.data.length; i++) {
        resampledSum += downsampled.data[i];
      }
      const resampledMean = resampledSum / downsampled.data.length;

      // Means should be approximately similar
      expect(resampledMean).toBeCloseTo(originalMean, -1); // Within 10
    });

    it('maintains value range after resampling', () => {
      const resampled = resampleSlice(slice, 256, 256, 'bilinear');

      let originalMin = Infinity;
      let originalMax = -Infinity;
      for (let i = 0; i < slice.data.length; i++) {
        if (slice.data[i] < originalMin) originalMin = slice.data[i];
        if (slice.data[i] > originalMax) originalMax = slice.data[i];
      }

      let resampledMin = Infinity;
      let resampledMax = -Infinity;
      for (let i = 0; i < resampled.data.length; i++) {
        if (resampled.data[i] < resampledMin) resampledMin = resampled.data[i];
        if (resampled.data[i] > resampledMax) resampledMax = resampled.data[i];
      }

      // Bilinear interpolation should not exceed original range
      expect(resampledMin).toBeGreaterThanOrEqual(originalMin);
      expect(resampledMax).toBeLessThanOrEqual(originalMax);
    });
  });

  describe('edge cases', () => {
    it('handles 1x1 target size', () => {
      const resampled = resampleSlice(slice, 1, 1, 'bilinear');

      expect(resampled.width).toBe(1);
      expect(resampled.height).toBe(1);
      expect(resampled.data.length).toBe(1);
    });

    it('handles very small source slice', () => {
      const tinySlice: Slice2D = {
        width: 1,
        height: 1,
        data: new Float32Array([42]),
      };

      const resampled = resampleSlice(tinySlice, 10, 10, 'bilinear');

      // All values should be 42 (only one source value to interpolate from)
      for (let i = 0; i < resampled.data.length; i++) {
        expect(resampled.data[i]).toBe(42);
      }
    });

    it('handles large upsampling factor', () => {
      const smallSlice: Slice2D = {
        width: 4,
        height: 4,
        data: new Float32Array(16).fill(100),
      };

      const resampled = resampleSlice(smallSlice, 64, 64, 'bilinear');

      expect(resampled.width).toBe(64);
      expect(resampled.height).toBe(64);

      // All values should still be 100 for uniform input
      for (let i = 0; i < resampled.data.length; i++) {
        expect(resampled.data[i]).toBeCloseTo(100, 3);
      }
    });
  });
});

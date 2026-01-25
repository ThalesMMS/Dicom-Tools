import { describe, it, expect } from 'vitest';
import {
  applyWindowLevel,
  windowLevelSlice,
  extractAxialSlice,
  Slice2D,
} from '../src/volumeUtils';
import { VOI_PRESETS, applyVoiPreset } from '../src/presets';
import { loadSampleSeriesVolume } from './helpers/sampleSeriesVolume';

describe('Window/Level (VOI) manipulation', () => {
  describe('applyWindowLevel', () => {
    it('maps values below window to 0', () => {
      const center = 40;
      const width = 400;
      const lower = center - width / 2; // -160

      expect(applyWindowLevel(-200, center, width)).toBe(0);
      expect(applyWindowLevel(-161, center, width)).toBe(0);
      expect(applyWindowLevel(lower, center, width)).toBe(0);
    });

    it('maps values above window to 255', () => {
      const center = 40;
      const width = 400;
      const upper = center + width / 2; // 240

      expect(applyWindowLevel(300, center, width)).toBe(255);
      expect(applyWindowLevel(241, center, width)).toBe(255);
      expect(applyWindowLevel(upper, center, width)).toBe(255);
    });

    it('maps center value to 128 (midpoint)', () => {
      const center = 40;
      const width = 400;

      const result = applyWindowLevel(center, center, width);
      expect(result).toBeCloseTo(128, 0);
    });

    it('linearly interpolates values within window', () => {
      const center = 0;
      const width = 256;
      // lower = -128, upper = 128

      expect(applyWindowLevel(-128, center, width)).toBe(0);
      expect(applyWindowLevel(0, center, width)).toBe(128);
      expect(applyWindowLevel(128, center, width)).toBe(255);

      // 25% through the window
      const quarterPoint = -128 + 256 * 0.25;
      expect(applyWindowLevel(quarterPoint, center, width)).toBeCloseTo(64, 0);
    });
  });

  describe('windowLevelSlice', () => {
    it('transforms a slice to 8-bit using window/level', () => {
      const volume = loadSampleSeriesVolume();
      const midSlice = Math.floor(volume.slices / 2);
      const slice = extractAxialSlice(volume, midSlice);

      const result = windowLevelSlice(slice, 40, 400);

      expect(result.width).toBe(slice.width);
      expect(result.height).toBe(slice.height);
      expect(result.data).toBeInstanceOf(Uint8Array);
      expect(result.data.length).toBe(slice.data.length);
    });

    it('output values are clamped to 0-255 range', () => {
      const volume = loadSampleSeriesVolume();
      const midSlice = Math.floor(volume.slices / 2);
      const slice = extractAxialSlice(volume, midSlice);

      const result = windowLevelSlice(slice, 40, 400);

      for (let i = 0; i < result.data.length; i++) {
        expect(result.data[i]).toBeGreaterThanOrEqual(0);
        expect(result.data[i]).toBeLessThanOrEqual(255);
      }
    });

    it('narrow window increases contrast', () => {
      const volume = loadSampleSeriesVolume();
      const slice = extractAxialSlice(volume, Math.floor(volume.slices / 2));

      const wideWindow = windowLevelSlice(slice, 40, 4000);
      const narrowWindow = windowLevelSlice(slice, 40, 100);

      // Count extreme values (0 and 255)
      let wideExtremes = 0;
      let narrowExtremes = 0;

      for (let i = 0; i < slice.data.length; i++) {
        if (wideWindow.data[i] === 0 || wideWindow.data[i] === 255) wideExtremes++;
        if (narrowWindow.data[i] === 0 || narrowWindow.data[i] === 255) narrowExtremes++;
      }

      // Narrow window should produce more extreme values (higher contrast)
      expect(narrowExtremes).toBeGreaterThan(wideExtremes);
    });
  });

  describe('VOI presets', () => {
    it('soft tissue preset has expected values', () => {
      expect(VOI_PRESETS.soft.center).toBe(40);
      expect(VOI_PRESETS.soft.width).toBe(400);
    });

    it('bone preset has expected values', () => {
      expect(VOI_PRESETS.bone.center).toBe(300);
      expect(VOI_PRESETS.bone.width).toBe(1500);
    });

    it('lung preset has expected values', () => {
      expect(VOI_PRESETS.lung.center).toBe(-600);
      expect(VOI_PRESETS.lung.width).toBe(1600);
    });

    it('applyVoiPreset calls setVOI with correct values for string preset', () => {
      let capturedCenter = 0;
      let capturedWidth = 0;

      const mockViewer = {
        setVOI: (center: number, width: number) => {
          capturedCenter = center;
          capturedWidth = width;
        },
      };

      const result = applyVoiPreset(mockViewer, 'bone');

      expect(capturedCenter).toBe(300);
      expect(capturedWidth).toBe(1500);
      expect(result).toEqual({ center: 300, width: 1500 });
    });

    it('applyVoiPreset accepts custom preset object', () => {
      let capturedCenter = 0;
      let capturedWidth = 0;

      const mockViewer = {
        setVOI: (center: number, width: number) => {
          capturedCenter = center;
          capturedWidth = width;
        },
      };

      const customPreset = { center: 100, width: 500 };
      const result = applyVoiPreset(mockViewer, customPreset);

      expect(capturedCenter).toBe(100);
      expect(capturedWidth).toBe(500);
      expect(result).toEqual(customPreset);
    });
  });

  describe('clinical window/level scenarios', () => {
    const volume = loadSampleSeriesVolume();
    const slice = extractAxialSlice(volume, Math.floor(volume.slices / 2));

    it('soft tissue window optimizes visualization of organs', () => {
      const result = windowLevelSlice(slice, VOI_PRESETS.soft.center, VOI_PRESETS.soft.width);

      // Soft tissue window should have good distribution in middle range
      let midRangeCount = 0;
      for (let i = 0; i < result.data.length; i++) {
        if (result.data[i] >= 64 && result.data[i] <= 192) {
          midRangeCount++;
        }
      }

      // Should have significant pixels in mid-range for soft tissue
      expect(midRangeCount).toBeGreaterThan(slice.data.length * 0.1);
    });

    it('bone window shows high-density structures', () => {
      const result = windowLevelSlice(slice, VOI_PRESETS.bone.center, VOI_PRESETS.bone.width);

      // Bone window with wide width should have more gradation
      let nonExtremeCount = 0;
      for (let i = 0; i < result.data.length; i++) {
        if (result.data[i] > 0 && result.data[i] < 255) {
          nonExtremeCount++;
        }
      }

      expect(nonExtremeCount).toBeGreaterThan(0);
    });

    it('lung window optimizes visualization of air-filled structures', () => {
      const result = windowLevelSlice(slice, VOI_PRESETS.lung.center, VOI_PRESETS.lung.width);

      // Lung window centered at -600 should show lung parenchyma
      // Background air at -1000 should map to lower values
      let darkCount = 0;
      for (let i = 0; i < result.data.length; i++) {
        if (result.data[i] < 64) darkCount++;
      }

      // Should have some dark pixels representing air
      expect(darkCount).toBeGreaterThan(0);
    });
  });

  describe('synthetic slice window/level', () => {
    it('correctly applies window/level to known values', () => {
      const syntheticSlice: Slice2D = {
        width: 5,
        height: 1,
        data: new Float32Array([-200, -160, 40, 240, 300]),
      };

      const result = windowLevelSlice(syntheticSlice, 40, 400);

      expect(result.data[0]).toBe(0); // -200 is below window
      expect(result.data[1]).toBe(0); // -160 is at window lower bound
      expect(result.data[2]).toBeCloseTo(128, 0); // 40 is at center
      expect(result.data[3]).toBe(255); // 240 is at window upper bound
      expect(result.data[4]).toBe(255); // 300 is above window
    });
  });
});

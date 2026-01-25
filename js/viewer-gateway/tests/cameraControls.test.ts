import { describe, it, expect } from 'vitest';
import {
  computeZoomedCrop,
  cropSlice,
  extractAxialSlice,
  CameraState,
  Slice2D,
} from '../src/volumeUtils';
import { loadSampleSeriesVolume } from './helpers/sampleSeriesVolume';

describe('Camera controls and viewport manipulation', () => {
  const volume = loadSampleSeriesVolume();
  const slice = extractAxialSlice(volume, Math.floor(volume.slices / 2));

  describe('computeZoomedCrop', () => {
    it('returns full view dimensions at zoom=1', () => {
      const camera: CameraState = { zoom: 1, panX: 0, panY: 0, rotation: 0 };
      const crop = computeZoomedCrop(slice, camera);

      expect(crop.viewWidth).toBe(slice.width);
      expect(crop.viewHeight).toBe(slice.height);
      expect(crop.startCol).toBe(0);
      expect(crop.startRow).toBe(0);
    });

    it('reduces view dimensions at zoom=2', () => {
      const camera: CameraState = { zoom: 2, panX: 0, panY: 0, rotation: 0 };
      const crop = computeZoomedCrop(slice, camera);

      expect(crop.viewWidth).toBe(Math.round(slice.width / 2));
      expect(crop.viewHeight).toBe(Math.round(slice.height / 2));
    });

    it('centers crop at zoom=2 with no pan', () => {
      const camera: CameraState = { zoom: 2, panX: 0, panY: 0, rotation: 0 };
      const crop = computeZoomedCrop(slice, camera);

      // Crop should be centered
      const expectedStartCol = Math.round(slice.width / 2 - crop.viewWidth / 2);
      const expectedStartRow = Math.round(slice.height / 2 - crop.viewHeight / 2);

      expect(crop.startCol).toBe(expectedStartCol);
      expect(crop.startRow).toBe(expectedStartRow);
    });

    it('shifts crop region with positive pan', () => {
      const camera: CameraState = { zoom: 2, panX: 50, panY: 30, rotation: 0 };
      const noPanCamera: CameraState = { zoom: 2, panX: 0, panY: 0, rotation: 0 };

      const croppedWithPan = computeZoomedCrop(slice, camera);
      const croppedNoPan = computeZoomedCrop(slice, noPanCamera);

      // Positive pan should shift the view
      expect(croppedWithPan.startCol).toBeGreaterThan(croppedNoPan.startCol);
      expect(croppedWithPan.startRow).toBeGreaterThan(croppedNoPan.startRow);
    });

    it('shifts crop region with negative pan', () => {
      const camera: CameraState = { zoom: 2, panX: -50, panY: -30, rotation: 0 };
      const noPanCamera: CameraState = { zoom: 2, panX: 0, panY: 0, rotation: 0 };

      const croppedWithPan = computeZoomedCrop(slice, camera);
      const croppedNoPan = computeZoomedCrop(slice, noPanCamera);

      expect(croppedWithPan.startCol).toBeLessThan(croppedNoPan.startCol);
      expect(croppedWithPan.startRow).toBeLessThan(croppedNoPan.startRow);
    });

    it('clamps start position to non-negative', () => {
      const camera: CameraState = { zoom: 2, panX: -10000, panY: -10000, rotation: 0 };
      const crop = computeZoomedCrop(slice, camera);

      expect(crop.startCol).toBeGreaterThanOrEqual(0);
      expect(crop.startRow).toBeGreaterThanOrEqual(0);
    });

    it('increases zoom proportionally reduces view size', () => {
      const zoom2: CameraState = { zoom: 2, panX: 0, panY: 0, rotation: 0 };
      const zoom4: CameraState = { zoom: 4, panX: 0, panY: 0, rotation: 0 };

      const crop2 = computeZoomedCrop(slice, zoom2);
      const crop4 = computeZoomedCrop(slice, zoom4);

      expect(crop4.viewWidth).toBe(Math.round(crop2.viewWidth / 2));
      expect(crop4.viewHeight).toBe(Math.round(crop2.viewHeight / 2));
    });
  });

  describe('cropSlice integration with zoom', () => {
    it('extracts zoomed region using computed crop parameters', () => {
      const camera: CameraState = { zoom: 2, panX: 0, panY: 0, rotation: 0 };
      const { startRow, startCol, viewWidth, viewHeight } = computeZoomedCrop(slice, camera);

      const croppedSlice = cropSlice(slice, startRow, startCol, viewHeight, viewWidth);

      expect(croppedSlice.width).toBe(viewWidth);
      expect(croppedSlice.height).toBe(viewHeight);
    });

    it('cropped center matches original center at zoom=2', () => {
      const camera: CameraState = { zoom: 2, panX: 0, panY: 0, rotation: 0 };
      const { startRow, startCol, viewWidth, viewHeight } = computeZoomedCrop(slice, camera);

      const croppedSlice = cropSlice(slice, startRow, startCol, viewHeight, viewWidth);

      // Center of cropped slice should match center of original
      const originalCenterRow = Math.floor(slice.height / 2);
      const originalCenterCol = Math.floor(slice.width / 2);
      const originalCenterValue = slice.data[originalCenterRow * slice.width + originalCenterCol];

      const croppedCenterRow = Math.floor(croppedSlice.height / 2);
      const croppedCenterCol = Math.floor(croppedSlice.width / 2);
      const croppedCenterValue = croppedSlice.data[croppedCenterRow * croppedSlice.width + croppedCenterCol];

      expect(croppedCenterValue).toBeCloseTo(originalCenterValue, 3);
    });
  });

  describe('zoom levels for clinical use', () => {
    it('supports common clinical zoom levels (1x, 2x, 4x, 8x)', () => {
      const zoomLevels = [1, 2, 4, 8];

      for (const zoom of zoomLevels) {
        const camera: CameraState = { zoom, panX: 0, panY: 0, rotation: 0 };
        const crop = computeZoomedCrop(slice, camera);

        expect(crop.viewWidth).toBe(Math.round(slice.width / zoom));
        expect(crop.viewHeight).toBe(Math.round(slice.height / zoom));
      }
    });

    it('handles fractional zoom levels', () => {
      const camera: CameraState = { zoom: 1.5, panX: 0, panY: 0, rotation: 0 };
      const crop = computeZoomedCrop(slice, camera);

      expect(crop.viewWidth).toBe(Math.round(slice.width / 1.5));
      expect(crop.viewHeight).toBe(Math.round(slice.height / 1.5));
    });
  });

  describe('synthetic slice camera operations', () => {
    it('correctly crops a small synthetic slice', () => {
      const syntheticSlice: Slice2D = {
        width: 10,
        height: 10,
        data: new Float32Array(100),
      };

      // Fill with position-based values for verification
      for (let r = 0; r < 10; r++) {
        for (let c = 0; c < 10; c++) {
          syntheticSlice.data[r * 10 + c] = r * 10 + c;
        }
      }

      const camera: CameraState = { zoom: 2, panX: 0, panY: 0, rotation: 0 };
      const { startRow, startCol, viewWidth, viewHeight } = computeZoomedCrop(syntheticSlice, camera);

      const cropped = cropSlice(syntheticSlice, startRow, startCol, viewHeight, viewWidth);

      expect(cropped.width).toBe(5);
      expect(cropped.height).toBe(5);

      // Top-left of cropped should be from center region of original
      const expectedTopLeftValue = syntheticSlice.data[startRow * 10 + startCol];
      expect(cropped.data[0]).toBe(expectedTopLeftValue);
    });

    it('pan moves visible region correctly', () => {
      const syntheticSlice: Slice2D = {
        width: 20,
        height: 20,
        data: new Float32Array(400),
      };

      // Fill with unique values
      for (let i = 0; i < 400; i++) {
        syntheticSlice.data[i] = i;
      }

      // Pan to upper-left quadrant
      const camera: CameraState = { zoom: 2, panX: -5, panY: -5, rotation: 0 };
      const { startRow, startCol, viewWidth, viewHeight } = computeZoomedCrop(syntheticSlice, camera);

      expect(startCol).toBeLessThan(5);
      expect(startRow).toBeLessThan(5);

      const cropped = cropSlice(syntheticSlice, startRow, startCol, viewHeight, viewWidth);

      // First element should be from upper-left region
      expect(cropped.data[0]).toBe(syntheticSlice.data[startRow * 20 + startCol]);
    });
  });
});

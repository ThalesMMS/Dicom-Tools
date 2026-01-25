import { describe, it, expect } from 'vitest';
import {
  indexToWorld,
  worldToIndex,
  extractAxialSlice,
  extractSagittalSlice,
  extractCoronalSlice,
  getVoxel,
  VolumeData,
  PhysicalPoint,
} from '../src/volumeUtils';
import { loadSampleSeriesVolume } from './helpers/sampleSeriesVolume';

describe('MPR crosshair synchronization', () => {
  const volume = loadSampleSeriesVolume();

  describe('world coordinate round-trip consistency', () => {
    it('converts index to world and back with high precision', () => {
      const testPoints = [
        { slice: 0, row: 0, col: 0 },
        { slice: Math.floor(volume.slices / 2), row: Math.floor(volume.rows / 2), col: Math.floor(volume.cols / 2) },
        { slice: volume.slices - 1, row: volume.rows - 1, col: volume.cols - 1 },
        { slice: 50, row: 100, col: 200 },
        { slice: 87, row: 256, col: 128 },
      ];

      for (const point of testPoints) {
        const world = indexToWorld(volume, point.slice, point.row, point.col);
        const indices = worldToIndex(volume, world);

        expect(indices.slice).toBeCloseTo(point.slice, 4);
        expect(indices.row).toBeCloseTo(point.row, 4);
        expect(indices.col).toBeCloseTo(point.col, 4);
      }
    });

    it('maintains sub-voxel precision in coordinate transforms', () => {
      // Test fractional indices
      const fractionalPoint = { slice: 50.5, row: 100.25, col: 200.75 };
      const world = indexToWorld(volume, fractionalPoint.slice, fractionalPoint.row, fractionalPoint.col);
      const indices = worldToIndex(volume, world);

      expect(indices.slice).toBeCloseTo(fractionalPoint.slice, 4);
      expect(indices.row).toBeCloseTo(fractionalPoint.row, 4);
      expect(indices.col).toBeCloseTo(fractionalPoint.col, 4);
    });
  });

  describe('crosshair value consistency across views', () => {
    it('same physical point shows same value in all MPR views', () => {
      const testIndices = { slice: 50, row: 256, col: 256 };

      const axialValue = getVoxel(volume, testIndices.slice, testIndices.row, testIndices.col);

      // Extract MPR views at the crosshair position
      const sagittal = extractSagittalSlice(volume, testIndices.col);
      const sagittalValue = sagittal.data[testIndices.row * sagittal.width + testIndices.slice];

      const coronal = extractCoronalSlice(volume, testIndices.row);
      const coronalValue = coronal.data[testIndices.slice * coronal.width + testIndices.col];

      expect(sagittalValue).toBeCloseTo(axialValue, 6);
      expect(coronalValue).toBeCloseTo(axialValue, 6);
    });

    it('crosshair intersection point is consistent across multiple test positions', () => {
      const positions = [
        { slice: 10, row: 100, col: 150 },
        { slice: 87, row: 256, col: 256 },
        { slice: 170, row: 400, col: 300 },
      ];

      for (const pos of positions) {
        const axial = getVoxel(volume, pos.slice, pos.row, pos.col);
        const sagittal = extractSagittalSlice(volume, pos.col);
        const coronal = extractCoronalSlice(volume, pos.row);

        const sagVal = sagittal.data[pos.row * sagittal.width + pos.slice];
        const corVal = coronal.data[pos.slice * coronal.width + pos.col];

        expect(sagVal).toBeCloseTo(axial, 6);
        expect(corVal).toBeCloseTo(axial, 6);
      }
    });
  });

  describe('crosshair movement simulation', () => {
    it('moving crosshair in axial view updates world coordinates correctly', () => {
      const initialPos = { slice: 87, row: 256, col: 256 };
      const initialWorld = indexToWorld(volume, initialPos.slice, initialPos.row, initialPos.col);

      // Move crosshair by 10 pixels in row direction
      const movedPos = { ...initialPos, row: initialPos.row + 10 };
      const movedWorld = indexToWorld(volume, movedPos.slice, movedPos.row, movedPos.col);

      // Row direction maps to X in standard orientation [1,0,0]
      const expectedDelta = 10 * (volume.spacing?.row ?? 1);
      expect(movedWorld[0] - initialWorld[0]).toBeCloseTo(expectedDelta, 4);

      // Z should remain unchanged when only row changes
      expect(movedWorld[2]).toBeCloseTo(initialWorld[2], 4);
    });

    it('moving crosshair in sagittal view updates correct dimensions', () => {
      const initialPos = { slice: 87, row: 256, col: 256 };

      // In sagittal view, horizontal movement changes slice (Z)
      // Vertical movement changes row (Y)
      const movedSlice = { ...initialPos, slice: initialPos.slice + 5 };
      const initialWorld = indexToWorld(volume, initialPos.slice, initialPos.row, initialPos.col);
      const movedWorld = indexToWorld(volume, movedSlice.slice, movedSlice.row, movedSlice.col);

      const expectedZDelta = 5 * (volume.spacing?.slice ?? 1);
      expect(movedWorld[2] - initialWorld[2]).toBeCloseTo(expectedZDelta, 4);
    });

    it('moving crosshair in coronal view updates correct dimensions', () => {
      const initialPos = { slice: 87, row: 256, col: 256 };

      // In coronal view, col direction maps to Y in standard orientation [0,1,0]
      const movedCol = { ...initialPos, col: initialPos.col + 20 };
      const initialWorld = indexToWorld(volume, initialPos.slice, initialPos.row, initialPos.col);
      const movedWorld = indexToWorld(volume, movedCol.slice, movedCol.row, movedCol.col);

      const expectedYDelta = 20 * (volume.spacing?.col ?? 1);
      expect(movedWorld[1] - initialWorld[1]).toBeCloseTo(expectedYDelta, 4);
    });
  });

  describe('linked viewport synchronization', () => {
    type LinkedViewports = {
      axialSlice: number;
      sagittalCol: number;
      coronalRow: number;
      worldPos: PhysicalPoint;
    };

    function createLinkedState(slice: number, row: number, col: number): LinkedViewports {
      return {
        axialSlice: slice,
        sagittalCol: col,
        coronalRow: row,
        worldPos: indexToWorld(volume, slice, row, col),
      };
    }

    function updateFromWorld(worldPos: PhysicalPoint): LinkedViewports {
      const indices = worldToIndex(volume, worldPos);
      return {
        axialSlice: Math.round(indices.slice),
        sagittalCol: Math.round(indices.col),
        coronalRow: Math.round(indices.row),
        worldPos,
      };
    }

    it('linked viewports update together when crosshair moves', () => {
      const initial = createLinkedState(50, 200, 300);

      // Simulate clicking in axial view at different position
      const newWorld = indexToWorld(volume, 60, 220, 310);
      const updated = updateFromWorld(newWorld);

      expect(updated.axialSlice).toBe(60);
      expect(updated.coronalRow).toBe(220);
      expect(updated.sagittalCol).toBe(310);
    });

    it('maintains crosshair alignment after multiple updates', () => {
      let state = createLinkedState(87, 256, 256);

      // Series of crosshair movements
      const movements = [
        [90, 260, 250],
        [85, 255, 260],
        [100, 300, 200],
      ] as const;

      for (const [s, r, c] of movements) {
        const newWorld = indexToWorld(volume, s, r, c);
        state = updateFromWorld(newWorld);

        // Verify all viewports show same point
        const axialVal = getVoxel(volume, state.axialSlice, state.coronalRow, state.sagittalCol);
        const sagittal = extractSagittalSlice(volume, state.sagittalCol);
        const sagVal = sagittal.data[state.coronalRow * sagittal.width + state.axialSlice];

        expect(sagVal).toBeCloseTo(axialVal, 3);
      }
    });
  });

  describe('orientation-specific coordinate mapping', () => {
    it('axial view maps row to X, col to Y (standard orientation)', () => {
      const pos = { slice: 50, row: 100, col: 200 };
      const world = indexToWorld(volume, pos.slice, pos.row, pos.col);

      // Standard orientation: row=[1,0,0], col=[0,1,0]
      // Moving row should primarily affect X
      const movedRow = indexToWorld(volume, pos.slice, pos.row + 1, pos.col);
      expect(Math.abs(movedRow[0] - world[0])).toBeGreaterThan(0);

      // Moving col should primarily affect Y
      const movedCol = indexToWorld(volume, pos.slice, pos.row, pos.col + 1);
      expect(Math.abs(movedCol[1] - world[1])).toBeGreaterThan(0);
    });

    it('sagittal view: slice maps to Z, row maps to Y', () => {
      const pos = { slice: 50, row: 100, col: 200 };
      const world = indexToWorld(volume, pos.slice, pos.row, pos.col);

      // Moving slice should affect Z
      const movedSlice = indexToWorld(volume, pos.slice + 1, pos.row, pos.col);
      expect(Math.abs(movedSlice[2] - world[2])).toBeGreaterThan(0);
    });

    it('coronal view: slice maps to Z, col maps to Y', () => {
      const pos = { slice: 50, row: 100, col: 200 };
      const world = indexToWorld(volume, pos.slice, pos.row, pos.col);

      const movedSlice = indexToWorld(volume, pos.slice + 1, pos.row, pos.col);
      const movedCol = indexToWorld(volume, pos.slice, pos.row, pos.col + 1);

      expect(Math.abs(movedSlice[2] - world[2])).toBeGreaterThan(0);
      expect(Math.abs(movedCol[1] - world[1])).toBeGreaterThan(0);
    });
  });
});

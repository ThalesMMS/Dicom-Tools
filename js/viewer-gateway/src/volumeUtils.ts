export type PhysicalPoint = [number, number, number];

export type Orientation = {
  row: PhysicalPoint;
  col: PhysicalPoint;
  slice?: PhysicalPoint;
};

export type Spacing = {
  row: number;
  col: number;
  slice: number;
};

export type VolumeData = {
  rows: number;
  cols: number;
  slices: number;
  voxelData: Float32Array;
  spacing?: Spacing;
  origin?: PhysicalPoint;
  orientation?: Orientation;
};

export type Slice2D<TArray extends Float32Array | Uint8Array = Float32Array> = {
  width: number;
  height: number;
  data: TArray;
};

export function voxelIndex(volume: VolumeData, sliceIndex: number, row: number, col: number) {
  if (sliceIndex < 0 || sliceIndex >= volume.slices) throw new Error('slice index out of range');
  if (row < 0 || row >= volume.rows) throw new Error('row out of range');
  if (col < 0 || col >= volume.cols) throw new Error('column out of range');
  return sliceIndex * volume.rows * volume.cols + row * volume.cols + col;
}

export function getVoxel(volume: VolumeData, sliceIndex: number, row: number, col: number) {
  return volume.voxelData[voxelIndex(volume, sliceIndex, row, col)];
}

export function extractAxialSlice(volume: VolumeData, sliceIndex: number): Slice2D {
  const { rows, cols } = volume;
  const offset = voxelIndex(volume, sliceIndex, 0, 0);
  const data = volume.voxelData.subarray(offset, offset + rows * cols);
  return { width: cols, height: rows, data };
}

export function extractSagittalSlice(volume: VolumeData, colIndex: number): Slice2D {
  const { rows, cols, slices, voxelData } = volume;
  if (colIndex < 0 || colIndex >= cols) throw new Error('column out of range');
  const data = new Float32Array(rows * slices);
  for (let s = 0; s < slices; s++) {
    const sliceOffset = s * rows * cols;
    for (let r = 0; r < rows; r++) {
      const srcIdx = sliceOffset + r * cols + colIndex;
      const dstIdx = r * slices + s; // width=slices, height=rows
      data[dstIdx] = voxelData[srcIdx];
    }
  }
  return { width: slices, height: rows, data };
}

export function extractCoronalSlice(volume: VolumeData, rowIndex: number): Slice2D {
  const { rows, cols, slices, voxelData } = volume;
  if (rowIndex < 0 || rowIndex >= rows) throw new Error('row out of range');
  const data = new Float32Array(slices * cols);
  for (let s = 0; s < slices; s++) {
    const sliceOffset = s * rows * cols;
    for (let c = 0; c < cols; c++) {
      const srcIdx = sliceOffset + rowIndex * cols + c;
      const dstIdx = s * cols + c; // width=cols, height=slices
      data[dstIdx] = voxelData[srcIdx];
    }
  }
  return { width: cols, height: slices, data };
}

export function computeMIP(volume: VolumeData): Slice2D {
  const { rows, cols, slices, voxelData } = volume;
  const data = new Float32Array(rows * cols);
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      let max = -Infinity;
      for (let s = 0; s < slices; s++) {
        const value = voxelData[s * rows * cols + r * cols + c];
        if (value > max) max = value;
      }
      data[r * cols + c] = max;
    }
  }
  return { width: cols, height: rows, data };
}

function crossProduct(a: PhysicalPoint, b: PhysicalPoint): PhysicalPoint {
  return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
}

function normalize(vec: PhysicalPoint): PhysicalPoint {
  const len = Math.sqrt(vec[0] * vec[0] + vec[1] * vec[1] + vec[2] * vec[2]) || 1;
  return [vec[0] / len, vec[1] / len, vec[2] / len];
}

function resolveSliceDirection(orientation?: Orientation): PhysicalPoint {
  if (orientation?.slice) return orientation.slice;
  if (orientation?.row && orientation?.col) return crossProduct(orientation.row, orientation.col);
  return [0, 0, 1];
}

export function indexToWorld(volume: VolumeData, sliceIndex: number, row: number, col: number): PhysicalPoint {
  const spacing = volume.spacing || { row: 1, col: 1, slice: 1 };
  const origin = volume.origin || [0, 0, 0];
  const orientation = volume.orientation || { row: [1, 0, 0], col: [0, 1, 0] };
  const rowDir = normalize(orientation.row);
  const colDir = normalize(orientation.col);
  const sliceDir = normalize(resolveSliceDirection(orientation));

  return [
    origin[0] + rowDir[0] * row * spacing.row + colDir[0] * col * spacing.col + sliceDir[0] * sliceIndex * spacing.slice,
    origin[1] + rowDir[1] * row * spacing.row + colDir[1] * col * spacing.col + sliceDir[1] * sliceIndex * spacing.slice,
    origin[2] + rowDir[2] * row * spacing.row + colDir[2] * col * spacing.col + sliceDir[2] * sliceIndex * spacing.slice,
  ];
}

export function worldToIndex(volume: VolumeData, world: PhysicalPoint) {
  const spacing = volume.spacing || { row: 1, col: 1, slice: 1 };
  const origin = volume.origin || [0, 0, 0];
  const orientation = volume.orientation || { row: [1, 0, 0], col: [0, 1, 0] };
  const rowDir = normalize(orientation.row);
  const colDir = normalize(orientation.col);
  const sliceDir = normalize(resolveSliceDirection(orientation));

  const delta: PhysicalPoint = [world[0] - origin[0], world[1] - origin[1], world[2] - origin[2]];
  const rowIndex = (delta[0] * rowDir[0] + delta[1] * rowDir[1] + delta[2] * rowDir[2]) / spacing.row;
  const colIndex = (delta[0] * colDir[0] + delta[1] * colDir[1] + delta[2] * colDir[2]) / spacing.col;
  const sliceIndex = (delta[0] * sliceDir[0] + delta[1] * sliceDir[1] + delta[2] * sliceDir[2]) / spacing.slice;

  return { row: rowIndex, col: colIndex, slice: sliceIndex };
}

export type RoiStats = {
  count: number;
  mean: number;
  std: number;
  min: number;
  max: number;
  area: number;
};

export function cropSlice(slice: Slice2D, rowStart: number, colStart: number, height: number, width: number): Slice2D {
  const data = new Float32Array(width * height);
  for (let r = 0; r < height; r++) {
    for (let c = 0; c < width; c++) {
      const src = (rowStart + r) * slice.width + (colStart + c);
      const dst = r * width + c;
      data[dst] = slice.data[src];
    }
  }
  return { width, height, data };
}

export function computeRoiStats(slice: Slice2D, spacing?: Pick<Spacing, 'row' | 'col'>): RoiStats {
  const pixelCount = slice.data.length;
  if (pixelCount === 0) {
    return { count: 0, mean: 0, std: 0, min: 0, max: 0, area: 0 };
  }

  let min = slice.data[0];
  let max = slice.data[0];
  let sum = 0;
  let sumSq = 0;

  for (let i = 0; i < pixelCount; i++) {
    const value = slice.data[i];
    sum += value;
    sumSq += value * value;
    if (value < min) min = value;
    if (value > max) max = value;
  }

  const mean = sum / pixelCount;
  const variance = sumSq / pixelCount - mean * mean;
  const std = Math.sqrt(Math.max(variance, 0));
  const pixelArea = (spacing?.row || 1) * (spacing?.col || 1);

  return { count: pixelCount, mean, std, min, max, area: pixelArea * pixelCount };
}

export type LabelVolume = {
  rows: number;
  cols: number;
  slices: number;
  labels: Uint8Array | Uint16Array | Uint32Array;
};

export function extractLabelSlice(volume: LabelVolume, orientation: 'axial' | 'sagittal' | 'coronal', index: number): Slice2D<Uint8Array> {
  const rows = volume.rows;
  const cols = volume.cols;
  const slices = volume.slices;
  const src = volume.labels;

  if (orientation === 'axial') {
    if (index < 0 || index >= slices) throw new Error('slice index out of range');
    const offset = index * rows * cols;
    const data = src.subarray(offset, offset + rows * cols);
    return { width: cols, height: rows, data: Uint8Array.from(data) };
  }

  if (orientation === 'sagittal') {
    if (index < 0 || index >= cols) throw new Error('column out of range');
    const data = new Uint8Array(rows * slices);
    for (let s = 0; s < slices; s++) {
      const sliceOffset = s * rows * cols;
      for (let r = 0; r < rows; r++) {
        const srcIdx = sliceOffset + r * cols + index;
        const dstIdx = r * slices + s;
        data[dstIdx] = src[srcIdx];
      }
    }
    return { width: slices, height: rows, data };
  }

  if (index < 0 || index >= rows) throw new Error('row out of range');
  const data = new Uint8Array(slices * cols);
  for (let s = 0; s < slices; s++) {
    const sliceOffset = s * rows * cols;
    for (let c = 0; c < cols; c++) {
      const srcIdx = sliceOffset + index * cols + c;
      const dstIdx = s * cols + c;
      data[dstIdx] = src[srcIdx];
    }
  }
  return { width: cols, height: slices, data };
}

export function countLabelVoxels(labelVolume: LabelVolume) {
  const counts = new Map<number, number>();
  for (let i = 0; i < labelVolume.labels.length; i++) {
    const label = labelVolume.labels[i];
    counts.set(label, (counts.get(label) || 0) + 1);
  }
  return counts;
}

export function buildThresholdLabelMap(
  volume: VolumeData,
  thresholds: Array<{ label: number; predicate: (value: number) => boolean }>,
  targetArray: Uint8Array | Uint16Array | Uint32Array = new Uint8Array(volume.rows * volume.cols * volume.slices),
): LabelVolume {
  if (targetArray.length !== volume.voxelData.length) {
    throw new Error('target label array size does not match volume');
  }

  for (let i = 0; i < volume.voxelData.length; i++) {
    const value = volume.voxelData[i];
    const match = thresholds.find((entry) => entry.predicate(value));
    targetArray[i] = match ? (match.label as any) : 0;
  }

  return {
    rows: volume.rows,
    cols: volume.cols,
    slices: volume.slices,
    labels: targetArray,
  };
}

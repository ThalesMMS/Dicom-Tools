export type VolumeData = {
  rows: number;
  cols: number;
  slices: number;
  voxelData: Float32Array;
  spacing?: {
    row: number;
    col: number;
    slice: number;
  };
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

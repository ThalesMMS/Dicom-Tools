export type VoiPresetKey = 'soft' | 'bone' | 'lung';

export type VoiPreset = {
  center: number;
  width: number;
};

export const VOI_PRESETS: Record<VoiPresetKey, VoiPreset> = {
  soft: { center: 40, width: 400 },
  bone: { center: 300, width: 1500 },
  lung: { center: -600, width: 1600 },
};

export type ViewerWithVOI = {
  setVOI: (center: number, width: number) => void;
};

export function applyVoiPreset(viewer: ViewerWithVOI, preset: VoiPresetKey | VoiPreset) {
  const { center, width } = typeof preset === 'string' ? VOI_PRESETS[preset] : preset;
  viewer.setVOI(center, width);
  return { center, width };
}

export type ViewState = {
  slice?: number;
  voi?: VoiPreset;
  orientation?: 'axial' | 'sagittal' | 'coronal';
  mode?: 'mip' | 'volume';
  slabThickness?: number;
};

export type StackController = {
  setSlice: (index: number) => Promise<void> | void;
  setVOI: (center: number, width: number) => void;
};

export type VolumeController = {
  setOrientation: (orientation: 'axial' | 'sagittal' | 'coronal') => void;
  setBlendMode: (mode: 'mip' | 'volume') => void;
  setSlabThickness?: (value: number) => void;
};

export function restoreStackState(stack: StackController, state: ViewState) {
  if (typeof state.slice === 'number') {
    stack.setSlice(state.slice);
  }
  if (state.voi) {
    stack.setVOI(state.voi.center, state.voi.width);
  }
}

export function restoreVolumeState(volume: VolumeController, state: ViewState) {
  if (state.orientation) {
    volume.setOrientation(state.orientation);
  }
  if (state.mode) {
    volume.setBlendMode(state.mode);
  }
  if (state.slabThickness && volume.setSlabThickness) {
    volume.setSlabThickness(state.slabThickness);
  }
}

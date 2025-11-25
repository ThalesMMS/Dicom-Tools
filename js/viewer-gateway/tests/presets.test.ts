import { describe, it, expect, vi } from 'vitest';
import { VOI_PRESETS, applyVoiPreset, restoreStackState, restoreVolumeState } from '../src/presets';

describe('VOI presets and state helpers', () => {
  it('applies preset to viewer', () => {
    const setVOI = vi.fn();
    applyVoiPreset({ setVOI }, 'bone');
    expect(setVOI).toHaveBeenCalledWith(VOI_PRESETS.bone.center, VOI_PRESETS.bone.width);
  });

  it('restores stack state', () => {
    const setSlice = vi.fn();
    const setVOI = vi.fn();
    restoreStackState({ setSlice, setVOI }, { slice: 5, voi: { center: 10, width: 200 } });
    expect(setSlice).toHaveBeenCalledWith(5);
    expect(setVOI).toHaveBeenCalledWith(10, 200);
  });

  it('restores volume state', () => {
    const setOrientation = vi.fn();
    const setBlendMode = vi.fn();
    const setSlabThickness = vi.fn();
    restoreVolumeState({ setOrientation, setBlendMode, setSlabThickness }, { orientation: 'coronal', mode: 'volume', slabThickness: 15 });
    expect(setOrientation).toHaveBeenCalledWith('coronal');
    expect(setBlendMode).toHaveBeenCalledWith('volume');
    expect(setSlabThickness).toHaveBeenCalledWith(15);
  });
});

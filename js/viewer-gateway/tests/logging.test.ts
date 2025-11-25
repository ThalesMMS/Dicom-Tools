import { describe, it, expect, vi } from 'vitest';
import { reportStatus, setStatus } from '../src/logging';

describe('logging helpers', () => {
  it('sets status text and dataset', () => {
    const el = { textContent: '', dataset: {} } as any;
    setStatus(el, 'hello', 'info');
    expect(el.textContent).toBe('hello');
    expect(el.dataset.statusLevel).toBe('info');
  });

  it('logs and updates element', () => {
    const el = { textContent: '', dataset: {} } as any;
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    reportStatus(el, 'error', 'failed', new Error('boom'));
    expect(el.textContent).toBe('failed');
    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  });
});

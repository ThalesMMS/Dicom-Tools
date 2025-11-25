import { describe, it, expect, vi, beforeEach } from 'vitest';
import { loadDemoConfig } from '../src/config';

describe('config loader', () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it('returns defaults when no env is set', () => {
    const cfg = loadDemoConfig({ metaEnv: {}, processEnv: {} });
    expect(cfg.sampleBaseUrl).toBe('http://localhost:8080/sample_series');
    expect(cfg.sampleCount).toBe(174);
    expect(cfg.dicomweb).toBeUndefined();
  });

  it('reads dicomweb config from env vars', () => {
    const cfg = loadDemoConfig({
      metaEnv: {
        VITE_DICOMWEB_BASE: 'http://env-base',
        VITE_DICOMWEB_STUDY: '1.2.3',
        VITE_DICOMWEB_SERIES: '4.5.6',
        VITE_SAMPLE_BASE: 'http://other',
        VITE_SAMPLE_COUNT: '42',
        VITE_USE_CPU: 'true',
      },
    });

    expect(cfg.sampleBaseUrl).toBe('http://other');
    expect(cfg.sampleCount).toBe(42);
    expect(cfg.useCPU).toBe(true);
    expect(cfg.dicomweb?.baseUrl).toBe('http://env-base');
  });

  it('prefers global window config over env', () => {
    vi.stubGlobal('window', {
      DICOMWEB_CONFIG: {
        baseUrl: 'http://global',
        studyInstanceUID: 's',
        seriesInstanceUID: 'se',
      },
    } as any);

    const cfg = loadDemoConfig({
      metaEnv: {
        VITE_DICOMWEB_BASE: 'http://env-base',
        VITE_DICOMWEB_STUDY: '1.2.3',
        VITE_DICOMWEB_SERIES: '4.5.6',
      },
    });

    expect(cfg.dicomweb?.baseUrl).toBe('http://global');
    vi.unstubAllGlobals();
  });
});

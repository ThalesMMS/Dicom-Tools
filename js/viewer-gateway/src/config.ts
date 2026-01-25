import type { DicomWebConfig } from './dicomWeb';

export type DemoConfig = {
  sampleBaseUrl: string;
  sampleCount: number;
  useCPU?: boolean;
  dicomweb?: DicomWebConfig;
};

function readEnv(metaEnv: Record<string, any> | undefined, processEnv: Record<string, any> | undefined) {
  return {
    VITE_DICOMWEB_BASE: metaEnv?.VITE_DICOMWEB_BASE ?? processEnv?.VITE_DICOMWEB_BASE,
    VITE_DICOMWEB_STUDY: metaEnv?.VITE_DICOMWEB_STUDY ?? processEnv?.VITE_DICOMWEB_STUDY,
    VITE_DICOMWEB_SERIES: metaEnv?.VITE_DICOMWEB_SERIES ?? processEnv?.VITE_DICOMWEB_SERIES,
    VITE_SAMPLE_BASE: metaEnv?.VITE_SAMPLE_BASE ?? processEnv?.VITE_SAMPLE_BASE,
    VITE_SAMPLE_COUNT: metaEnv?.VITE_SAMPLE_COUNT ?? processEnv?.VITE_SAMPLE_COUNT,
    VITE_USE_CPU: metaEnv?.VITE_USE_CPU ?? processEnv?.VITE_USE_CPU,
  };
}

export function loadDemoConfig(opts?: { metaEnv?: Record<string, any>; processEnv?: Record<string, any> }): DemoConfig {
  const metaEnv = opts?.metaEnv ?? (typeof import.meta !== 'undefined' ? (import.meta as any).env : undefined);
  const env = readEnv(metaEnv, opts?.processEnv ?? (typeof process !== 'undefined' ? process.env : undefined));

  const sampleBaseUrl = env.VITE_SAMPLE_BASE || 'http://localhost:8080/sample_series';
  const sampleCount = Number(env.VITE_SAMPLE_COUNT) || 174;
  const useCPU = typeof env.VITE_USE_CPU === 'string' ? env.VITE_USE_CPU === 'true' : !!env.VITE_USE_CPU;

  const win = typeof window !== 'undefined' ? (window as any) : undefined;
  const globalDicom = win?.DICOMWEB_CONFIG || win?.__DICOMWEB_CONFIG__;

  let dicomweb: DicomWebConfig | undefined;
  if (globalDicom?.baseUrl && globalDicom?.studyInstanceUID && globalDicom?.seriesInstanceUID) {
    dicomweb = {
      baseUrl: globalDicom.baseUrl,
      studyInstanceUID: globalDicom.studyInstanceUID,
      seriesInstanceUID: globalDicom.seriesInstanceUID,
    };
  } else if (env.VITE_DICOMWEB_BASE && env.VITE_DICOMWEB_STUDY && env.VITE_DICOMWEB_SERIES) {
    dicomweb = {
      baseUrl: String(env.VITE_DICOMWEB_BASE),
      studyInstanceUID: String(env.VITE_DICOMWEB_STUDY),
      seriesInstanceUID: String(env.VITE_DICOMWEB_SERIES),
    };
  }

  return {
    sampleBaseUrl,
    sampleCount,
    useCPU,
    dicomweb,
  };
}

import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    port: 4173,
  },
  build: {
    target: 'esnext',
    // Avoid rollup using unsupported IIFE format with code-splitting; force ES output
    rollupOptions: {
      output: {
        format: 'es',
        inlineDynamicImports: true,
      },
    },
    commonjsOptions: {
      transformMixedEsModules: true,
    },
  },
  worker: {
    format: 'es',
    rollupOptions: {
      output: {
        inlineDynamicImports: true,
      },
    },
  },
});

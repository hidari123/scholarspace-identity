import { defineConfig } from 'tsup';

export default defineConfig({
  entry: { index: 'src/identity-ui/index.ts' },
  format: ['esm'],
  dts: true,
  sourcemap: true,
  clean: true,
  treeshake: true,
  external: [
    'react',
    'react-dom',
    // ⚠️ @scholarspace/ui 是 peer —— 不打进产物
    '@scholarspace/ui',
  ],
});

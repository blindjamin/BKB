import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  site: 'https://www.bkb.cl',
  output: 'static',
  server: {
    port: 3000,
    host: true
  }
});

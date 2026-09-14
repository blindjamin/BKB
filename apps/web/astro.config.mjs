import { defineConfig } from 'astro/config';

const isGitHubPages = process.env.GITHUB_PAGES === 'true';

// https://astro.build/config
export default defineConfig({
  site: isGitHubPages ? 'https://blindjamin.github.io' : 'https://www.bkb.cl',
  base: isGitHubPages ? '/BKB' : '/',
  output: 'static',
  server: {
    port: 3000,
    host: true
  }
});

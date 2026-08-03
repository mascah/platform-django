// @ts-check
import react from '@astrojs/react';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'astro/config';
import path from 'path';

// https://astro.build/config
export default defineConfig({
  integrations: [react()],
  output: 'static',
  outDir: './dist',
  build: {
    assets: 'assets',
  },
  base: '/static/',
  vite: {
    plugins: [tailwindcss()],
    // Project identity is data, not a rename, so the display name reaches the
    // built page as an env var. It comes from the repo-root .env locally and
    // from the process environment on a deploy; PROJECT_ only ever matches the
    // slug and the display name, neither of which is a secret.
    envDir: path.resolve(import.meta.dirname, '../..'),
    envPrefix: ['VITE_', 'PUBLIC_', 'PROJECT_'],
    resolve: {
      alias: {
        '@': path.resolve('./src'),
      },
    },
    server: {
      proxy: {
        '/ph/static': {
          target: 'https://us-assets.i.posthog.com',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/ph/, ''),
        },
        '/ph': {
          target: 'https://us.i.posthog.com',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/ph/, ''),
        },
      },
    },
  },
  server: {
    port: 5174,
  },
});

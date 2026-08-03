import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Project identity is data, not a rename, so the display name reaches the
  // bundle as an env var. It comes from the repo-root .env locally and from the
  // process environment on a deploy; PROJECT_ only ever matches the slug and
  // the display name, neither of which is a secret.
  envDir: path.resolve(__dirname, '../..'),
  envPrefix: ['VITE_', 'PROJECT_'],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: parseInt(process.env.VITE_PORT || '5173'),
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
  root: path.resolve('src'),
  base: '/static/platform_django',
  build: {
    manifest: 'manifest.json',
    outDir: path.resolve(path.join('dist', 'platform_django')),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: path.resolve('src/main.tsx'),
      },
    },
  },
});

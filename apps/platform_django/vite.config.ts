import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig, loadEnv } from 'vite';

const envDir = path.resolve(import.meta.dirname, '../..');
const envPrefix = ['VITE_', 'PROJECT_'];

// A worktree's ports live in the repo-root .env, and both sides of the dev
// setup have to agree on them: Django reads VITE_PORT to build the script tag
// pointing at this server. Django reads .env through django-environ and the
// justfile through dotenv-load, but Vite reads it into import.meta.env for the
// bundle rather than into process.env, so the config cannot see it. Reading the
// file here is what the other two sides already do. loadEnv applies a real
// environment variable over the file, so an explicit VITE_PORT still wins.
export default defineConfig(({ mode }) => ({
  plugins: [react(), tailwindcss()],
  // Project identity is data, not a rename, so the display name reaches the
  // bundle as an env var. It comes from the repo-root .env locally and from the
  // process environment on a deploy; PROJECT_ only ever matches the slug and
  // the display name, neither of which is a secret.
  envDir,
  envPrefix,
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: Number(loadEnv(mode, envDir, envPrefix).VITE_PORT) || 5173,
    // Falling back to the next free port would leave this server running
    // somewhere Django is not pointing, which reads as a blank /app/ rather
    // than as a port collision.
    strictPort: true,
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
}));

import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: parseInt(process.env.VITE_PLATFORM_DJANGO_PORT || '5173'),
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

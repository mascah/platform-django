import { sentryVitePlugin } from '@sentry/vite-plugin';
import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig, loadEnv } from 'vite';

const envDir = path.resolve(import.meta.dirname, '../..');
const envPrefix = ['VITE_', 'PROJECT_'];

const outDir = path.resolve(path.join('dist', 'platform_django'));

// Source maps are what turn a stack trace off a minified bundle into one that
// names a file and a line, and uploading them needs an auth token the template
// does not ship. Read from the build environment rather than through loadEnv,
// because this is a build credential and must never reach the bundle.
//
// Unset, the plugin is absent altogether and no source maps are emitted: a
// clone with no Sentry account builds exactly as it did before, with no upload
// step to fail and no .map files to collect and serve. That makes it part of
// the build's identity, so it and the two slugs below are declared in
// turbo.json's `env` — otherwise a build cached without a token gets replayed
// over one that was meant to upload.
const sentryAuthToken = process.env.SENTRY_AUTH_TOKEN;

// A worktree's ports live in the repo-root .env, and both sides of the dev
// setup have to agree on them: Django reads VITE_PORT to build the script tag
// pointing at this server. Django reads .env through django-environ and the
// justfile through dotenv-load, but Vite reads it into import.meta.env for the
// bundle rather than into process.env, so the config cannot see it. Reading the
// file here is what the other two sides already do. loadEnv applies a real
// environment variable over the file, so an explicit VITE_PORT still wins.
export default defineConfig(({ mode }) => ({
  plugins: [
    react(),
    tailwindcss(),
    ...(sentryAuthToken
      ? [
          sentryVitePlugin({
            authToken: sentryAuthToken,
            org: process.env.SENTRY_ORG,
            project: process.env.SENTRY_PROJECT,
            // The release the SDK stamps on every event comes from here — the
            // plugin injects it and detects it from Heroku's SOURCE_VERSION or
            // the git HEAD, so it is set for exactly the builds that upload.
            telemetry: false,
            sourcemaps: {
              // Deleted once uploaded. collectstatic would otherwise publish
              // them next to the bundle, which is the whole source of the
              // application on a public URL.
              filesToDeleteAfterUpload: [path.join(outDir, '**/*.map')],
            },
          }),
        ]
      : []),
  ],
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
    outDir,
    emptyOutDir: true,
    // Only worth generating when there is somewhere to upload them to.
    sourcemap: Boolean(sentryAuthToken),
    rollupOptions: {
      input: {
        main: path.resolve('src/main.tsx'),
        // The stylesheet for everything Django renders from a template, built
        // here so it shares one Tailwind and one set of tokens with the
        // application (ADR-0012). base.html reads it out of the manifest with
        // {% vite_asset_url 'django.css' %}.
        django: path.resolve('src/django.css'),
      },
    },
  },
}));

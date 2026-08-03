import { defaultPlugins, defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  // Only used when the generator is run with no `-i`. `just openapi` passes one,
  // pointing at a schema dumped by `manage.py spectacular` — which needs no
  // running server, and so no knowledge of this worktree's port.
  input: 'http://localhost:8000/api/schema',
  output: 'src/services/platform_django',
  // Django emits separate request components (COMPONENT_SPLIT_REQUEST), so the
  // read/write split already happened server-side with correct required flags.
  // Left on (its default), this splits the split, emitting redundant *Writable
  // types alongside the *Request ones Django already produced.
  parser: {
    transforms: {
      readWrite: false,
    },
  },
  plugins: [
    ...defaultPlugins,
    '@hey-api/client-fetch',
    {
      name: '@tanstack/react-query',
      infiniteQueryOptions: false,
    },
  ],
});

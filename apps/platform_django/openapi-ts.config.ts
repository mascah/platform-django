import { defaultPlugins, defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: 'http://localhost:8000/api/schema',
  output: 'src/services/platform_django',
  plugins: [
    ...defaultPlugins,
    '@hey-api/client-fetch',
    {
      name: '@tanstack/react-query',
      infiniteQueryOptions: false,
    },
  ],
});

import pluginReactHooks from 'eslint-plugin-react-hooks';
import pluginReactRefresh from 'eslint-plugin-react-refresh';
import globals from 'globals';

import { config as baseConfig } from './base.js';

/**
 * A custom ESLint configuration for Vite React applications.
 *
 * @type {import("eslint").Linter.Config}
 */
export const viteConfig = [
  ...baseConfig,
  pluginReactRefresh.configs.vite,
  {
    languageOptions: {
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
      globals: {
        ...globals.browser,
      },
    },
  },
  pluginReactHooks.configs.flat.recommended,
];

import { defineConfig, devices } from '@playwright/test';
import path from 'path';

const authFile = path.join(__dirname, 'playwright/.auth/user.json');

// Get Django port from environment (the same variable the application server binds)
const djangoPort = process.env.DJANGO_PORT || '8000';
const baseURL = process.env.E2E_BASE_URL || `http://localhost:${djangoPort}`;

export default defineConfig({
  testDir: './tests',

  // Run tests in parallel
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Limit parallel workers on CI for stability
  workers: process.env.CI ? 1 : undefined,

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
    ...(process.env.CI ? ([['github']] as const) : []),
  ],

  // Shared settings for all projects
  use: {
    // Base URL for Django server
    baseURL,

    // Collect trace when retrying the failed test
    trace: 'on-first-retry',

    // Screenshot on failure
    screenshot: 'only-on-failure',

    // Video recording on failure
    video: 'retain-on-failure',
  },

  // Configure projects for authentication setup and browser testing
  projects: [
    // Setup project - runs authentication before tests
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
      testDir: './auth',
    },

    // Main test project - Chromium
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // Use prepared auth state
        storageState: authFile,
      },
      dependencies: ['setup'],
    },
  ],
});

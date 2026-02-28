import { test as base } from '@playwright/test';

// Extend the base test type with custom fixtures
export const test = base.extend({
  context: async ({ context }, use) => {
    // Add X-Playwright header to all requests to disable debug toolbar
    await context.setExtraHTTPHeaders({
      'X-Playwright-Test': '1',
    });

    await use(context);
  },
});

export { expect } from '@playwright/test';

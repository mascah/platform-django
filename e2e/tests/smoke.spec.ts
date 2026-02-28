import { expect, test } from '@/fixtures';

test.describe('Smoke Test', () => {
  test('should load the home page when authenticated', async ({ page }) => {
    await page.goto('/');

    // Verify we're authenticated and the page loaded
    await expect(page.getByText('This is the way.')).toBeVisible();
  });
});

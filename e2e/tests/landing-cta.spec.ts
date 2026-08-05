import { expect, test } from '@/fixtures';

// The landing page's call to action is decided in the browser, from a cookie,
// before the first paint. Only a real browser under the real Content Security
// Policy can prove that works: if the inline script's hash and the policy ever
// drift apart, the browser silently refuses to run the script and the page
// simply shows the wrong button. Nothing on the server notices.
//
// Asserting the class on <html> is what makes these tests a CSP guard rather
// than a CSS one — only the script can put it there.
test.describe('Landing page call to action', () => {
  test('offers the application to a signed-in visitor', async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('html')).toHaveClass(/signed-in/);
    await expect(page.getByRole('link', { name: 'Open App' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Sign In' })).toBeHidden();
  });

  test.describe('with no session', () => {
    test.use({ storageState: { cookies: [], origins: [] } });

    test('offers sign in to everybody else', async ({ page }) => {
      await page.goto('/');

      await expect(page.locator('html')).toHaveClass(/signed-out/);
      await expect(page.getByRole('link', { name: 'Sign In' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Open App' })).toBeHidden();
    });
  });
});

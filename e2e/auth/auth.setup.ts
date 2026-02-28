import path from 'path';

import { expect, test as setup } from '../fixtures';

const authFile = path.join(__dirname, '../playwright/.auth/user.json');

// Test user credentials - should match what create_e2e_user command creates
const E2E_USER_USERNAME = process.env.E2E_USER_EMAIL || 'e2e';
const E2E_USER_PASSWORD = process.env.E2E_USER_PASSWORD || 'e2e-test-password';

setup('authenticate', async ({ page }) => {
  // Navigate to login page
  await page.goto('/accounts/login/');

  // Fill in the login form
  await page.getByLabel('Username').fill(E2E_USER_USERNAME);
  await page.getByLabel('Password').fill(E2E_USER_PASSWORD);

  // Submit the form
  await page.getByRole('button', { name: 'Sign In' }).click();

  // Wait for redirect after successful login
  // Should redirect to home page or wherever LOGIN_REDIRECT_URL points
  await page.waitForURL('/');

  // Verify we're logged in by checking the page content
  await expect(page.getByText('This is the way.')).toBeVisible();

  // Save the storage state (cookies including session cookie)
  await page.context().storageState({ path: authFile });
});

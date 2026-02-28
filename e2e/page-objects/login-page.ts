import { Locator, Page, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly signInButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.getByLabel('Username');
    this.passwordInput = page.getByLabel('Password');
    this.signInButton = page.getByRole('button', { name: 'Sign In' });
  }

  async goto() {
    await this.page.goto('/accounts/login/');
  }

  async login(email: string, password: string) {
    await this.usernameInput.fill(email);
    await this.passwordInput.fill(password);
    await this.signInButton.click();
  }

  async expectToBeOnLoginPage() {
    await expect(this.page).toHaveURL(/\/accounts\/login/);
    await expect(this.usernameInput).toBeVisible();
    await expect(this.passwordInput).toBeVisible();
  }
}

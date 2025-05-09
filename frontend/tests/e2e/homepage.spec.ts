import { test, expect } from '@playwright/test';

test('homepage loads and displays title and text', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/matchwise/i);
  await expect(page.locator('body')).toContainText(/matchwise/i);
}); 
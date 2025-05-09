import { test, expect } from '@playwright/test';

test('fixtures page loads and displays data', async ({ page }) => {
  await page.goto('/fixtures');
  await expect(page.locator('h1')).toHaveText(/fixtures/i);
  // Check for at least one fixture row (adjust selector as needed)
  await expect(page.locator('.fixture-row')).toHaveCountGreaterThan(0);
}); 
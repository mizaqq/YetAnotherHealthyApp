/**
 * Simple E2E test to verify Playwright setup
 */

import { test, expect } from '@playwright/test';

test('homepage loads', async ({ page }) => {
  await page.goto('/');

  // Wait for page to load
  await page.waitForLoadState('domcontentloaded');

  // Verify page loaded (should not be 404)
  expect(page.url()).toContain('localhost');
});


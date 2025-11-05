import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for E2E tests
 * @see https://playwright.dev/docs/test-configuration
 */


export default defineConfig({
  // Test directory
  testDir: './e2e',
  
  // Maximum time one test can run (increased for CI environments)
  timeout: process.env.CI ? 120 * 1000 : 60 * 1000, // 120s on CI, 60s locally
  
  // Run tests in files in parallel
  fullyParallel: true,
  
  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,
  
  // Retry on CI only
  retries: process.env.CI ? 2 : 0,
  
  // Opt out of parallel tests on CI
  workers: process.env.CI ? 1 : undefined,
  
  // Global timeout for the whole test run
  globalTimeout: process.env.CI ? 20 * 60 * 1000 : undefined, // 20 minutes on CI
  
  // Reporter to use
  reporter: [
    ['html'],
    ['list'],
  ],
  
  // Shared settings for all projects
  use: {
    // Base URL to use in actions like `await page.goto('/')`
    baseURL: 'http://localhost:5173',
    
    // Collect trace when retrying the failed test
    trace: 'on-first-retry',
    
    // Screenshot on failure
    screenshot: 'only-on-failure',
    
    // Video on failure
    video: 'retain-on-failure',
    
    // Increase timeouts for slower CI environments
    navigationTimeout: process.env.CI ? 45 * 1000 : 15 * 1000, // 45s on CI, 15s locally
    actionTimeout: process.env.CI ? 30 * 1000 : 10 * 1000, // 30s on CI, 10s locally
  },

  // Configure projects for Chromium only (as per guidelines)
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Run your local dev server before starting the tests
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: process.env.CI ? 180 * 1000 : 120 * 1000, // 3 minutes on CI, 2 minutes locally
  },
});


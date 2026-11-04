import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './preparedness-tests', testMatch: '**/*.spec.ts', workers: 1, fullyParallel: false,
  timeout: 60000, expect: { timeout: 15000 }, reporter: [['list']], outputDir: './test-results-preparedness',
  use: { baseURL: 'http://127.0.0.1:18186', channel: process.env.CI ? undefined : 'chrome', viewport: { width: 1280, height: 900 },
    screenshot: 'only-on-failure', trace: 'retain-on-failure' },
  webServer: { command: '../.venv/bin/python preparedness-tests/server.py', url: 'http://127.0.0.1:18186/api/health',
    timeout: 30000, reuseExistingServer: false, gracefulShutdown: { signal: 'SIGTERM', timeout: 5000 } },
});

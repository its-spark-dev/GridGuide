import { defineConfig } from '@playwright/test';

// Node supplies this runtime value; the frontend intentionally has no Node type dependency.
declare const process: { env: Record<string, string | undefined> };

export default defineConfig({
  testDir: './tests',
  testMatch: '**/*.spec.ts',
  fullyParallel: false,
  workers: 1,
  timeout: 45_000,
  expect: { timeout: 10_000 },
  reporter: [['list'], ['html', { open: 'never' }]],
  outputDir: './test-results',
  use: {
    baseURL: 'http://127.0.0.1:15173',
    channel: 'chrome',
    viewport: { width: 1440, height: 1000 },
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      command: 'PYTHONDONTWRITEBYTECODE=1 ../.venv/bin/python tests/server_fixture.py',
      url: 'http://127.0.0.1:18080/api/health',
      timeout: 120_000,
      reuseExistingServer: process.env.GRIDGUIDE_REUSE_TEST_SERVERS === '1',
      gracefulShutdown: { signal: 'SIGTERM', timeout: 10_000 },
    },
    {
      command: 'npm run dev -- --port 15173',
      url: 'http://127.0.0.1:15173',
      timeout: 30_000,
      reuseExistingServer: process.env.GRIDGUIDE_REUSE_TEST_SERVERS === '1',
      gracefulShutdown: { signal: 'SIGTERM', timeout: 5_000 },
    },
  ],
});

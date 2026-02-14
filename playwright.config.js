const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './test',
  testMatch: /e2e_.*\.spec\.js/,
  timeout: 30_000,
  retries: 0,
  use: {
    headless: true,
    baseURL: process.env.DASHBOARD_BASE_URL || 'http://localhost:8080',
    viewport: { width: 1280, height: 720 },
  },
});

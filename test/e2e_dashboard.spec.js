const { test, expect } = require('@playwright/test');

const BASE_URL = process.env.DASHBOARD_BASE_URL || 'http://localhost:8080';
const DASHBOARD_URL = `${BASE_URL}/dashboard/#/login`;

test.describe('Dashboard E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(DASHBOARD_URL, { waitUntil: 'domcontentloaded' });
  });

  test('shows login page', async ({ page }) => {
    await expect(page.getByText('Frontier Dashboard')).toBeVisible();
    await expect(page.getByLabel('密码')).toBeVisible();
  });

  test('login error shows message', async ({ page }) => {
    await page.fill('input[type="password"]', 'wrong-password');
    await page.click('button[type="submit"]');
    await expect(page.locator('div.text-red-500')).toBeVisible();
  });

  test('login success redirects to dashboard', async ({ page }) => {
    const password = process.env.DASHBOARD_PASSWORD || 'admin';
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard/#/');
    await expect(page.getByText('仪表盘')).toBeVisible();
  });
});

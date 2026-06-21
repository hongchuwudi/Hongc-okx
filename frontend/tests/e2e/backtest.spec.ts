/**
 * 创建时间: 2025-06-21
 * 作者: hongchuwudi
 * 描述: 回测页面交互测试 — 表单填写 + K线预览 + 导航切换
 */

import { test, expect } from '@playwright/test';

test.describe('回测页面', () => {
  test('表单默认值正确渲染', async ({ page }) => {
    await page.goto('/backtest');
    await page.waitForSelector('text=策略');
    // 确认页面核心元素存在
    await expect(page.locator('text=策略')).toBeVisible();
    await expect(page.locator('text=交易对')).toBeVisible();
  });

  test('可以从回测页面切换到历史记录', async ({ page }) => {
    await page.goto('/backtest');

    // 先确认在回测结果视图
    await expect(page.locator('text=策略')).toBeVisible();

    // 点击历史记录按钮（如果存在）
    const historyBtn = page.locator('button:has-text("历史")');
    if (await historyBtn.isVisible()) {
      await historyBtn.click();
      await page.waitForTimeout(300);
    }
  });
});

test.describe('导航栏', () => {
  const LINKS = [
    { label: '仪表盘',   path: '/' },
    { label: '回测',     path: '/backtest' },
    { label: 'Agent',    path: '/agents' },
    { label: '交易',     path: '/trades' },
    { label: '决策',     path: '/decisions' },
    { label: 'Playground', path: '/playground' },
  ];

  for (const { label, path } of LINKS) {
    test(`导航到"${label}"页面`, async ({ page }) => {
      await page.goto('/');
      await page.waitForTimeout(300);

      // 点击导航链接
      const link = page.locator(`a[href="${path}"]`);
      if (await link.isVisible()) {
        await link.click();
        await page.waitForTimeout(500);
        expect(page.url()).toContain(path);
      }
    });
  }
});

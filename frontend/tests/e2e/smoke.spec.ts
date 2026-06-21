/**
 * 创建时间: 2025-06-21
 * 作者: hongchuwudi
 * 描述: 冒烟测试 — 验证全部 6 个页面正常加载，无崩溃/白屏
 */

import { test, expect } from '@playwright/test';

const PAGES = [
  { path: '/',           title: '仪表盘' },
  { path: '/backtest',   title: '回测' },
  { path: '/agents',     title: 'Agent' },
  { path: '/trades',     title: '交易' },
  { path: '/decisions',  title: '决策' },
  { path: '/playground', title: 'Playground' },
];

for (const { path, title } of PAGES) {
  test(`${title} 页面 (${path}) 正常渲染`, async ({ page }) => {
    const res = await page.goto(path);
    // 页面状态码应为 200-299
    expect(res?.status()).toBeLessThan(400);

    // 页面应有可见内容（非白屏）
    const body = page.locator('body');
    await expect(body).toBeVisible();

    // 无控制台报错
    const errors: string[] = [];
    page.on('pageerror', err => errors.push(err.message));

    // 等待布局渲染完成
    await page.waitForTimeout(500);
    expect(errors.filter(e => !e.includes('ResizeObserver'))).toEqual([]);
  });
}

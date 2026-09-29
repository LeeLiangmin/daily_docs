#!/usr/bin/env node
// HTML 幻灯片检查：溢出检测 + 可选逐页截图
// 用法：node check.mjs <deck.html> [--shots] [--out <dir>]
// 依赖：playwright（npm i -D playwright && npx playwright install chromium）

import { resolve, dirname, join } from 'node:path';
import { mkdirSync, existsSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const args = process.argv.slice(2);
const file = args.find(a => !a.startsWith('--'));
if (!file || !existsSync(file)) {
  console.error('用法：node check.mjs <deck.html> [--shots] [--out <dir>]');
  process.exit(2);
}
const shots = args.includes('--shots');
const outIdx = args.indexOf('--out');
const outDir = outIdx >= 0 ? args[outIdx + 1] : join(dirname(resolve(file)), 'shots');

let chromium;
try {
  ({ chromium } = await import('playwright'));
} catch {
  console.error('未找到 playwright。请先运行：npm i -D playwright && npx playwright install chromium');
  process.exit(2);
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
const errors = [];
page.on('pageerror', e => errors.push(String(e)));
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });

await page.goto(pathToFileURL(resolve(file)).href);
await page.waitForFunction(() => typeof window.deckCheck === 'function');
const result = await page.evaluate(() => window.deckCheck());

if (shots) {
  mkdirSync(outDir, { recursive: true });
  for (let i = 1; i <= result.total; i++) {
    await page.evaluate(n => { location.hash = '#' + n; }, i);
    await page.evaluate(() => new Promise(r => setTimeout(r, 50)));
    // 显示该页全部逐步元素再截图
    await page.evaluate(() => document.querySelectorAll('.slide.active .step').forEach(s => s.classList.add('shown')));
    await page.waitForTimeout(300);
    await page.screenshot({ path: join(outDir, String(i).padStart(2, '0') + '.png') });
  }
}

await browser.close();

console.log(`共 ${result.total} 页`);
if (result.overflow.length) console.log(`内容溢出：第 ${result.overflow.join('、')} 页`);
else console.log('溢出检查通过');
if (errors.length) console.log('页面脚本错误：\n  ' + errors.join('\n  '));
if (shots) console.log(`截图已保存到 ${outDir}`);
process.exit(result.overflow.length || errors.length ? 1 : 0);

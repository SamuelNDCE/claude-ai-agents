// Playwright + Opera GX integration (CommonJS so NODE_PATH resolves the global install).
// Opera GX is Chromium-based but NOT an official Playwright channel,
// so we drive it via executablePath. No `playwright install` needed.
const { chromium } = require('playwright');

const OPERA_GX = 'C:\\Users\\Futur\\AppData\\Local\\Programs\\Opera GX\\opera.exe';

(async () => {
  const browser = await chromium.launch({
    executablePath: OPERA_GX,
    headless: false, // Opera GX has no reliable headless mode; run headed
  });
  const page = await browser.newPage();
  await page.goto('https://example.com', { waitUntil: 'domcontentloaded' });
  console.log('PAGE TITLE :', await page.title());
  console.log('USER AGENT :', await page.evaluate(() => navigator.userAgent));
  await browser.close();
  console.log('OK: Opera GX driven by Playwright successfully.');
})().catch((e) => { console.error('FAILED:', e.message); process.exit(1); });

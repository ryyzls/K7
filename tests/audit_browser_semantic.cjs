/** CariSehat browser smoke test. Read-only; blocks all booking writes. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
let chromium;
try { ({ chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright')); }
catch (error) {
  console.error('BLOCKED: Playwright belum tersedia. Instal dengan: npm install --no-save --no-package-lock playwright; npx playwright install chromium');
  process.exit(2);
}
const BASE = process.env.CARISEHAT_URL || 'http://127.0.0.1:8000';
const outputDir = path.resolve('docs/semantic-audit-output/patch06');
fs.mkdirSync(outputDir, { recursive: true });
const results = [];
const check = async (name, fn) => {
  try { const detail = await fn(); results.push({ name, status: 'PASS', detail: detail || '' }); console.log('PASS', name, detail || ''); }
  catch (e) { results.push({ name, status: 'FAIL', detail: String(e.message || e).slice(0, 400) }); console.error('FAIL', name, String(e.message || e).slice(0, 400)); }
};
(async () => {
  let browser;
  try { browser = await chromium.launch({ channel: 'chrome', headless: true }); }
  catch (e) { console.error('BLOCKED: Chromium tidak bisa dijalankan:', e.message); process.exit(2); }
  const ctx = await browser.newContext({ reducedMotion: 'reduce' });
  // Prevent modifications to real booking records, regardless of UI actions.
  await ctx.route('**/api/booking**', route => {
    if (!['GET', 'HEAD', 'OPTIONS'].includes(route.request().method())) return route.abort();
    return route.continue();
  });
  const page = await ctx.newPage();
  const jsErrors = [];
  page.on('pageerror', e => jsErrors.push(e.message));
  try {
    await check('homepage_load_and_206', async () => {
      const response = await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 30000 });
      assert.equal(response.status(), 200);
      await page.locator('#list .card-main').first().waitFor({ timeout: 60000 });
      await page.waitForFunction(() => /206\s+rumah/i.test(document.querySelector('#status')?.textContent || ''), { timeout: 20000 });
      return '206 RS tertera di status katalog';
    });
    if (results.at(-1)?.status === 'PASS') {
      await check('hero_search', async () => {
        await page.locator('#reset').click();
        await page.waitForFunction(() => /206\s+rumah/i.test(document.querySelector('#status')?.textContent || ''), null, { timeout: 20000 });
        const query = 'Adam Malik';
        await page.locator('#hero-q').fill(query);
        // Request a native form submit. The visible button is hidden in this frontend.
        const requests = [];
        const capture = r => { if (r.url().includes('/api/search')) requests.push(r.url()); };
        page.on('request', capture);
        try {
          await page.locator('.hero-search-box').evaluate(form => form.requestSubmit());
          await page.waitForFunction(q => document.querySelector('#q')?.value === q, query, { timeout: 5000 });
          await page.waitForFunction(() => /\d+\s+rumah sakit ditemukan/i.test(document.querySelector('#status')?.textContent || '') &&
            document.querySelector('#status')?.textContent?.includes('rumah sakit ditemukan') &&
            !document.querySelector('#status')?.textContent?.includes('206'), null, { timeout: 20000 });
          const status = await page.locator('#status').innerText();
          assert(!/^0\s+rumah/i.test(status), 'Pencarian Adam Malik menghasilkan 0 RS');
          assert((await page.locator('#list').innerText()).toLowerCase().includes('adam malik'), 'Hasil katalog tidak mengandung Adam Malik');
          assert(requests.some(url => new URL(url).searchParams.get('q') === query), `Tidak ditemukan request search q=${query}. Request tertangkap: ${JSON.stringify(requests)}`);
          return `Pencarian ${query}: ${status.trim()}`;
        } catch (error) {
          const state = await page.evaluate(() => ({ hero: document.querySelector('#hero-q')?.value, q: document.querySelector('#q')?.value, status: document.querySelector('#status')?.textContent }));
          throw new Error(`${error.message}; state=${JSON.stringify(state)}; requests=${JSON.stringify(requests.slice(-5))}`);
        } finally { page.off('request', capture); }
      });
      await check('detail_and_semantic_link', async () => {
        await page.locator('#list .card-main').first().click();
        await page.locator('#detail').waitFor({ state: 'visible', timeout: 15000 });
        const link = page.locator('a:has-text("Halaman Semantik")').first();
        const href = await link.getAttribute('href');
        assert(href && /\/rs\/rs-\d+/.test(href), 'Tautan halaman semantik tidak ditemukan');
        const detail = await ctx.newPage();
        try {
          const r = await detail.goto(new URL(href, BASE).href, { waitUntil: 'domcontentloaded' });
          assert.equal(r.status(), 200);
          assert(await detail.locator('[typeof*="Hospital"]').count() > 0 || await detail.locator('[property="name"]').count() > 0);
        } finally { await detail.close(); }
      });
      await check('return_to_catalog', async () => {
        await page.locator('#d-back').click();
        await page.waitForFunction(() => !document.querySelector('#detail')?.classList.contains('show'));
      });
      await check('filter_class_C', async () => {
        await page.locator('#reset').click();
        await page.locator('#kelas').selectOption('C');
        await page.waitForFunction(() => /120\s+rumah/i.test(document.querySelector('#status')?.textContent || ''), { timeout: 20000 });
        return '120 RS kelas C';
      });
      await check('no_result_and_reset', async () => {
        await page.locator('#reset').click();
        await page.waitForFunction(() => /206\s+rumah/i.test(document.querySelector('#status')?.textContent || ''), null, { timeout: 20000 });
        const query = 'zzzzz-no-match-123456';
        await page.locator('#hero-q').fill(query);
        const requests = [];
        const capture = r => { if (r.url().includes('/api/search')) requests.push(r.url()); };
        page.on('request', capture);
        try {
          await page.locator('.hero-search-box').evaluate(form => form.requestSubmit());
          await page.waitForFunction(q => document.querySelector('#q')?.value === q, query, { timeout: 5000 });
          await page.waitForFunction(() => /0\s+rumah sakit ditemukan/i.test(document.querySelector('#status')?.textContent || ''), null, { timeout: 20000 });
          assert(requests.some(url => new URL(url).searchParams.get('q') === query), `Request q=${query} tidak ditemukan: ${JSON.stringify(requests)}`);
          await page.locator('#reset').click();
          await page.waitForFunction(() => /206\s+rumah/i.test(document.querySelector('#status')?.textContent || ''), null, { timeout: 20000 });
          return '0 hasil dan reset kembali ke 206 RS';
        } catch (error) {
          const state = await page.evaluate(() => ({ hero: document.querySelector('#hero-q')?.value, q: document.querySelector('#q')?.value, status: document.querySelector('#status')?.textContent }));
          throw new Error(`${error.message}; state=${JSON.stringify(state)}; requests=${JSON.stringify(requests.slice(-5))}`);
        } finally { page.off('request', capture); }
      });
      for (const width of [375, 768, 1440]) {
        await check('responsive_' + width, async () => {
          await page.setViewportSize({ width, height: 900 });
          await page.waitForTimeout(300);
          assert(await page.locator('#list .card-main').first().isVisible());
          const dimensions = await page.evaluate(() => ({ scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth }));
          assert(dimensions.scrollWidth <= dimensions.clientWidth + 2, `Horizontal overflow ${dimensions.scrollWidth} > ${dimensions.clientWidth}`);
          await page.screenshot({ path: path.join(outputDir, `catalog_${width}.png`), fullPage: true, animations: 'disabled' });
          return `Screenshot catalog_${width}.png`;
        });
      }
    }
    await check('sparql_studio_js', async () => {
      const studio = await ctx.newPage();
      try {
        const response = await studio.goto(BASE + '/sparql', { waitUntil: 'domcontentloaded', timeout: 30000 });
        assert.equal(response.status(), 200);
        await studio.locator('.yasgui').waitFor({ timeout: 20000 });
        await studio.screenshot({ path: path.join(outputDir, 'sparql_studio.png'), fullPage: true, animations: 'disabled' });
        return 'YASGUI berhasil dirender dalam browser';
      } finally { await studio.close(); }
    });
    await check('no_uncaught_homepage_js_errors', async () => {
      assert.deepEqual(jsErrors, []);
    });
  } finally {
    const summary = { source: 'CariSehat ZIP K7(4), test browser against local runtime', base_url: BASE,
      note: 'Hanya pengujian browser dan screenshot; booking mutations blocked. Tidak menguji kebenaran semua data RS.',
      counts: { pass: results.filter(x => x.status === 'PASS').length, fail: results.filter(x => x.status === 'FAIL').length }, results };
    fs.writeFileSync(path.join(outputDir, 'browser_semantic_report.json'), JSON.stringify(summary, null, 2));
    console.log('\nSUMMARY', JSON.stringify(summary.counts), '\nOutput:', outputDir);
    await browser.close();
    if (summary.counts.fail > 0) process.exitCode = 1;
  }
})().catch(err => { console.error('ERROR', err.stack || err); process.exitCode = 1; });

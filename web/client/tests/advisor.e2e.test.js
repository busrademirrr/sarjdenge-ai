process.env.NODE_ENV = 'test';

import test from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from 'playwright-core';
import app from '../../server/index.js';

let server;
let browser;
let page;
const PORT = 5096;
const BASE_URL = `http://localhost:${PORT}`;

test.before(async () => {
  // 1. Start test Express server
  await new Promise((resolve) => {
    server = app.listen(PORT, resolve);
  });

  // 2. Launch real local Chrome (fallback to Edge)
  try {
    browser = await chromium.launch({ channel: 'chrome', headless: true });
  } catch {
    browser = await chromium.launch({ channel: 'msedge', headless: true });
  }

  const context = await browser.newContext();
  page = await context.newPage();
});

test.after(async () => {
  if (page) await page.close().catch(() => {});
  if (browser) await browser.close().catch(() => {});
  if (server) {
    await new Promise((resolve) => server.close(resolve));
  }
});

test('1. Ger├ğek Chrome: Kapasite Dan─▒┼şman─▒ sekmesi a├ğ─▒lmal─▒ ve Sentetik Senaryo etiketi do─şrulanmal─▒', { timeout: 30000 }, async () => {
  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });

  // 1. Navbar ├╝zerindeki Kapasite Dan─▒┼şman─▒ sekmesine t─▒kla
  const advisorTabBtn = page.locator('nav button', { hasText: 'Kapasite Dan─▒┼şman─▒' });
  await advisorTabBtn.waitFor({ state: 'visible', timeout: 5000 });
  await advisorTabBtn.click();

  // 2. Kapasite Dan─▒┼şman─▒ ba┼şl─▒─ş─▒n─▒n g├Âr├╝nd├╝─ş├╝n├╝ do─şrula
  const heading = page.locator('h2', { hasText: 'Canl─▒ Kapasite Dan─▒┼şman─▒' });
  await heading.waitFor({ state: 'visible', timeout: 5000 });
  assert.ok(await heading.isVisible());

  // 3. Sentetik senaryo rozetinin g├Âr├╝n├╝r oldu─şunu do─şrula
  const badge = page.locator('span', { hasText: 'SENTET─░K SENARYO (T├£RK─░YE VARSAYIMI)' }).first();
  await badge.waitFor({ state: 'visible', timeout: 25000 });
  assert.ok(await badge.isVisible());
});

test('2. Ger├ğek Chrome: 4 Y├Ântem (FCFS, EDF, MPC, E┼şit Payla┼ş─▒m) ve kW birimleri aray├╝zde g├Âr├╝nmeli', { timeout: 30000 }, async () => {
  // 4 Y├Ântem kartlar─▒n─▒n ba┼şl─▒klar─▒n─▒ kontrol et
  const fcfsCard = page.locator('div', { hasText: 'FCFS (─░lk Gelen ─░lk ┼Şarj)' }).first();
  const edfCard = page.locator('div', { hasText: 'EDF (En Erken Termin ├ûncelikli)' }).first();
  const esitCard = page.locator('div', { hasText: 'Aktif Ara├ğlara E┼şit G├╝├ğ Payla┼ş─▒m─▒' }).first();
  const mpcCard = page.locator('div', { hasText: 'MPC (LP / HiGHS Optimizasyon)' }).first();

  await fcfsCard.waitFor({ state: 'visible', timeout: 10000 });
  await edfCard.waitFor({ state: 'visible', timeout: 10000 });
  await esitCard.waitFor({ state: 'visible', timeout: 10000 });
  await mpcCard.waitFor({ state: 'visible', timeout: 10000 });

  assert.ok(await fcfsCard.isVisible());
  assert.ok(await edfCard.isVisible());
  assert.ok(await esitCard.isVisible());
  assert.ok(await mpcCard.isVisible());

  // kW birimlerinin g├Âr├╝nt├╝lendi─şini do─şrula
  const kwUnits = await page.locator('text=kW').all();
  assert.ok(kwUnits.length >= 4, 'En az 4 kW birim etiketi bulunmal─▒');
});

test('3. Ger├ğek Chrome: 1 ara├ğ fiziksel yetersizlik uyar─▒s─▒ ve tarama matrisi do─şrulanmal─▒', { timeout: 15000 }, async () => {
  // 1 ara├ğ kal─▒┼ş s├╝resi azl─▒─ş─▒ uyar─▒s─▒n─▒n g├Âr├╝nt├╝lendi─şini kontrol et
  const warningText = page.locator('text=1 ara├ğ kal─▒┼ş s├╝resi azl─▒─ş─▒ nedeniyle tam dolamaz');
  await warningText.waitFor({ state: 'visible', timeout: 5000 });
  assert.ok(await warningText.isVisible());

  // Kapasite tarama tablosunun g├Âr├╝n├╝r oldu─şunu do─şrula
  const table = page.locator('table');
  await table.waitFor({ state: 'visible', timeout: 5000 });
  assert.ok(await table.isVisible());

  // Tabloda en az bir "├ûNER─░LEN ASGAR─░" rozetinin yer ald─▒─ş─▒n─▒ do─şrula
  const minBadge = page.locator('text=├ûNER─░LEN ASGAR─░');
  assert.ok(await minBadge.count() >= 1);
});

test('4. Ger├ğek Chrome: Apartman senaryosunda e┼şitlik (tie-breaking), yan─▒lt─▒c─▒ tasarruf etiketinin kald─▒r─▒lmas─▒ ve 390px mobil ta┼şma kontrol├╝', { timeout: 35000 }, async () => {
  // 1. Senaryo se├ğim kutusundan apartman_gece se├ğ
  const selectEl = page.locator('select').first();
  await selectEl.selectOption('apartman_gece');

  // 2. E┼şitlik ba┼şl─▒─ş─▒n─▒n ("En d├╝┼ş├╝k kapasite: y├Ântemler e┼şit") g├Âr├╝nmesini bekle
  const tieHeading = page.locator('text=En d├╝┼ş├╝k kapasite: y├Ântemler e┼şit');
  await tieHeading.waitFor({ state: 'visible', timeout: 25000 });
  assert.ok(await tieHeading.isVisible(), 'E┼şit kapasitede "En d├╝┼ş├╝k kapasite: y├Ântemler e┼şit" g├Âsterilmeli');

  const mainText = await page.innerText('main');
  assert.ok(!mainText.includes('Trafo Tasarrufu: %'), 'Kaba ─▒zgaradan kaynaklanan yan─▒lt─▒c─▒ "Trafo Tasarrufu: %" etiketi g├Âsterilmemeli');
  assert.ok(mainText.includes('senaryodaki nominal trafo kapasitesi 80.0 kW'), 'Nominal trafo kapasitesi ├Âzeti g├Âr├╝nmeli');

  // 3. 390px mobil geni┼şlikte ta┼şma (horizontal overflow) kontrol├╝
  await page.setViewportSize({ width: 390, height: 844 });
  const overflowMobile = await page.evaluate(() => {
    return document.documentElement.scrollWidth > document.documentElement.clientWidth;
  });
  assert.equal(overflowMobile, false, '390px mobil g├Âr├╝n├╝mde yatay sayfa ta┼şmas─▒ olmamal─▒');

  // Masa├╝st├╝ boyuta geri d├Ân
  await page.setViewportSize({ width: 1280, height: 800 });
});

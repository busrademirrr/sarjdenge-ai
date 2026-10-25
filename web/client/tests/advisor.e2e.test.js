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

test('1. Gerçek Chrome: Kapasite Danışmanı sekmesi açılmalı ve Sentetik Senaryo etiketi doğrulanmalı', { timeout: 60000 }, async () => {
  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });

  // 1. Navbar üzerindeki Kapasite Danışmanı sekmesine tıkla
  const advisorTabBtn = page.locator('nav button', { hasText: 'Kapasite Danışmanı' });
  await advisorTabBtn.waitFor({ state: 'visible', timeout: 5000 });
  await advisorTabBtn.click();

  // 2. Kapasite Danışmanı başlığının göründüğünü doğrula
  const heading = page.locator('h2', { hasText: 'Canlı Kapasite Danışmanı' });
  await heading.waitFor({ state: 'visible', timeout: 5000 });
  assert.ok(await heading.isVisible());

  // 3. Sentetik senaryo rozetinin görünür olduğunu doğrula
  const badge = page.locator('span', { hasText: 'SENTETİK SENARYO (TÜRKİYE VARSAYIMI)' }).first();
  await badge.waitFor({ state: 'visible', timeout: 50000 });
  assert.ok(await badge.isVisible());
});

test('2. Gerçek Chrome: 4 Yöntem (FCFS, EDF, MPC, Eşit Paylaşım) ve kW birimleri arayüzde görünmeli', { timeout: 30000 }, async () => {
  // 4 Yöntem kartlarının başlıklarını kontrol et
  const fcfsCard = page.locator('div', { hasText: 'FCFS (İlk Gelen İlk Şarj)' }).first();
  const edfCard = page.locator('div', { hasText: 'EDF (En Erken Termin Öncelikli)' }).first();
  const esitCard = page.locator('div', { hasText: 'Aktif Araçlara Eşit Güç Paylaşımı' }).first();
  const mpcCard = page.locator('div', { hasText: 'MPC (LP / HiGHS Optimizasyon)' }).first();

  await fcfsCard.waitFor({ state: 'visible', timeout: 10000 });
  await edfCard.waitFor({ state: 'visible', timeout: 10000 });
  await esitCard.waitFor({ state: 'visible', timeout: 10000 });
  await mpcCard.waitFor({ state: 'visible', timeout: 10000 });

  assert.ok(await fcfsCard.isVisible());
  assert.ok(await edfCard.isVisible());
  assert.ok(await esitCard.isVisible());
  assert.ok(await mpcCard.isVisible());

  // kW birimlerinin görüntülendiğini doğrula
  const kwUnits = await page.locator('text=kW').all();
  assert.ok(kwUnits.length >= 4, 'En az 4 kW birim etiketi bulunmalı');
});

test('3. Gerçek Chrome: 1 araç fiziksel yetersizlik uyarısı ve tarama matrisi doğrulanmalı', { timeout: 15000 }, async () => {
  // 1 araç kalış süresi azlığı uyarısının görüntülendiğini kontrol et
  const warningText = page.locator('text=1 araç kalış süresi azlığı nedeniyle tam dolamaz');
  await warningText.waitFor({ state: 'visible', timeout: 5000 });
  assert.ok(await warningText.isVisible());

  // Kapasite tarama tablosunun görünür olduğunu doğrula
  const table = page.locator('table');
  await table.waitFor({ state: 'visible', timeout: 5000 });
  assert.ok(await table.isVisible());

  // Tabloda en az bir "ÖNERİLEN ASGARİ" rozetinin yer aldığını doğrula
  const minBadge = page.locator('text=ÖNERİLEN ASGARİ');
  assert.ok(await minBadge.count() >= 1);
});

test('4. Gerçek Chrome: Apartman senaryosunda eşitlik (tie-breaking), yanıltıcı tasarruf etiketinin kaldırılması ve 390px mobil taşma kontrolü', { timeout: 35000 }, async () => {
  // 1. Senaryo seçim kutusundan apartman_gece seç
  const selectEl = page.locator('select').first();
  await selectEl.selectOption('apartman_gece');

  // 2. Eşitlik başlığının (yöntem adlarıyla "eşit: 15,0 kW") görünmesini bekle
  const tieHeading = page.locator('text=eşit: 15,0 kW');
  await tieHeading.waitFor({ state: 'visible', timeout: 25000 });
  assert.ok(await tieHeading.isVisible(), 'Eşit kapasitede yöntem adlarıyla eşitlik başlığı gösterilmeli');

  const mainText = await page.innerText('main');
  assert.ok(!mainText.includes('Trafo Tasarrufu: %'), 'Kaba ızgaradan kaynaklanan yanıltıcı "Trafo Tasarrufu: %" etiketi gösterilmemeli');
  assert.ok(mainText.includes('Mevcut trafo yeterli') || mainText.includes('80.0 kW'), 'Trafo durumu görünmeli');

  // 3. 390px mobil genişlikte taşma (horizontal overflow) kontrolü
  await page.setViewportSize({ width: 390, height: 844 });
  const overflowMobile = await page.evaluate(() => {
    return document.documentElement.scrollWidth > document.documentElement.clientWidth;
  });
  assert.equal(overflowMobile, false, '390px mobil görünümde yatay sayfa taşması olmamalı');

  // Masaüstü boyuta geri dön
  await page.setViewportSize({ width: 1280, height: 800 });
});

test('5. Gerçek Chrome: Çok Günlü Mod (≥20 Gün) dağılım tablosu, başarılı gün sayısı ve ACN TA senaryosu doğrulanmalı', { timeout: 360000 }, async () => {
  // 1. Çok Günlü Mod butonuna tıkla
  const multiDayBtn = page.locator('button', { hasText: 'Çok Günlü Mod (≥20 Gün)' });
  await multiDayBtn.click();

  // 2. Çok günlü yüklenme bildiriminin veya tablosunun gelmesini bekle
  const multiHeading = page.locator('h3', { hasText: 'Çok Günlü Kapasite Dağılımı' });
  await multiHeading.waitFor({ state: 'visible', timeout: 150000 });
  const headingText = await multiHeading.innerText();
  assert.ok(headingText.includes('20 Gün / Tohum'), `Beklenen '20 Gün / Tohum' başlığı, gelen: '${headingText}'`);

  // 3. Başarılı Gün sütununun varlığını kontrol et
  const basariliGunHeader = page.locator('th', { hasText: 'Başarılı Gün' });
  await basariliGunHeader.waitFor({ state: 'visible', timeout: 5000 });
  assert.ok(await basariliGunHeader.isVisible());

  // 4. Dönemler Arası Test (acn_gercek_ta) seçildiğinde 0 gün hatası olmadığını doğrula
  const selectEl = page.locator('select').first();
  await selectEl.selectOption('acn_gercek_ta');

  await page.waitForTimeout(1000);
  const taHeading = page.locator('h3', { hasText: 'Çok Günlü Kapasite Dağılımı' });
  await taHeading.waitFor({ state: 'visible', timeout: 210000 });
  const taHeadingText = await taHeading.innerText();
  assert.ok(!taHeadingText.includes('(0 Gün'), `0 Gün hatası oluşmamalı: '${taHeadingText}'`);
  assert.ok(taHeadingText.includes('20 Gün / Tohum'), `ACN TA için 20 gün bekleniyordu: '${taHeadingText}'`);
});

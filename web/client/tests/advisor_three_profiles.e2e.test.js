process.env.NODE_ENV = 'test';

import test from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from 'playwright-core';
import app from '../../server/index.js';

let server;
let browser;
let page;
const PORT = 5098;
const BASE_URL = `http://localhost:${PORT}`;

test.before(async () => {
  await new Promise((resolve) => {
    server = app.listen(PORT, resolve);
  });

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

const PROFILES = [
  { id: 'acn_gercek_ta', name: 'ACN Gerçek Saha — Dönemler Arası' },
  { id: 'karma', name: 'Türkiye Karma Yerleşke (İş + Konut)' },
  { id: 'isyeri_gunduz', name: 'Türkiye İş Yeri Kampüsü' },
];

for (const prof of PROFILES) {
  test(`Gerçek Chrome Doğrulaması: ${prof.name} (${prof.id}) - 2 Ardışık Çalıştırma`, { timeout: 300000 }, async () => {
    await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });

    // 1. Kapasite Danışmanı sekmesine tıkla
    const advisorTabBtn = page.locator('nav button', { hasText: 'Kapasite Danışmanı' });
    await advisorTabBtn.waitFor({ state: 'visible', timeout: 5000 });
    await advisorTabBtn.click();

    // 2. Çok Günlü Mod butonuna tıkla
    const multiDayBtn = page.locator('button', { hasText: 'Çok Günlü Mod (≥20 Gün)' });
    await multiDayBtn.waitFor({ state: 'visible', timeout: 5000 });
    await multiDayBtn.click();

    const selectEl = page.locator('select[aria-label="Senaryo Seçimi"]');
    await selectEl.waitFor({ state: 'visible', timeout: 5000 });

    console.log(`\n======================================================`);
    console.log(`[TEST BAŞLADI] Profil: ${prof.name} (${prof.id})`);
    console.log(`======================================================`);

    const multiHeading = page.locator('h3', { hasText: 'Çok Günlü Kapasite Dağılımı' });

    // --- ÇALIŞTIRMA 1: Senaryoyu seç ---
    const tStart1 = Date.now();
    const [res1] = await Promise.all([
      page.waitForResponse(
        (r) => r.url().includes('/api/capacity-advisor') && r.request().method() === 'POST',
        { timeout: 180000 }
      ),
      selectEl.selectOption(prof.id),
    ]);

    const apiStatus1 = res1.status();
    const apiData1 = await res1.json();

    await multiHeading.waitFor({ state: 'visible', timeout: 180000 });
    const wallSec1 = (Date.now() - tStart1) / 1000;
    const headingText1 = await multiHeading.innerText();

    console.log(`\n>>> [ÇALIŞTIRMA #1 SONUCU - ${prof.name}]`);
    console.log(`  Gerçek Tarayıcı Süresi: ${wallSec1.toFixed(2)} sn`);
    console.log(`  HTTP Kodu: ${apiStatus1}`);
    console.log(`  Hata Durumu: ${apiData1.error || 'Yok (Başarılı)'}`);
    console.log(`  Render Edilen Başlık: "${headingText1}"`);

    assert.equal(apiStatus1, 200, `HTTP durum kodu 200 olmalı, gelen: ${apiStatus1}`);
    assert.equal(apiData1.success, true, 'API success true olmalı');
    assert.ok(apiData1.advisor, 'advisor objesi bulunmalı');
    const cg1 = apiData1.advisor.cok_gunlu_analiz;
    assert.ok(cg1);
    console.log(`  Seçilen Gün Sayısı: ${cg1.toplam_gun}`);
    console.log(`  Değerlendirilen Başarılı Gün: ${cg1.degerlendirilen_gun_sayisi}`);
    console.log(`  Hariç Tutulan Gün: ${cg1.haric_tutulan_gun_sayisi}`);
    assert.equal(cg1.toplam_gun, 20);
    assert.ok(headingText1.includes('20 Gün / Tohum'), `Başlık 20 Gün içermeli: '${headingText1}'`);
    assert.ok(!headingText1.includes('(0 Gün'), '0 Gün hatası olmamalı');

    for (const y of cg1.yontemler) {
      console.log(`    - ${y.kod} (${y.ad}): Medyan=${y.medyan_kw} kW | Başarılı Gün=${y.orneklem_sayisi}/${cg1.toplam_gun} (%${y.erisme_orani_yuzde})`);
      assert.ok(y.orneklem_sayisi > 0);
      assert.ok(y.medyan_kw !== null);
    }

    // --- ÇALIŞTIRMA 2: "Yeniden Hesapla" butonuna basarak ardışık çalıştırma ---
    console.log(`\n>>> [ÇALIŞTIRMA #2 BAŞLATILIYOR (Yeniden Hesapla) - ${prof.name}]`);
    const refreshBtn = page.locator('button', { hasText: 'Yeniden Hesapla' });
    await refreshBtn.waitFor({ state: 'visible', timeout: 5000 });

    const tStart2 = Date.now();
    const [res2] = await Promise.all([
      page.waitForResponse(
        (r) => r.url().includes('/api/capacity-advisor') && r.request().method() === 'POST',
        { timeout: 180000 }
      ),
      refreshBtn.click(),
    ]);

    const apiStatus2 = res2.status();
    const apiData2 = await res2.json();
    await multiHeading.waitFor({ state: 'visible', timeout: 180000 });
    const wallSec2 = (Date.now() - tStart2) / 1000;
    const headingText2 = await multiHeading.innerText();

    console.log(`\n>>> [ÇALIŞTIRMA #2 SONUCU - ${prof.name}]`);
    console.log(`  Gerçek Tarayıcı Süresi: ${wallSec2.toFixed(2)} sn`);
    console.log(`  HTTP Kodu: ${apiStatus2}`);
    console.log(`  Hata Durumu: ${apiData2.error || 'Yok (Başarılı)'}`);
    console.log(`  Render Edilen Başlık: "${headingText2}"`);

    assert.equal(apiStatus2, 200, `HTTP durum kodu 200 olmalı, gelen: ${apiStatus2}`);
    assert.equal(apiData2.success, true);
    const cg2 = apiData2.advisor.cok_gunlu_analiz;
    assert.equal(cg2.toplam_gun, 20);
    assert.ok(headingText2.includes('20 Gün / Tohum'));

    for (const y of cg2.yontemler) {
      console.log(`    - ${y.kod} (${y.ad}): Medyan=${y.medyan_kw} kW | Başarılı Gün=${y.orneklem_sayisi}/${cg2.toplam_gun} (%${y.erisme_orani_yuzde})`);
      assert.ok(y.orneklem_sayisi > 0);
    }

    console.log(`\n[BAŞARILI] ${prof.name} için 2 ardışık çalıştırma eksiksiz tamamlandı.\n`);
  });
}

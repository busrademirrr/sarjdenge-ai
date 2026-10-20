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

const MOCK_SUCCESS_SIMULATION = {
  senaryo_id: 'isyeri_gunduz',
  senaryo_bilgi: { id: 'isyeri_gunduz', name: 'Türkiye İş Yeri Kampüsü' },
  veri_kaynagi_etiketi: 'SENTETİK MODEL (VARSAYIM)',
  tarih: '2026-03-10',
  arac_sayisi: 2,
  f_orani: 0.5,
  kapasite_siniri_kw: 75.0,
  kontrolsuz_tepe_kw: 150.0,
  talep_toplam_kwh: 40.0,
  zaman_etiketleri: Array.from({ length: 96 }, (_, i) => {
    const h = String(Math.floor(i / 4)).padStart(2, '0');
    const m = String((i % 4) * 15).padStart(2, '0');
    return `${h}:${m}`;
  }),
  kontrolsuz_profil_kw: Array(96).fill(10.0),
  yontem_profilleri: {
    fcfs_beyan: Array(96).fill(8.0),
    edf_beyan: Array(96).fill(8.5),
    edf_tahmin_guvenli: Array(96).fill(9.0),
    mpc_beyan: Array(96).fill(8.8),
    mpc_tahmin_guvenli: Array(96).fill(8.2),
    mpc_hibrit_asimetrik: Array(96).fill(8.4),
  },
  kpi_ozet: {
    fcfs_beyan: { kod: 'fcfs_beyan', ad: 'FCFS (Beyan)', basari_orani_yuzde: 85.0, teslim_orani_yuzde: 90.0, erken_ayrilan_basari_yuzde: 80.0, p10_adillik_yuzde: 82.0, kapasite_ihlali_kw: 0.0 },
    edf_beyan: { kod: 'edf_beyan', ad: 'EDF (Beyan)', basari_orani_yuzde: 92.0, teslim_orani_yuzde: 95.0, erken_ayrilan_basari_yuzde: 88.0, p10_adillik_yuzde: 89.0, kapasite_ihlali_kw: 0.0 },
    edf_tahmin_guvenli: { kod: 'edf_tahmin_guvenli', ad: 'EDF Güvenli', basari_orani_yuzde: 94.0, teslim_orani_yuzde: 96.0, erken_ayrilan_basari_yuzde: 91.0, p10_adillik_yuzde: 92.0, kapasite_ihlali_kw: 0.0 },
    mpc_beyan: { kod: 'mpc_beyan', ad: 'MPC (Beyan)', basari_orani_yuzde: 89.0, teslim_orani_yuzde: 93.0, erken_ayrilan_basari_yuzde: 84.0, p10_adillik_yuzde: 86.0, kapasite_ihlali_kw: 0.0 },
    mpc_tahmin_guvenli: { kod: 'mpc_tahmin_guvenli', ad: 'MPC Güvenli', basari_orani_yuzde: 88.5, teslim_orani_yuzde: 92.5, erken_ayrilan_basari_yuzde: 83.0, p10_adillik_yuzde: 85.0, kapasite_ihlali_kw: 0.0 },
    mpc_hibrit_asimetrik: { kod: 'mpc_hibrit_asimetrik', ad: 'MPC Hibrit', basari_orani_yuzde: 90.0, teslim_orani_yuzde: 93.5, erken_ayrilan_basari_yuzde: 86.0, p10_adillik_yuzde: 87.0, kapasite_ihlali_kw: 0.0 },
  },
  araclar: [
    {
      arac_id: 'EV-001',
      sira: 1,
      kullanici_id: 'U-01',
      giris_adim: 32,
      ayril_adim: 68,
      giris_saat: '08:00',
      ayril_saat: '17:00',
      beyan_ayril_saat: '17:30',
      sure_gercek_dk: 540,
      sure_beyan_dk: 570,
      sure_tahmin_q20_dk: 480,
      sure_tahmin_q50_dk: 540,
      sure_tahmin_q80_dk: 600,
      talep_gercek_kwh: 18.0,
      talep_beyan_kwh: 20.0,
      tahmin_kwh_q20: 15.0,
      tahmin_kwh_q50: 18.0,
      tahmin_kwh_q80: 22.0,
      erken_ayrildi: false,
      teslim_kwh: { fcfs_beyan: 18.0, edf_tahmin_guvenli: 18.0, mpc_tahmin_guvenli: 17.5 },
      doyum_orani: { fcfs_beyan: 1.0, edf_tahmin_guvenli: 1.0, mpc_tahmin_guvenli: 0.97 },
      sarj_suresi_dk: { edf_tahmin_guvenli: 240 },
      neden_analizi: { ozet_hukum: 'Normal Planlı Şarj Tamamlandı', nedenler: [] },
    },
  ],
};

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

test('1. Simülasyon hatasında Toast görünmeli', async () => {
  // Intercept simulate request and return mock error
  await page.route('**/api/simulate', async (route) => {
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({
        success: false,
        error: 'Tesis trafo kapasitesi yetersiz veya simülasyon hatası oluştu.',
      }),
    });
  });

  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });

  // Toast should appear (initial run or click run)
  const alertLocator = page.locator('[role="alert"]');
  await alertLocator.waitFor({ state: 'visible', timeout: 5000 });

  const titleText = await alertLocator.locator('h4').innerText();
  const bodyText = await alertLocator.locator('p').innerText();

  assert.equal(titleText, 'Simülasyon Yürütülemedi');
  assert.ok(bodyText.includes('Tesis trafo kapasitesi yetersiz'));
});

test('2. Kapatma düğmesi Toast\'ı DOM\'dan kaldırmalı', async () => {
  const alertLocator = page.locator('[role="alert"]');
  assert.ok(await alertLocator.isVisible());

  // Click close button
  const closeBtn = alertLocator.locator('button[aria-label="Bildirimi kapat"]');
  await closeBtn.click();

  // Wait for it to disappear
  await alertLocator.waitFor({ state: 'detached', timeout: 3000 });
  assert.equal(await alertLocator.count(), 0);
});

test('3. Ağ hatasında (Connection drop) anlaşılır bildirim gösterilmeli', async () => {
  // Mock network abort
  await page.unroute('**/api/simulate');
  await page.route('**/api/simulate', async (route) => {
    await route.abort('failed');
  });

  // Click "Simülasyonu Çalıştır" button
  const runBtn = page.locator('button:has-text("Simülasyonu Çalıştır")');
  await runBtn.click();

  const alertLocator = page.locator('[role="alert"]');
  await alertLocator.waitFor({ state: 'visible', timeout: 5000 });

  const titleText = await alertLocator.locator('h4').innerText();
  const bodyText = await alertLocator.locator('p').innerText();

  assert.equal(titleText, 'Bağlantı Hatası');
  assert.ok(bodyText.includes('Simülasyon servisine bağlanılamadı'));
});

test('4. Hata mesajındaki sahte Bearer token ve traceback kullanıcıya gösterilmemeli', async () => {
  // Mock sensitive leak attempt
  const SENSITIVE_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.super_secret_payload_token_999';
  const RAW_TRACEBACK = 'Traceback (most recent call last):\n  File "sarjdenge/sim.py", line 42, in simule\nZeroDivisionError: division by zero';

  await page.unroute('**/api/simulate');
  await page.route('**/api/simulate', async (route) => {
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({
        success: false,
        error: `Yetkisiz erişim: Bearer ${SENSITIVE_TOKEN}\n${RAW_TRACEBACK}`,
      }),
    });
  });

  const runBtn = page.locator('button:has-text("Simülasyonu Çalıştır")');
  await runBtn.click();

  const alertLocator = page.locator('[role="alert"]');
  await alertLocator.waitFor({ state: 'visible', timeout: 5000 });
  const bodyText = await alertLocator.locator('p').innerText();

  // Token must be masked
  assert.ok(!bodyText.includes(SENSITIVE_TOKEN), 'Hassas Bearer token sızdırıldı!');
  assert.ok(bodyText.includes('[KORUMALI]'), '[KORUMALI] maskesi bulunamadı!');

  // Traceback must be completely stripped
  assert.ok(!bodyText.includes('Traceback (most recent call last)'), 'Traceback sızdırıldı!');
  assert.ok(!bodyText.includes('sarjdenge/sim.py'), 'Python dosya yolu sızdırıldı!');
});

test('5. "Yeniden Dene" düğmesi hata alınan parametreleri aynen tekrarlamalı', async () => {
  let capturedPayload = null;

  await page.unroute('**/api/simulate');
  await page.route('**/api/simulate', async (route) => {
    capturedPayload = JSON.parse(route.request().postData());
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ success: false, error: 'Tekrar deneme testi hatası' }),
    });
  });

  const alertLocator = page.locator('[role="alert"]');
  const retryBtn = alertLocator.locator('button:has-text("Yeniden Dene")');
  await retryBtn.click();

  assert.ok(capturedPayload !== null, 'Yeniden dene isteği gönderilmedi');
  assert.equal(capturedPayload.scenarioId, 'isyeri_gunduz');
  assert.equal(capturedPayload.f, 0.5);
  assert.equal(capturedPayload.day, '2026-03-10');
});

test('6. Yeniden deneme sırasında mükerrer tıklamalar engellenmeli (Debounce/Lock)', async () => {
  let requestCount = 0;

  await page.unroute('**/api/simulate');
  await page.route('**/api/simulate', async (route) => {
    requestCount++;
    // Delay 1000ms to test pending lock state
    await new Promise((r) => setTimeout(r, 1000));
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ success: false, error: 'Kilit testi hatası' }),
    });
  });

  const alertLocator = page.locator('[role="alert"]');
  const retryBtn = alertLocator.locator('button[aria-label="Simülasyonu aynı parametrelerle yeniden dene"]');

  // First click triggers pending request
  await retryBtn.click();

  // Check disabled state immediately
  assert.ok(await retryBtn.isDisabled(), 'Yeniden dene butonu istek sırasında disabled olmadı!');
  assert.ok((await retryBtn.innerText()).includes('Yeniden Deneniyor…'));

  // Attempt click while disabled (should not trigger new request)
  await retryBtn.click({ force: true }).catch(() => {});

  // Wait for route to complete
  await page.waitForTimeout(1200);

  // Exactly 1 request should have been made
  assert.equal(requestCount, 1, `Beklenen 1 istek, gelen: ${requestCount}`);
});

test('7. Başarılı simülasyon yanıtı geldiğinde eski hata Toast\'ı temizlenmeli', async () => {
  const alertLocator = page.locator('[role="alert"]');
  assert.ok(await alertLocator.isVisible(), 'Test başlangıcında hata açık olmalı');

  // Now fulfill route with successful simulation data
  await page.unroute('**/api/simulate');
  await page.route('**/api/simulate', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        simulation: MOCK_SUCCESS_SIMULATION,
      }),
    });
  });

  const retryBtn = alertLocator.locator('button:has-text("Yeniden Dene")');
  await retryBtn.click();

  // Toast must disappear automatically
  await alertLocator.waitFor({ state: 'detached', timeout: 5000 });
  assert.equal(await alertLocator.count(), 0, 'Başarılı simülasyon sonrası Toast kapanmadı!');
});

test('8. Klavye odağı ve erişilebilirlik (A11y) denetimi', async () => {
  // Re-trigger error to test A11y on visible toast
  await page.unroute('**/api/simulate');
  await page.route('**/api/simulate', async (route) => {
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ success: false, error: 'Erişilebilirlik testi hatası' }),
    });
  });

  const runBtn = page.locator('button:has-text("Simülasyonu Çalıştır")');
  await runBtn.click();

  const alertLocator = page.locator('[role="alert"]');
  await alertLocator.waitFor({ state: 'visible', timeout: 5000 });

  // 1. ARIA Attributes Check
  const role = await alertLocator.getAttribute('role');
  const ariaLive = await alertLocator.getAttribute('aria-live');
  const ariaAtomic = await alertLocator.getAttribute('aria-atomic');

  assert.equal(role, 'alert');
  assert.equal(ariaLive, 'assertive');
  assert.equal(ariaAtomic, 'true');

  // 2. Keyboard Focus on Action Button
  const closeBtn = alertLocator.locator('button[aria-label="Bildirimi kapat"]');
  await closeBtn.focus();

  const isCloseFocused = await closeBtn.evaluate((el) => el === document.activeElement);
  assert.ok(isCloseFocused, 'Kapatma butonu klavye odağı alamadı!');

  // Check focus ring styling
  const classNames = await closeBtn.getAttribute('class');
  assert.ok(classNames.includes('focus:ring-2'), 'Görünür odak halkası (focus:ring-2) eksik!');
});

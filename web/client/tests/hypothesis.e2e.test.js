process.env.NODE_ENV = 'test';

import test from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from 'playwright-core';
import app from '../../server/index.js';

let server;
let browser;
let page;
const PORT = 5094;
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

test('1. Gerçek Chrome: Doğrulama & Hipotez sekmesi açılmalı ve tekil ana başlık doğrulanmalı', { timeout: 30000 }, async () => {
  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });

  // 1. Navbar üzerindeki Doğrulama & Hipotez sekmesine tıkla
  const benchmarkTabBtn = page.locator('nav button', { hasText: 'Doğrulama & Hipotez' });
  await benchmarkTabBtn.waitFor({ state: 'visible', timeout: 5000 });
  await benchmarkTabBtn.click();

  // 2. "Önkayıtlı hipotez desteklenmedi" başlığını bul ve doğrula
  const heading = page.locator('h2', { hasText: 'Önkayıtlı hipotez desteklenmedi' });
  await heading.waitFor({ state: 'visible', timeout: 8000 });
  assert.ok(await heading.isVisible(), 'Ana başlık görünür olmalı');

  // 3. Bildirimin sayfada sadece 1 kez yer aldığını (mükerrer olmadığını) doğrula
  const count = await heading.count();
  assert.equal(count, 1, 'Önkayıtlı hipotez desteklenmedi başlığı tam olarak 1 kez yer almalı (mükerrer olmamalı)');

  // 4. Alt açıklamanın doğruluğunu kontrol et
  const subText = page.locator('text=Önkayıtlı başarı ölçütü karşılanmadı: farkın en az +2 yüzde puan olması');
  assert.ok(await subText.isVisible(), 'Alt açıklama görünür olmalı');
});

test('2. Gerçek Chrome: "H₀ Korundu" ifadesi bulunmamalı ve EDF koşulsuz üstün olarak sunulmamalı', { timeout: 15000 }, async () => {
  const bodyText = await page.innerText('main');

  // 1. "H₀ Korundu" veya "H0 Korundu" ifadesinin bulunmadığını doğrula
  assert.ok(!bodyText.includes('H₀ Korundu'), '"H₀ Korundu" ifadesi bulunmamalı');
  assert.ok(!bodyText.includes('H0 Korundu'), '"H0 Korundu" ifadesi bulunmamalı');

  // 2. "Lider Algoritma" başlığı yerine "Değerlendirme Bulgusu" kullanıldığını doğrula
  assert.ok(!bodyText.includes('Lider Algoritma:'), '"Lider Algoritma:" ifadesi kaldırılmış olmalı');
  assert.ok(bodyText.includes('Değerlendirme Bulgusu:'), '"Değerlendirme Bulgusu:" başlığı yer almalı');

  // 3. EDF'nin koşulsuz kazanan olmadığını, dengeli değerlendirme metnini doğrula
  assert.ok(
    bodyText.includes('Bu değerlendirmede EDF bazı kapasite düzeylerinde yüksek hedef karşılama sonuçları vermiştir'),
    'Dengeli EDF değerlendirme açıklaması bulunmalı'
  );
  assert.ok(
    !bodyText.includes('EDF tüm kısıt düzeylerinde en yüksek başarıyı elde etmiştir'),
    'Koşulsuz üstünlük iddiası yer almamalı'
  );
});

test('3. Gerçek Chrome: Örneklem mutabakatı (5.315, 5.207, 108 ve 11.911) doğrulanmalı', { timeout: 15000 }, async () => {
  const bodyText = await page.innerText('main');

  // 1. Doğrulama oturumu
  assert.ok(bodyText.includes('5.315'), '5.315 doğrulama oturumu sayısı bulunmalı');

  // 2. Simülasyon oturumu
  assert.ok(bodyText.includes('5.207'), '5.207 simülasyon oturumu sayısı bulunmalı');

  // 3. Protokol filtresi farkı
  assert.ok(bodyText.includes('108'), '108 protokol filtresi farkı bulunmalı');

  // 4. Dönemler arası test kümesi (11.911 oturum, 148 gün)
  assert.ok(bodyText.includes('11.911'), '11.911 test oturumu sayısı bulunmalı');
  assert.ok(bodyText.includes('148'), '148 gün sayısı bulunmalı');

  // 5. Veri kaybı değil protokol filtresi olduğu açıklaması
  assert.ok(
    bodyText.includes('Bu durum bir veri kaybı değil') || bodyText.includes('108 oturumluk fark veri kaybı değil'),
    'Protokol filtresi gerekçesi açıklanmış olmalı'
  );
});

test('4. Gerçek Chrome: Keşifsel EDF satırı (+0,38 y.p.) ile önkayıtlı ana hipotez kararı ayrılmalı ve Olası Açıklama dili kullanılmalı', { timeout: 15000 }, async () => {
  const bodyText = await page.innerText('main');

  // 1. Önkayıtlı ana hipotez satırları için açık etiket
  assert.ok(
    bodyText.includes('Önkayıtlı Hipotez Desteklenmedi'),
    'Ana hipotez satırları "Önkayıtlı Hipotez Desteklenmedi" olarak etiketlenmeli'
  );

  // 2. f=0.9 EDF (+0,38 y.p.) keşifsel satırı için "Keşifsel bulgu" etiketi
  assert.ok(
    bodyText.includes('Keşifsel bulgu (GA > 0; ana hipotez dışı)'),
    'Güven aralığı sıfırın üzerinde olan keşifsel EDF satırı "Keşifsel bulgu (GA > 0; ana hipotez dışı)" olarak ayrılmalı'
  );

  // 3. Kesin "Fiziksel Mekanizma:" yerine "Gözlenen Davranış İçin Olası Açıklama (Çalışma Hipotezi):" kullanılmalı
  assert.ok(
    !bodyText.includes('Fiziksel Mekanizma:'),
    'Kesin nedensellik ima eden "Fiziksel Mekanizma:" başlığı kaldırılmış olmalı'
  );
  assert.ok(
    bodyText.includes('Gözlenen Davranış İçin Olası Açıklama (Çalışma Hipotezi):'),
    '"Gözlenen Davranış İçin Olası Açıklama (Çalışma Hipotezi):" başlığı yer almalı'
  );
});

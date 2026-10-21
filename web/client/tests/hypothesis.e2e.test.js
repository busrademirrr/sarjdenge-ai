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

test('1. Ger├ğek Chrome: Do─şrulama & Hipotez sekmesi a├ğ─▒lmal─▒ ve tekil ana ba┼şl─▒k do─şrulanmal─▒', { timeout: 30000 }, async () => {
  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });

  // 1. Navbar ├╝zerindeki Do─şrulama & Hipotez sekmesine t─▒kla
  const benchmarkTabBtn = page.locator('nav button', { hasText: 'Do─şrulama & Hipotez' });
  await benchmarkTabBtn.waitFor({ state: 'visible', timeout: 5000 });
  await benchmarkTabBtn.click();

  // 2. "├ûnkay─▒tl─▒ hipotez desteklenmedi" ba┼şl─▒─ş─▒n─▒ bul ve do─şrula
  const heading = page.locator('h2', { hasText: '├ûnkay─▒tl─▒ hipotez desteklenmedi' });
  await heading.waitFor({ state: 'visible', timeout: 8000 });
  assert.ok(await heading.isVisible(), 'Ana ba┼şl─▒k g├Âr├╝n├╝r olmal─▒');

  // 3. Bildirimin sayfada sadece 1 kez yer ald─▒─ş─▒n─▒ (m├╝kerrer olmad─▒─ş─▒n─▒) do─şrula
  const count = await heading.count();
  assert.equal(count, 1, '├ûnkay─▒tl─▒ hipotez desteklenmedi ba┼şl─▒─ş─▒ tam olarak 1 kez yer almal─▒ (m├╝kerrer olmamal─▒)');

  // 4. Alt a├ğ─▒klaman─▒n do─şrulu─şunu kontrol et
  const subText = page.locator('text=├ûnkay─▒tl─▒ ba┼şar─▒ ├Âl├ğ├╝t├╝ kar┼ş─▒lanmad─▒: fark─▒n en az +2 y├╝zde puan olmas─▒');
  assert.ok(await subText.isVisible(), 'Alt a├ğ─▒klama g├Âr├╝n├╝r olmal─▒');
});

test('2. Ger├ğek Chrome: "HÔéÇ Korundu" ifadesi bulunmamal─▒ ve EDF ko┼şulsuz ├╝st├╝n olarak sunulmamal─▒', { timeout: 15000 }, async () => {
  const bodyText = await page.innerText('main');

  // 1. "HÔéÇ Korundu" veya "H0 Korundu" ifadesinin bulunmad─▒─ş─▒n─▒ do─şrula
  assert.ok(!bodyText.includes('HÔéÇ Korundu'), '"HÔéÇ Korundu" ifadesi bulunmamal─▒');
  assert.ok(!bodyText.includes('H0 Korundu'), '"H0 Korundu" ifadesi bulunmamal─▒');

  // 2. "Lider Algoritma" ba┼şl─▒─ş─▒ yerine "De─şerlendirme Bulgusu" kullan─▒ld─▒─ş─▒n─▒ do─şrula
  assert.ok(!bodyText.includes('Lider Algoritma:'), '"Lider Algoritma:" ifadesi kald─▒r─▒lm─▒┼ş olmal─▒');
  assert.ok(bodyText.includes('De─şerlendirme Bulgusu:'), '"De─şerlendirme Bulgusu:" ba┼şl─▒─ş─▒ yer almal─▒');

  // 3. EDF'nin ko┼şulsuz kazanan olmad─▒─ş─▒n─▒, dengeli de─şerlendirme metnini do─şrula
  assert.ok(
    bodyText.includes('Bu de─şerlendirmede EDF baz─▒ kapasite d├╝zeylerinde y├╝ksek hedef kar┼ş─▒lama sonu├ğlar─▒ vermi┼ştir'),
    'Dengeli EDF de─şerlendirme a├ğ─▒klamas─▒ bulunmal─▒'
  );
  assert.ok(
    !bodyText.includes('EDF t├╝m k─▒s─▒t d├╝zeylerinde en y├╝ksek ba┼şar─▒y─▒ elde etmi┼ştir'),
    'Ko┼şulsuz ├╝st├╝nl├╝k iddias─▒ yer almamal─▒'
  );
});

test('3. Ger├ğek Chrome: ├ûrneklem mutabakat─▒ (5.315, 5.207, 108 ve 11.911) do─şrulanmal─▒', { timeout: 15000 }, async () => {
  const bodyText = await page.innerText('main');

  // 1. Do─şrulama oturumu
  assert.ok(bodyText.includes('5.315'), '5.315 do─şrulama oturumu say─▒s─▒ bulunmal─▒');

  // 2. Sim├╝lasyon oturumu
  assert.ok(bodyText.includes('5.207'), '5.207 sim├╝lasyon oturumu say─▒s─▒ bulunmal─▒');

  // 3. Protokol filtresi fark─▒
  assert.ok(bodyText.includes('108'), '108 protokol filtresi fark─▒ bulunmal─▒');

  // 4. D├Ânemler aras─▒ test k├╝mesi (11.911 oturum, 148 g├╝n)
  assert.ok(bodyText.includes('11.911'), '11.911 test oturumu say─▒s─▒ bulunmal─▒');
  assert.ok(bodyText.includes('148'), '148 g├╝n say─▒s─▒ bulunmal─▒');

  // 5. Veri kayb─▒ de─şil protokol filtresi oldu─şu a├ğ─▒klamas─▒
  assert.ok(
    bodyText.includes('Bu durum bir veri kayb─▒ de─şil') || bodyText.includes('108 oturumluk fark veri kayb─▒ de─şil'),
    'Protokol filtresi gerek├ğesi a├ğ─▒klanm─▒┼ş olmal─▒'
  );
});

test('4. Ger├ğek Chrome: Ke┼şifsel EDF sat─▒r─▒ (+0,38 y.p.) ile ├Ânkay─▒tl─▒ ana hipotez karar─▒ ayr─▒lmal─▒ ve Olas─▒ A├ğ─▒klama dili kullan─▒lmal─▒', { timeout: 15000 }, async () => {
  const bodyText = await page.innerText('main');

  // 1. ├ûnkay─▒tl─▒ ana hipotez sat─▒rlar─▒ i├ğin a├ğ─▒k etiket
  assert.ok(
    bodyText.includes('├ûnkay─▒tl─▒ Hipotez Desteklenmedi'),
    'Ana hipotez sat─▒rlar─▒ "├ûnkay─▒tl─▒ Hipotez Desteklenmedi" olarak etiketlenmeli'
  );

  // 2. f=0.9 EDF (+0,38 y.p.) ke┼şifsel sat─▒r─▒ i├ğin "Ke┼şifsel bulgu" etiketi
  assert.ok(
    bodyText.includes('Ke┼şifsel bulgu (GA > 0; ana hipotez d─▒┼ş─▒)'),
    'G├╝ven aral─▒─ş─▒ s─▒f─▒r─▒n ├╝zerinde olan ke┼şifsel EDF sat─▒r─▒ "Ke┼şifsel bulgu (GA > 0; ana hipotez d─▒┼ş─▒)" olarak ayr─▒lmal─▒'
  );

  // 3. Kesin "Fiziksel Mekanizma:" yerine "G├Âzlenen Davran─▒┼ş ─░├ğin Olas─▒ A├ğ─▒klama (├çal─▒┼şma Hipotezi):" kullan─▒lmal─▒
  assert.ok(
    !bodyText.includes('Fiziksel Mekanizma:'),
    'Kesin nedensellik ima eden "Fiziksel Mekanizma:" ba┼şl─▒─ş─▒ kald─▒r─▒lm─▒┼ş olmal─▒'
  );
  assert.ok(
    bodyText.includes('G├Âzlenen Davran─▒┼ş ─░├ğin Olas─▒ A├ğ─▒klama (├çal─▒┼şma Hipotezi):'),
    '"G├Âzlenen Davran─▒┼ş ─░├ğin Olas─▒ A├ğ─▒klama (├çal─▒┼şma Hipotezi):" ba┼şl─▒─ş─▒ yer almal─▒'
  );
});

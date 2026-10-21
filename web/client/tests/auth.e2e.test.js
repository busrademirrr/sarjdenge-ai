process.env.NODE_ENV = 'test';

import test from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from 'playwright-core';
import app from '../../server/index.js';
import { getInitials } from '../src/lib/supabaseClient.js';

let server;
let browser;
let page;
const PORT = 5092;
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

test('1. Birim Testi: ─░ki harfli profil avatar ├╝retimi do─şrulanmal─▒', () => {
  assert.equal(getInitials('B├╝┼şra Demir'), 'BD', 'B├╝┼şra Demir -> BD olmal─▒');
  assert.equal(getInitials('Can Kurtulu┼ş Kaya'), 'CK', 'Can Kurtulu┼ş Kaya -> CK olmal─▒');
  assert.equal(getInitials('Ahmet'), 'AH', 'Ahmet -> AH olmal─▒');
  assert.equal(getInitials('', 'ahmet@climathon.org'), 'AH', '─░sim yoksa email ahmet -> AH olmal─▒');
  assert.equal(getInitials(null, 'info@sarjdenge.ai'), 'IN', '─░sim null ise email info -> IN olmal─▒');
});

test('2. Ger├ğek Chrome: Navbar Giri┼ş Yap butonu ile AuthModal a├ğ─▒lmal─▒ ve sekmeler aras─▒ ge├ği┼ş ├ğal─▒┼şmal─▒', { timeout: 30000 }, async () => {
  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });

  // 1. Navbar'daki "Giri┼ş Yap" butonuna t─▒kla
  const loginBtn = page.locator('header button:has-text("Giri┼ş Yap")').first();
  await loginBtn.waitFor({ state: 'visible', timeout: 5000 });
  await loginBtn.click();

  // 2. Modal─▒n a├ğ─▒ld─▒─ş─▒n─▒ do─şrula
  const modalHeading = page.locator('h3:has-text("┼ŞarjDenge AI")');
  await modalHeading.waitFor({ state: 'visible', timeout: 3000 });
  assert.ok(await modalHeading.isVisible(), 'Auth modal─▒ ba┼şl─▒─ş─▒ g├Âr├╝n├╝r olmal─▒');

  // 3. Varsay─▒lan olarak "Giri┼ş Yap" sekmesinin aktif oldu─şunu do─şrula
  const signInSubmitBtn = page.locator('button[type="submit"]:has-text("Giri┼ş Yap")');
  assert.ok(await signInSubmitBtn.isVisible(), 'Giri┼ş Yap butonu g├Âr├╝n├╝r olmal─▒');

  // 4. "Hesap Olu┼ştur" sekmesine ge├ğ
  const signUpTabBtn = page.locator('button:has-text("Hesap Olu┼ştur")').first();
  await signUpTabBtn.click();

  const fullNameInput = page.locator('input[placeholder="B├╝┼şra Demir"]');
  await fullNameInput.waitFor({ state: 'visible', timeout: 2000 });
  assert.ok(await fullNameInput.isVisible(), 'Ad Soyad alan─▒ g├Âr├╝n├╝r olmal─▒');
});

test('3. Ger├ğek Chrome: Kay─▒t formunda ┼şifre e┼şle┼şmeme ve k─▒sa ┼şifre validasyonu', { timeout: 20000 }, async () => {
  // 1. K─▒sa ┼şifre kontrol├╝ (< 6 karakter)
  await page.fill('input[placeholder="B├╝┼şra Demir"]', 'Deneme Kullan─▒c─▒');
  await page.fill('input[placeholder="busra.demir@sirket.com"]', 'deneme@sarjdenge.ai');
  const passwordInputs = await page.locator('input[placeholder="ÔÇóÔÇóÔÇóÔÇóÔÇóÔÇóÔÇóÔÇó"]').all();
  assert.ok(passwordInputs.length >= 2, '┼Şifre ve ┼şifre tekrar─▒ inputlar─▒ bulunmal─▒');

  await passwordInputs[0].fill('123');
  await passwordInputs[1].fill('123');

  const submitBtn = page.locator('button[type="submit"]:has-text("Hesap Olu┼ştur")');
  await submitBtn.click();

  const errorAlert = page.locator('[role="alert"]');
  await errorAlert.waitFor({ state: 'visible', timeout: 3000 });
  let errorText = await errorAlert.innerText();
  assert.ok(errorText.includes('en az 6 karakter'), 'K─▒sa ┼şifre uyar─▒s─▒ g├Âsterilmeli');

  // 2. ┼Şifre e┼şle┼şmeme kontrol├╝
  await passwordInputs[0].fill('123456');
  await passwordInputs[1].fill('654321');
  await submitBtn.click();

  await page.waitForTimeout(200);
  errorText = await errorAlert.innerText();
  assert.ok(errorText.includes('┼şifreler e┼şle┼şmiyor'), 'E┼şle┼şmeyen ┼şifre uyar─▒s─▒ g├Âsterilmeli');
});

test('4. Ger├ğek Chrome: ┼Şifre g├Âster/gizle ikonu ├ğal─▒┼şmal─▒', { timeout: 15000 }, async () => {
  const passwordInput = page.locator('input[placeholder="ÔÇóÔÇóÔÇóÔÇóÔÇóÔÇóÔÇóÔÇó"]').first();
  assert.equal(await passwordInput.getAttribute('type'), 'password', 'Varsay─▒lan type password olmal─▒');

  // G├Âz butonuna t─▒kla
  const eyeBtn = page.locator('button[aria-label="┼Şifreyi g├Âster"]').first();
  await eyeBtn.click();

  assert.equal(await passwordInput.getAttribute('type'), 'text', 'T─▒kland─▒ktan sonra type text olmal─▒');

  // Tekrar t─▒kla (gizle)
  const eyeOffBtn = page.locator('button[aria-label="┼Şifreyi gizle"]').first();
  await eyeOffBtn.click();

  assert.equal(await passwordInput.getAttribute('type'), 'password', 'Tekrar t─▒kland─▒ktan sonra type password olmal─▒');
});

test('5. Ger├ğek Chrome: ┼Şifremi unuttum ak─▒┼ş─▒na ge├ği┼ş ve geri d├Ân├╝┼ş', { timeout: 15000 }, async () => {
  // Giri┼ş Yap sekmesine geri d├Ân (sekme gridi i├ğindeki Giri┼ş Yap butonu)
  const signInTab = page.locator('.grid button:has-text("Giri┼ş Yap")').first();
  await signInTab.click();

  // "┼Şifremi unuttum" ba─şlant─▒s─▒na t─▒kla
  const forgotBtn = page.locator('button:has-text("┼Şifremi unuttum")');
  await forgotBtn.waitFor({ state: 'visible', timeout: 3000 });
  await forgotBtn.click();

  const forgotHeading = page.locator('h4:has-text("┼Şifrenizi mi Unuttunuz?")');
  await forgotHeading.waitFor({ state: 'visible', timeout: 3000 });
  assert.ok(await forgotHeading.isVisible(), '┼Şifremi unuttum ba┼şl─▒─ş─▒ g├Âr├╝nmeli');

  // Geri d├Ân butonu
  const backBtn = page.locator('button:has-text("Giri┼ş Ekran─▒na D├Ân")');
  await backBtn.waitFor({ state: 'visible', timeout: 3000 });
  await backBtn.click();

  const signInHeading = page.locator('button[type="submit"]:has-text("Giri┼ş Yap")');
  await signInHeading.waitFor({ state: 'visible', timeout: 3000 });
  assert.ok(await signInHeading.isVisible(), 'Giri┼ş ekran─▒na d├Ân├╝lm├╝┼ş olmal─▒');
});

test('6. Ger├ğek Chrome: Giri┼ş yapmadan devam et (Misafir / Demo Modu)', { timeout: 15000 }, async () => {
  // Modal a├ğ─▒kken "Giri┼ş yapmadan devam et (Demo Modu)" butonuna t─▒kla
  const guestLink = page.locator('button:has-text("Giri┼ş yapmadan devam et (Demo Modu)")');
  await guestLink.waitFor({ state: 'visible', timeout: 3000 });
  await guestLink.click();

  // Modal─▒n kapand─▒─ş─▒n─▒ do─şrula
  const modalHeading = page.locator('h3:has-text("┼ŞarjDenge AI")');
  await modalHeading.waitFor({ state: 'hidden', timeout: 3000 });
  assert.equal(await modalHeading.count(), 0, 'Modal kapanm─▒┼ş olmal─▒');

  // Sim├╝lasyonun engelsiz ├ğal─▒┼şt─▒─ş─▒n─▒ do─şrula
  const runSimBtn = page.locator('button:has-text("Sim├╝lasyonu ├çal─▒┼şt─▒r"), button:has-text("Sim├╝le EdiliyorÔÇĞ")').first();
  await runSimBtn.waitFor({ state: 'visible', timeout: 5000 });
  assert.ok(await runSimBtn.isVisible(), 'Sim├╝lasyon butonu eri┼şilebilir olmal─▒');
});

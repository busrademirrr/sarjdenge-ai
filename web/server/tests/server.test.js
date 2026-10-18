process.env.NODE_ENV = 'test';
import test from 'node:test';
import assert from 'node:assert/strict';
import app from '../index.js';

let server;
const PORT = 5099;
const BASE_URL = `http://localhost:${PORT}`;

test.before(async () => {
  await new Promise(resolve => {
    server = app.listen(PORT, resolve);
  });
});

test.after(async () => {
  await new Promise(resolve => {
    server.close(resolve);
  });
});

test('GET /api/health returns ok status', async () => {
  const res = await fetch(`${BASE_URL}/api/health`);
  assert.equal(res.status, 200);
  const data = await res.json();
  assert.equal(data.status, 'ok');
});

test('GET /api/scenarios returns scenarios list with labels', async () => {
  const res = await fetch(`${BASE_URL}/api/scenarios`);
  assert.equal(res.status, 200);
  const data = await res.json();
  assert.equal(data.success, true);
  assert.ok(data.scenarios.length >= 4);

  const realScenario = data.scenarios.find(s => s.id === 'acn_gercek_val');
  assert.ok(realScenario);
  assert.equal(realScenario.badgeType, 'real');

  const synScenario = data.scenarios.find(s => s.id === 'isyeri_gunduz');
  assert.ok(synScenario);
  assert.equal(synScenario.badgeType, 'synthetic');
});

test('GET /api/benchmark-results returns verified experiment results', async () => {
  const res = await fetch(`${BASE_URL}/api/benchmark-results`);
  assert.equal(res.status, 200);
  const data = await res.json();
  assert.equal(data.success, true);
  assert.ok(data.valTable.length > 0);
  assert.ok(data.bootVal.length > 0);
  assert.equal(data.primaryHypothesis.desteklendi_mi, false);
  assert.equal(data.reconciliation.wpC_dogrulama_oturum, 5315);
  assert.equal(data.reconciliation.wpD_simulasyon_oturum, 5207);
  assert.equal(data.reconciliation.dislanan_oturum_sayisi, 108);
});

test('Auth flow: Guest mode default and Google login simulation', async () => {
  // 1. Status check
  const statusRes = await fetch(`${BASE_URL}/api/auth/status`);
  const statusData = await statusRes.json();
  assert.equal(statusData.session.isAuthenticated, true);
  assert.equal(statusData.session.isGuest, true);

  // 2. Google simulation
  const loginRes = await fetch(`${BASE_URL}/api/auth/google`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      mockUser: { name: 'Prof. Dr. Jüri', email: 'juri.prof@climathon.org' },
    }),
  });
  const loginData = await loginRes.json();
  assert.equal(loginData.success, true);
  assert.equal(loginData.session.isGuest, false);
  assert.equal(loginData.session.user.name, 'Prof. Dr. Jüri');

  // 3. Logout back to guest
  const logoutRes = await fetch(`${BASE_URL}/api/auth/logout`, { method: 'POST' });
  const logoutData = await logoutRes.json();
  assert.equal(logoutData.session.isGuest, true);
});

test('POST /api/export/csv exports formatted csv with UTF-8 BOM', async () => {
  const mockSim = {
    senaryo_id: 'isyeri_gunduz',
    tarih: '2026-03-10',
    araclar: [
      {
        arac_id: 'EV-001',
        kullanici_id: 'U-1',
        giris_saat: '08:00',
        ayril_saat: '17:00',
        beyan_ayril_saat: '17:30',
        sure_gercek_dk: 540,
        sure_beyan_dk: 570,
        sure_tahmin_q20_dk: 480,
        talep_gercek_kwh: 12.5,
        talep_beyan_kwh: 15.0,
        tahmin_kwh_q80: 14.2,
        erken_ayrildi: false,
        teslim_kwh: { fcfs_beyan: 12.5, edf_beyan: 12.5, mpc_tahmin_guvenli: 12.5 },
        doyum_orani: { fcfs_beyan: 1.0, edf_beyan: 1.0, mpc_tahmin_guvenli: 1.0 },
        neden_analizi: { ozet_hukum: 'Normal Planlı Şarj Tamamlandı' },
      },
    ],
  };

  const res = await fetch(`${BASE_URL}/api/export/csv`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ simulation: mockSim }),
  });

  assert.equal(res.status, 200);
  const text = await res.text();
  assert.ok(text.includes('arac_id'));
  assert.ok(text.includes('EV-001'));
  assert.ok(text.includes('Normal Planlı Şarj Tamamlandı'));
});

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

test('POST /api/capacity-advisor returns valid 4-method analysis', { timeout: 25000 }, async () => {
  const res = await fetch(`${BASE_URL}/api/capacity-advisor`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenarioId: 'isyeri_gunduz', day: '2026-03-10' }),
  });

  assert.equal(res.status, 200);
  const data = await res.json();
  assert.equal(data.success, true);
  assert.ok(data.advisor);
  assert.equal(data.advisor.sentetik_mi, true);
  assert.equal(data.advisor.arac_sayisi, 23);
  assert.ok(data.advisor.yontemler.length >= 4);

  const yontemKodlari = data.advisor.yontemler.map(y => y.kod);
  assert.ok(yontemKodlari.includes('fcfs'));
  assert.ok(yontemKodlari.includes('edf'));
  assert.ok(yontemKodlari.includes('esit'));
  assert.ok(yontemKodlari.includes('mpc'));
});

test('POST /api/capacity-advisor runs multi-day analysis without timing out and returns distributions', { timeout: 90000 }, async () => {
  const res = await fetch(`${BASE_URL}/api/capacity-advisor`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenarioId: 'isyeri_gunduz', day: '2026-03-10', multiDay: true }),
  });

  assert.equal(res.status, 200);
  const data = await res.json();
  assert.equal(data.success, true);
  assert.ok(data.advisor);
  assert.ok(data.advisor.cok_gunlu_analiz);
  assert.equal(data.advisor.cok_gunlu_analiz.toplam_gun, 20);
  assert.equal(data.advisor.cok_gunlu_analiz.hedef_gun_sayisi, 20);
  assert.equal(data.advisor.cok_gunlu_analiz.yontemler.length, 4);

  for (const y of data.advisor.cok_gunlu_analiz.yontemler) {
    assert.ok(y.medyan_kw !== null);
    assert.ok(y.orneklem_sayisi > 0);
  }
});

test('POST /api/simulate runs end-to-end simulation with all algorithm families', { timeout: 25000 }, async () => {
  const res = await fetch(`${BASE_URL}/api/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenarioId: 'isyeri_gunduz', f: 0.5, day: '2026-03-10' }),
  });

  assert.equal(res.status, 200);
  const data = await res.json();
  assert.equal(data.success, true);
  assert.ok(data.simulation);
  assert.ok(data.simulation.arac_sayisi > 0);
  assert.ok(data.simulation.kontrolsuz_profil_kw.length >= 96);

  // Sentetik senaryoda yalnızca geçerli beyan yöntemleri bulunur ve kuantil notu yer alır
  for (const key of ['fcfs_beyan', 'esit_beyan', 'edf_beyan', 'mpc_beyan']) {
    assert.ok(data.simulation.yontem_profilleri[key], `Missing profile for ${key}`);
    assert.ok(data.simulation.kpi_ozet[key], `Missing KPI for ${key}`);
    assert.equal(data.simulation.kpi_ozet[key].kapasite_ihlali_kw, 0);
  }
  assert.ok(data.simulation.kuantil_kalibrasyon_notu);
});

test('POST /api/simulate rejects invalid parameters and empty date gracefully', { timeout: 20000 }, async () => {
  const badFRes = await fetch(`${BASE_URL}/api/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenarioId: 'isyeri_gunduz', f: -0.5 }),
  });
  assert.equal(badFRes.status, 400);
  const badFData = await badFRes.json();
  assert.equal(badFData.success, false);

  const emptyDateRes = await fetch(`${BASE_URL}/api/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenarioId: 'acn_gercek_val', f: 0.5, day: '2099-01-01' }),
  });
  assert.equal(emptyDateRes.status, 422);
  const emptyDateData = await emptyDateRes.json();
  assert.equal(emptyDateData.success, false);
  assert.ok(emptyDateData.error);
});



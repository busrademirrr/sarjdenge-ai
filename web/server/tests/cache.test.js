import assert from 'node:assert/strict';
import { executeWithCacheAndSingleFlight, lruCache, normalizeKey } from '../utils/calculationCache.js';

async function testCacheAndSingleFlight() {
  lruCache.clear();
  console.log('Testing LRU Cache & Single-Flight...');

  let computationCount = 0;
  const mockCompute = async (id) => {
    computationCount++;
    await new Promise(r => setTimeout(r, 200)); // 200ms yapay gecikme
    return { id, result: 42, count: computationCount };
  };

  const params = { scenarioId: 'isyeri_gunduz', f: 0.5, day: '2026-03-10' };

  // 1. Single-Flight Test: 3 eşzamanlı istek aynı anda gönderiliyor
  const t0 = Date.now();
  const [res1, res2, res3] = await Promise.all([
    executeWithCacheAndSingleFlight('simulate', params, () => mockCompute('req1')),
    executeWithCacheAndSingleFlight('simulate', params, () => mockCompute('req2')),
    executeWithCacheAndSingleFlight('simulate', params, () => mockCompute('req3')),
  ]);
  const singleFlightDuration = Date.now() - t0;

  console.log(`Single-Flight tamamlandı (${singleFlightDuration}ms). Gerçek hesaplama sayısı: ${computationCount}`);
  assert.equal(computationCount, 1, 'Eşzamanlı 3 istek yalnızca 1 kez hesaplanmalı');
  assert.equal(res1.data.result, 42);
  assert.equal(res2.data.result, 42);
  assert.equal(res3.data.result, 42);

  // 2. Cache Hit Test: Ardışık istek önbellekten dönmeli
  const t1 = Date.now();
  const resCache = await executeWithCacheAndSingleFlight('simulate', params, () => mockCompute('req4'));
  const cacheDuration = Date.now() - t1;

  console.log(`Cache Hit süresi: ${cacheDuration}ms (Kaynak: ${resCache.source})`);
  assert.equal(resCache.source, 'cache', 'Önbellekten dönmeli');
  assert.equal(computationCount, 1, 'Hesaplama sayısı artmamalı');
  assert.ok(cacheDuration < 5, 'Önbellek 5ms altında yanıt vermeli');

  console.log('✅ LRU Cache & Single-Flight testleri %100 BAŞARILI!');
}

testCacheAndSingleFlight().catch(err => {
  console.error('Test hatası:', err);
  process.exit(1);
});

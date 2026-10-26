/**
 * ŞarjDenge AI — Bellek İçi LRU Önbellek ve Single-Flight (Eşzamanlı İstek Birleştirici)
 *
 * Render Free planında CPU kısıtlı olduğundan:
 * 1. Aynı parametrelerle gelen istekler LRU önbellekten (max 30 kayıt) 1 ms içinde döner.
 * 2. Aynı anda gelen özdeş istekler tek bir Python hesabını paylaşır (Single-Flight).
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const precomputedPath = path.join(__dirname, 'precomputed_data.json');

class LRUCache {
  constructor(maxEntries = 100) {
    this.maxEntries = maxEntries;
    this.cache = new Map();
  }

  get(key) {
    if (!this.cache.has(key)) return null;
    const value = this.cache.get(key);
    // LRU tazeleme: Silip sona ekleyerek en son kullanılan yap
    this.cache.delete(key);
    this.cache.set(key, value);
    return value;
  }

  set(key, value) {
    if (this.cache.has(key)) {
      this.cache.delete(key);
    } else if (this.cache.size >= this.maxEntries) {
      // En eski (ilk) kaydı temizle
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }
    this.cache.set(key, value);
  }

  has(key) {
    return this.cache.has(key);
  }

  clear() {
    this.cache.clear();
  }

  get size() {
    return this.cache.size;
  }
}

export const lruCache = new LRUCache(30);
const inFlightRequests = new Map();

/**
 * İstek gövdesini ve rotayı deterministik anahtara dönüştürür
 */
export function normalizeKey(route, body = {}) {
  if (route === 'simulate') {
    const scId = String(body.scenarioId || 'isyeri_gunduz').trim();
    const f = Number(body.f !== undefined ? body.f : 0.5).toFixed(2);
    const cap = body.capKw ? Number(body.capKw).toFixed(1) : '';
    const day = body.day ? String(body.day).trim() : '';
    const seed = Number(body.seed || 42);
    return `sim:${scId}:${f}:${cap}:${day}:${seed}`;
  }

  if (route === 'capacityAdvisor') {
    const scId = String(body.scenarioId || 'isyeri_gunduz').trim();
    const day = body.day ? String(body.day).trim() : '';
    const seed = Number(body.seed || 42);
    const multiDay = Boolean(body.multiDay);
    return `adv:${scId}:${day}:${seed}:${multiDay}`;
  }

  return `${route}:${JSON.stringify(body)}`;
}

// Sunucu başlangıcında önceden hesaplanmış tüm varsayılan senaryoları önbelleğe yükle
try {
  if (fs.existsSync(precomputedPath)) {
    const raw = fs.readFileSync(precomputedPath, 'utf-8');
    const preData = JSON.parse(raw);
    if (preData.advisor) {
      for (const [k, val] of Object.entries(preData.advisor)) {
        const parts = k.split('_');
        const multiDay = parts[parts.length - 1] === 'true';
        const day = parts[parts.length - 2];
        const scId = parts.slice(0, parts.length - 2).join('_');

        const keyWithDay = normalizeKey('capacityAdvisor', { scenarioId: scId, day, seed: 42, multiDay });
        const keyNoDay = normalizeKey('capacityAdvisor', { scenarioId: scId, day: '', seed: 42, multiDay });
        lruCache.set(keyWithDay, val);
        lruCache.set(keyNoDay, val);
      }
    }
    if (preData.simulation) {
      for (const [k, val] of Object.entries(preData.simulation)) {
        const parts = k.split('_');
        const day = parts[parts.length - 1];
        const scId = parts.slice(0, parts.length - 2).join('_');

        const keyWithDay = normalizeKey('simulate', { scenarioId: scId, f: 0.5, day, seed: 42 });
        const keyNoDay = normalizeKey('simulate', { scenarioId: scId, f: 0.5, day: '', seed: 42 });
        lruCache.set(keyWithDay, val);
        lruCache.set(keyNoDay, val);
      }
    }
    console.log(`[Cache] ${lruCache.size} adet önceden hesaplanmış senaryo hazır önbelleğe yüklendi.`);
  }
} catch (e) {
  console.warn('[Cache] Önceden hesaplanmış veri yüklenirken uyarı:', e.message);
}

/**
 * Önbellek kontrolü ve Single-Flight yürütme
 */
export async function executeWithCacheAndSingleFlight(route, body, calculationFn) {
  const key = normalizeKey(route, body);

  // 1. LRU Önbellek Kontrolü
  const cached = lruCache.get(key);
  if (cached) {
    return { data: cached, source: 'cache', key };
  }

  // 2. Single-Flight (Aynı hesaplama şu an yürütülüyorsa ona bağlan)
  if (inFlightRequests.has(key)) {
    const sharedResult = await inFlightRequests.get(key);
    return { data: sharedResult, source: 'single-flight', key };
  }

  // 3. Yeni Hesaplama Başlat
  const computationPromise = (async () => {
    try {
      const result = await calculationFn();
      if (result && !result.hata) {
        lruCache.set(key, result);
      }
      return result;
    } finally {
      inFlightRequests.delete(key);
    }
  })();

  inFlightRequests.set(key, computationPromise);
  const result = await computationPromise;
  return { data: result, source: 'computed', key };
}

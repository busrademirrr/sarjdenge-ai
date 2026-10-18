/**
 * ŞarjDenge AI - Sayı, Yüzde, Güç ve Zaman Biçimlendirme Yardımcıları
 * Standart: Türkçe sayı biçimi (ondalık virgül, binlik nokta), 
 * yüzdelerde "95,7%" gösterimi, sürelerde "+1 gün" taşma desteği.
 */

/**
 * Yüzde oranını biçimlendirir. Örn: 95.72 -> "95,7%"
 * @param {number|null|undefined} val - Yüzde değeri (0-100 veya oran)
 * @param {number} decimals - Ondalık basamak sayısı
 * @param {boolean} isFraction - Eğer değer 0-1 arasındaysa true geçilir
 */
export function formatPercent(val, decimals = 1, isFraction = false) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  const num = isFraction ? Number(val) * 100 : Number(val);
  const formatted = num.toFixed(decimals).replace('.', ',');
  return `${formatted}%`;
}

/**
 * Yüzde puanı (fark) biçimlendirir. Örn: -0.58 -> "-0,58 y.p." veya "+0,22 y.p."
 * @param {number|null|undefined} val - Yüzde puanı farkı
 * @param {number} decimals - Ondalık basamak sayısı
 * @param {boolean} withSign - Pozitif değerlere '+' eklesin mi
 */
export function formatYp(val, decimals = 2, withSign = true) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  const num = Number(val);
  const sign = withSign && num > 0 ? '+' : '';
  const formatted = num.toFixed(decimals).replace('.', ',');
  return `${sign}${formatted} y.p.`;
}

/**
 * Güç (kW) biçimlendirir. Örn: 30.21 -> "30,2 kW"
 * @param {number|null|undefined} val - kW değeri
 * @param {number} decimals - Ondalık basamak sayısı
 */
export function formatKw(val, decimals = 1) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  const num = Number(val);
  const formatted = num.toFixed(decimals).replace('.', ',');
  return `${formatted} kW`;
}

/**
 * Enerji (kWh) biçimlendirir. Örn: 14.5 -> "14,5 kWh"
 * @param {number|null|undefined} val - kWh değeri
 * @param {number} decimals - Ondalık basamak sayısı
 */
export function formatKwh(val, decimals = 1) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  const num = Number(val);
  const formatted = num.toFixed(decimals).replace('.', ',');
  return `${formatted} kWh`;
}

/**
 * Binlik ayracı noktalı tam sayı. Örn: 5207 -> "5.207"
 * @param {number|string|null|undefined} val
 */
export function formatNumber(val) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  const num = Math.round(Number(val));
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

/**
 * Süre / saat metnini biçimlendirir.
 * Gece yarısını aşan adımlarda (örn: "29:30" veya "25:15")
 * saat mod 24 alınarak "+1 gün" olarak eklenir. Örn: "29:30" -> "05:30 (+1 gün)"
 * Normal saatler ("08:45") aynen döner.
 * @param {string|null|undefined} timeStr - "HH:MM" biçiminde saat
 */
export function formatTimeHour(timeStr) {
  if (!timeStr || typeof timeStr !== 'string') return '—';
  const parts = timeStr.trim().split(':');
  if (parts.length !== 2) return timeStr;

  const hours = parseInt(parts[0], 10);
  const mins = parts[1];

  if (isNaN(hours)) return timeStr;

  if (hours >= 24) {
    const modHours = hours % 24;
    const days = Math.floor(hours / 24);
    const padded = String(modHours).padStart(2, '0');
    return `${padded}:${mins} (+${days} gün)`;
  }

  return `${String(hours).padStart(2, '0')}:${mins}`;
}

/**
 * Başlangıç ve bitiş saat aralığını biçimlendirir.
 * Örn: ("08:00", "29:30") -> "08:00 – 05:30 (+1 gün)"
 */
export function formatTimeRange(startStr, endStr) {
  const start = formatTimeHour(startStr);
  const end = formatTimeHour(endStr);
  return `${start} – ${end}`;
}

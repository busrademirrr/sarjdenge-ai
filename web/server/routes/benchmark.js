import { Router } from 'express';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const router = Router();
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, '../../..');

function parseCsv(filePath) {
  if (!fs.existsSync(filePath)) {
    return [];
  }
  const content = fs.readFileSync(filePath, 'utf-8').replace(/^\uFEFF/, '');
  const lines = content.trim().split(/\r?\n/).filter(Boolean);
  if (lines.length < 2) return [];

  const headers = lines[0].split(',').map(h => h.trim());
  return lines.slice(1).map(line => {
    const values = line.split(',').map(v => v.trim());
    const row = {};
    headers.forEach((h, i) => {
      const val = values[i];
      if (val === 'True') row[h] = true;
      else if (val === 'False') row[h] = false;
      else if (!isNaN(val) && val !== '') row[h] = Number(val);
      else row[h] = val;
    });
    return row;
  });
}

router.get('/', (req, res) => {
  try {
    const valTablePath = path.join(PROJECT_ROOT, 'data/deney_tablo_val_duzeltilmis.csv');
    const bootValPath = path.join(PROJECT_ROOT, 'data/deney_boot_val_duzeltilmis.csv');
    const taTablePath = path.join(PROJECT_ROOT, 'data/deney_tablo_ta_duzeltilmis.csv');
    const bootTaPath = path.join(PROJECT_ROOT, 'data/deney_boot_ta_duzeltilmis.csv');
    const holdoutTablePath = path.join(PROJECT_ROOT, 'data/holdout_2020_01_02/deney_tablo_holdout_2020_birincil_duzeltilmis.csv');
    const bootHoldoutPath = path.join(PROJECT_ROOT, 'data/holdout_2020_01_02/deney_boot_holdout_2020_birincil_duzeltilmis.csv');

    const valTable = parseCsv(valTablePath);
    const bootVal = parseCsv(bootValPath);
    const taTable = parseCsv(taTablePath);
    const bootTa = parseCsv(bootTaPath);
    const holdoutTable = parseCsv(holdoutTablePath);
    const bootHoldout = parseCsv(bootHoldoutPath);

    const reconciliation = {
      wpC_dogrulama_oturum: 5315,
      wpD_simulasyon_oturum: 5207,
      dislanan_oturum_sayisi: 108,
      dislanma_nedeni: 'Günlük aktif araç sayısı < 8 olan seyrek günler analiz protokolü gereği elenmiştir (min_arac_gunluk=8). Bu günlerde trafo kapasite darboğazı oluşmadığı için algoritmik karşılaştırma anlamsızdır. Bu durum bir veri kaybı değil, protokol filtresidir.',
      val_gun_sayisi: 68,
      ta_gun_sayisi: 148,
      ta_oturum_sayisi: 11911,
      holdout_temiz_oturum: 4072,
      holdout_simulasyon_oturum: 4043,
      holdout_dislanan_oturum: 29,
      holdout_gun_sayisi: 59,
    };

    const primaryHypothesis = {
      ifade: 'Δ = mpc_tahmin_guvenli - mpc_beyan >= +0.02 (+2 yüzde puanı) ve %95 güven aralığı alt ucu > 0',
      desteklendi_mi: false,
      durum: 'Desteklenmedi',
      bulgular: [
        { f: 0.5, fark_yp: -2.22, ci_95: [-2.97, -1.54], sonuc: 'Desteklenmedi (Sıfırın altında)' },
        { f: 0.7, fark_yp: -0.80, ci_95: [-1.32, -0.29], sonuc: 'Desteklenmedi (Sıfırın altında)' },
        { f: 0.9, fark_yp: -0.13, ci_95: [-0.43, 0.12], sonuc: 'Desteklenmedi (Sıfırı kapsar)' },
      ],
      donemler: {
        val: {
          key: 'val',
          ad: 'Doğrulama Kümesi (Val: 2019 H1)',
          kisaAd: 'Val (2019 H1)',
          aralik: 'Ocak – Haziran 2019',
          gun_sayisi: 68,
          oturum_sayisi: 5207,
          desteklendi_mi: false,
          bulgular: [
            { f: 0.5, beyan_basari: 90.93, guvenli_basari: 88.71, fark_yp: -2.22, ci_95: [-2.97, -1.54], sonuc: 'Desteklenmedi' },
            { f: 0.7, beyan_basari: 93.89, guvenli_basari: 93.09, fark_yp: -0.80, ci_95: [-1.32, -0.29], sonuc: 'Desteklenmedi' },
            { f: 0.9, beyan_basari: 95.17, guvenli_basari: 95.04, fark_yp: -0.13, ci_95: [-0.43, 0.12], sonuc: 'Desteklenmedi' },
          ],
        },
        ta: {
          key: 'ta',
          ad: 'Dönemler Arası Test (TA: 2019 H2)',
          kisaAd: 'TA (2019 H2)',
          aralik: 'Temmuz – Aralık 2019',
          gun_sayisi: 148,
          oturum_sayisi: 11911,
          desteklendi_mi: false,
          bulgular: [
            { f: 0.5, beyan_basari: 88.10, guvenli_basari: 86.06, fark_yp: -2.05, ci_95: [-2.55, -1.53], sonuc: 'Desteklenmedi' },
            { f: 0.7, beyan_basari: 90.34, guvenli_basari: 90.31, fark_yp: -0.94, ci_95: [-1.33, -0.53], sonuc: 'Desteklenmedi' },
            { f: 0.9, beyan_basari: 93.78, guvenli_basari: 93.83, fark_yp: -0.19, ci_95: [-0.40, 0.04], sonuc: 'Desteklenmedi' },
          ],
        },
        holdout2020: {
          key: 'holdout2020',
          ad: '2020 Holdout Birincil Değerlendirme',
          kisaAd: '2020 Holdout',
          aralik: 'Ocak – Şubat 2020',
          gun_sayisi: 59,
          oturum_sayisi: 4043,
          desteklendi_mi: false,
          bulgular: [
            { f: 0.5, beyan_basari: 85.04, guvenli_basari: 83.69, fark_yp: -1.35, ci_95: [-2.55, -0.18], sonuc: 'Desteklenmedi' },
            { f: 0.7, beyan_basari: 90.34, guvenli_basari: 90.31, fark_yp: -0.03, ci_95: [-0.89, 0.86], sonuc: 'Desteklenmedi' },
            { f: 0.9, beyan_basari: 93.78, guvenli_basari: 93.83, fark_yp: 0.05, ci_95: [-0.35, 0.53], sonuc: 'Desteklenmedi' },
          ],
        },
      },
      olasi_mekanizma: "Gözlenen davranış için olası açıklama: Güvenli q80 hedefi oturumların yaklaşık %12'sinde (2020 holdout) gerçek ihtiyacın %95'inin altında kalıyor; kullanıcı beyanında bu oran %2,55. Dar kapasitede bu araçlar hedefe ulaşamıyor. Bu, gözlenen farkla uyumlu bir açıklamadır; nedensel olarak kanıtlanmamıştır.",
      degerlendirme_bulgusu: {
        ad: 'EDF (En Erken Termin Önceliği)',
        neden: 'Bu değerlendirmede EDF bazı kapasite düzeylerinde yüksek hedef karşılama sonuçları vermiştir. Algoritmaların performansı kapasite düzeyine ve kullanılan metriğe göre karşılaştırılmalıdır.',
      },
      en_guclu_planlayici: {
        ad: 'EDF (En Erken Termin Önceliği)',
        neden: 'Bu değerlendirmede EDF bazı kapasite düzeylerinde yüksek hedef karşılama sonuçları vermiştir. Algoritmaların performansı kapasite düzeyine ve kullanılan metriğe göre karşılaştırılmalıdır.',
      },
      kesifsel_uyari: 'EDF ve Hibrit MPC karşılaştırmaları keşifsel analizdir; önkayıtlı ana hipotezin kanıtı olarak sunulamaz.',
    };

    res.json({
      success: true,
      valTable,
      bootVal,
      taTable,
      bootTa,
      holdoutTable,
      bootHoldout,
      reconciliation,
      primaryHypothesis,
    });
  } catch (err) {
    console.error('Benchmark results API error:', err);
    res.status(500).json({
      success: false,
      error: 'Doğrulama ve deney sonuçları yüklenirken bir hata oluştu.',
    });
  }
});

export default router;

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
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.trim().split('\n').filter(Boolean);
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
    const valTablePath = path.join(PROJECT_ROOT, 'data/deney_tablo_val.csv');
    const bootValPath = path.join(PROJECT_ROOT, 'data/deney_boot_val.csv');
    const taTablePath = path.join(PROJECT_ROOT, 'data/deney_tablo_ta.csv');

    const valTable = parseCsv(valTablePath);
    const bootVal = parseCsv(bootValPath);
    const taTable = parseCsv(taTablePath);

    const reconciliation = {
      wpC_dogrulama_oturum: 5315,
      wpD_simulasyon_oturum: 5207,
      dislanan_oturum_sayisi: 108,
      dislanma_nedeni: 'G├╝nl├╝k aktif ara├ğ say─▒s─▒ < 8 olan seyrek g├╝nler analiz protokol├╝ gere─şi elenmi┼ştir (min_arac_gunluk=8). Bu g├╝nlerde trafo kapasite darbo─şaz─▒ olu┼şmad─▒─ş─▒ i├ğin algoritmik kar┼ş─▒la┼şt─▒rma anlams─▒zd─▒r. Bu durum bir veri kayb─▒ de─şil, protokol filtresidir.',
      val_gun_sayisi: 68,
      ta_gun_sayisi: 148,
      ta_oturum_sayisi: 11911,
    };

    const primaryHypothesis = {
      ifade: '╬ö = mpc_tahmin_guvenli - mpc_beyan >= +0.02 (+2 y├╝zde puan─▒) ve %95 g├╝ven aral─▒─ş─▒ alt ucu > 0',
      desteklendi_mi: false,
      bulgular: [
        { f: 0.5, fark_yp: -0.17, ci_95: [-0.66, 0.28], sonuc: 'Desteklenmedi (S─▒f─▒r hipotezi reddedilemedi)' },
        { f: 0.7, fark_yp: -0.58, ci_95: [-1.06, -0.10], sonuc: 'Desteklenmedi (Anlaml─▒ d├╝┼ş├╝┼ş)' },
        { f: 0.9, fark_yp: -0.02, ci_95: [-0.22, 0.17], sonuc: 'Desteklenmedi (Fark yok)' },
      ],
      fiziksel_mekanizma: 'G├Âzlenen davran─▒┼ş i├ğin olas─▒ a├ğ─▒klama (Hayalet Kapasite Rezervasyonu ├ğal─▒┼şma hipotezi): Konservatif q80 enerji hedefi ve q20 dar s├╝re tahmini, LP-MPC optimizasyonunun erken ad─▒mlarda kapasiteyi belirli ara├ğlara ay─▒rmas─▒na ve e┼şzamanl─▒ di─şer ara├ğlar─▒n ┼şarj─▒n─▒ geciktirmesine yol a├ğm─▒┼ş olabilir.',
      olasi_mekanizma: 'G├Âzlenen davran─▒┼ş i├ğin olas─▒ a├ğ─▒klama (Hayalet Kapasite Rezervasyonu ├ğal─▒┼şma hipotezi): Konservatif q80 enerji hedefi ve q20 dar s├╝re tahmini, LP-MPC optimizasyonunun erken ad─▒mlarda kapasiteyi belirli ara├ğlara ay─▒rmas─▒na ve e┼şzamanl─▒ di─şer ara├ğlar─▒n ┼şarj─▒n─▒ geciktirmesine yol a├ğm─▒┼ş olabilir.',
      degerlendirme_bulgusu: {
        ad: 'EDF (En Erken Termin ├ûnceli─şi)',
        neden: 'Bu de─şerlendirmede EDF baz─▒ kapasite d├╝zeylerinde y├╝ksek hedef kar┼ş─▒lama sonu├ğlar─▒ vermi┼ştir. Algoritmalar─▒n performans─▒ kapasite d├╝zeyine ve kullan─▒lan metri─şe g├Âre kar┼ş─▒la┼şt─▒r─▒lmal─▒d─▒r.',
      },
      en_guclu_planlayici: {
        ad: 'EDF (En Erken Termin ├ûnceli─şi)',
        neden: 'Bu de─şerlendirmede EDF baz─▒ kapasite d├╝zeylerinde y├╝ksek hedef kar┼ş─▒lama sonu├ğlar─▒ vermi┼ştir. Algoritmalar─▒n performans─▒ kapasite d├╝zeyine ve kullan─▒lan metri─şe g├Âre kar┼ş─▒la┼şt─▒r─▒lmal─▒d─▒r.',
      },
    };

    res.json({
      success: true,
      valTable,
      bootVal,
      taTable,
      reconciliation,
      primaryHypothesis,
    });
  } catch (err) {
    console.error('Benchmark results API error:', err);
    res.status(500).json({
      success: false,
      error: 'Do─şrulama ve deney sonu├ğlar─▒ y├╝klenirken bir hata olu┼ştu.',
    });
  }
});

export default router;

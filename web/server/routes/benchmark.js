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
      dislanma_nedeni: 'Günlük aktif araç sayısı < 8 olan seyrek günler deney protokolü gereği elenmiştir (min_arac_gunluk=8). Bu günlerde trafo kapasite darboğazı oluşmadığı için algoritmik karşılaştırma anlamsızdır.',
      val_gun_sayisi: 68,
      ta_gun_sayisi: 153,
      ta_oturum_sayisi: 11911,
    };

    const primaryHypothesis = {
      ifade: 'Δ = mpc_tahmin_guvenli - mpc_beyan >= +0.02 (+2 yüzde puanı) ve %95 güven aralığı alt ucu > 0',
      desteklendi_mi: false,
      bulgular: [
        { f: 0.5, fark_yp: -0.17, ci_95: [-0.66, 0.28], sonuc: 'Desteklenmedi (H0 korundu)' },
        { f: 0.7, fark_yp: -0.58, ci_95: [-1.06, -0.10], sonuc: 'Desteklenmedi (Anlamlı düşüş)' },
        { f: 0.9, fark_yp: -0.02, ci_95: [-0.22, 0.17], sonuc: 'Desteklenmedi (Fark yok)' },
      ],
      fiziksel_mekanizma: 'Hayalet Kapasite Rezervasyonu (Ghost Capacity Reservation): Konservatif q80 enerji hedefi ve q20 dar süre tahmini, MPC optimizasyonunun gücü gereksiz yere geleceğe kilitlemesine ve eşzamanlı diğer araçları aç bırakmasına yol açmıştır.',
      en_guclu_planlayici: {
        ad: 'EDF (En Erken Termin Önceliği)',
        neden: 'Hayali rezervasyon tutmadan, yaklaşan gerçek/tahmin ayrılış anına göre dinamik güç dağıtarak en yüksek doyum ve adillik oranına (%91.23–%95.25) ulaşmıştır.',
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
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

export default router;

import { Router } from 'express';

const router = Router();

router.post('/csv', (req, res) => {
  const { simulation } = req.body;

  if (!simulation || !simulation.araclar) {
    return res.status(400).json({ success: false, error: 'Dışa aktarılacak simülasyon verisi bulunamadı.' });
  }

  const columns = [
    'arac_id',
    'kullanici_id',
    'giris_saat',
    'ayril_saat',
    'beyan_ayril_saat',
    'sure_gercek_dk',
    'sure_beyan_dk',
    'sure_tahmin_q20_dk',
    'talep_gercek_kwh',
    'talep_beyan_kwh',
    'tahmin_kwh_q80',
    'erken_ayrildi',
    'fcfs_kwh',
    'fcfs_doyum',
    'edf_beyan_kwh',
    'edf_beyan_doyum',
    'edf_guv_kwh',
    'edf_guv_doyum',
    'mpc_beyan_kwh',
    'mpc_beyan_doyum',
    'mpc_guv_kwh',
    'mpc_guv_doyum',
    'mpc_hibrit_kwh',
    'mpc_hibrit_doyum',
    'neden_ozet',
  ];

  const rows = simulation.araclar.map(a => [
    a.arac_id,
    a.kullanici_id,
    a.giris_saat,
    a.ayril_saat,
    a.beyan_ayril_saat,
    a.sure_gercek_dk,
    a.sure_beyan_dk,
    a.sure_tahmin_q20_dk,
    a.talep_gercek_kwh,
    a.talep_beyan_kwh,
    a.tahmin_kwh_q80,
    a.erken_ayrildi ? 'EVET' : 'HAYIR',
    a.teslim_kwh.fcfs_beyan ?? '',
    a.doyum_orani.fcfs_beyan ?? '',
    a.teslim_kwh.edf_beyan ?? '',
    a.doyum_orani.edf_beyan ?? '',
    a.teslim_kwh.edf_tahmin_guvenli ?? '',
    a.doyum_orani.edf_tahmin_guvenli ?? '',
    a.teslim_kwh.mpc_beyan ?? '',
    a.doyum_orani.mpc_beyan ?? '',
    a.teslim_kwh.mpc_tahmin_guvenli ?? '',
    a.doyum_orani.mpc_tahmin_guvenli ?? '',
    a.teslim_kwh.mpc_hibrit_asimetrik ?? '',
    a.doyum_orani.mpc_hibrit_asimetrik ?? '',
    `"${(a.neden_analizi?.ozet_hukum || '').replace(/"/g, '""')}"`,
  ]);

  const csvContent = [columns.join(','), ...rows.map(r => r.join(','))].join('\n');

  res.setHeader('Content-Type', 'text/csv; charset=utf-8');
  res.setHeader('Content-Disposition', `attachment; filename=sarjdenge_${simulation.senaryo_id}_${simulation.tarih}.csv`);
  res.send('\uFEFF' + csvContent); // UTF-8 BOM for Excel compatibility
});

router.post('/json', (req, res) => {
  const { simulation } = req.body;

  if (!simulation) {
    return res.status(400).json({ success: false, error: 'Dışa aktarılacak simülasyon verisi bulunamadı.' });
  }

  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Content-Disposition', `attachment; filename=sarjdenge_${simulation.senaryo_id || 'simulasyon'}.json`);
  res.send(JSON.stringify(simulation, null, 2));
});

export default router;

import React, { useState } from 'react';
import { Database, AlertCircle, TrendingUp, Info, RefreshCw, Calendar, Sparkles } from 'lucide-react';
import { formatPercent, formatYp, formatNumber } from '../utils/formatters.js';
import { BENCHMARK_METHOD_LABELS, BENCHMARK_METHOD_ORDER, ALGORITHM_META } from '../utils/algorithmMeta.js';

export default function BenchmarkView({ benchmarkData, onRetry }) {
  const [selectedPeriod, setSelectedPeriod] = useState('val');
  const [selectedF, setSelectedF] = useState('all');

  if (!benchmarkData) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-600 shadow-2xs">
        <RefreshCw className="w-5 h-5 text-emerald-700 animate-spin mx-auto mb-2.5" />
        <p className="text-xs font-semibold text-slate-800">Doğrulama sonuçları yükleniyor…</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-3 inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-800 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Yenile</span>
          </button>
        )}
      </div>
    );
  }

  const {
    valTable = [],
    bootVal = [],
    taTable = [],
    bootTa = [],
    holdoutTable = [],
    bootHoldout = [],
    reconciliation = {},
    primaryHypothesis = {},
  } = benchmarkData;

  const PERIODS = {
    val: {
      id: 'val',
      ad: 'Doğrulama Kümesi (Val: 2019 H1)',
      kisaAd: 'Val (2019 H1)',
      aralik: 'Ocak – Haziran 2019',
      gunEtiketi: '68 gün-saha',
      gunSayisi: reconciliation?.val_gun_sayisi || 68,
      oturumSayisi: reconciliation?.wpD_simulasyon_oturum || 5207,
      tableData: valTable,
      bootData: bootVal,
      bulgular: primaryHypothesis?.donemler?.val?.bulgular || [
        { f: 0.5, fark_yp: -2.22, ci_95: [-2.97, -1.54], sonuc: 'Desteklenmedi (Sıfırın altında)' },
        { f: 0.7, fark_yp: -0.80, ci_95: [-1.32, -0.29], sonuc: 'Desteklenmedi (Sıfırın altında)' },
        { f: 0.9, fark_yp: -0.13, ci_95: [-0.43, 0.12], sonuc: 'Desteklenmedi (Sıfırı kapsar)' },
      ],
    },
    ta: {
      id: 'ta',
      ad: 'Dönemler Arası Test (TA: 2019 H2)',
      kisaAd: 'TA (2019 H2)',
      aralik: 'Temmuz – Aralık 2019',
      gunEtiketi: '148 gün-saha',
      gunSayisi: reconciliation?.ta_gun_sayisi || 148,
      oturumSayisi: reconciliation?.ta_oturum_sayisi || 11911,
      tableData: taTable,
      bootData: bootTa,
      bulgular: primaryHypothesis?.donemler?.ta?.bulgular || [
        { f: 0.5, fark_yp: -2.05, ci_95: [-2.55, -1.53], sonuc: 'Desteklenmedi (Sıfırın altında)' },
        { f: 0.7, fark_yp: -0.94, ci_95: [-1.33, -0.53], sonuc: 'Desteklenmedi (Sıfırın altında)' },
        { f: 0.9, fark_yp: -0.19, ci_95: [-0.40, 0.04], sonuc: 'Desteklenmedi (Sıfırı kapsar)' },
      ],
    },
    holdout2020: {
      id: 'holdout2020',
      ad: '2020 Holdout Birincil Kümesi (2020 H1)',
      kisaAd: '2020 Holdout',
      aralik: 'Ocak – Şubat 2020',
      gunEtiketi: '108 gün-saha (59 takvim günü), günde ≥4 araç',
      gunSayisi: 108,
      oturumSayisi: reconciliation?.holdout_simulasyon_oturum || 4043,
      tableData: holdoutTable,
      bootData: bootHoldout,
      bulgular: primaryHypothesis?.donemler?.holdout2020?.bulgular || [
        { f: 0.5, fark_yp: -1.35, ci_95: [-2.55, -0.18], sonuc: 'Desteklenmedi (Sıfırın altında)' },
        { f: 0.7, fark_yp: -0.03, ci_95: [-0.89, 0.86], sonuc: 'Desteklenmedi (Sıfırı kapsar)' },
        { f: 0.9, fark_yp: 0.05, ci_95: [-0.35, 0.53], sonuc: 'Desteklenmedi (Sıfırı kapsar)' },
      ],
    },
  };

  const currentPeriod = PERIODS[selectedPeriod] || PERIODS.val;
  const activeBulgular = currentPeriod.bulgular;
  const activeTable = currentPeriod.tableData || [];
  const activeBoot = currentPeriod.bootData || [];

  const filteredRows = activeTable.filter(
    (row) => selectedF === 'all' || String(row.f) === selectedF
  );

  const sortedRows = [...filteredRows].sort((a, b) => {
    if (a.f !== b.f) return Number(a.f) - Number(b.f);
    const orderA = BENCHMARK_METHOD_ORDER.indexOf(a.yontem);
    const orderB = BENCHMARK_METHOD_ORDER.indexOf(b.yontem);
    const idxA = orderA === -1 ? 999 : orderA;
    const idxB = orderB === -1 ? 999 : orderB;
    return idxA - idxB;
  });

  const baslikDetay = ` (${currentPeriod.gunEtiketi}, ${formatNumber(currentPeriod.oturumSayisi)} Oturum)`;

  return (
    <div className="space-y-4">
      {/* 22 Ekim Düzeltme Notu */}
      <div className="bg-blue-50/80 border border-blue-200/90 rounded-xl p-3 sm:p-3.5 text-xs text-blue-900 flex items-center space-x-2.5 shadow-2xs">
        <Info className="w-4 h-4 text-blue-700 shrink-0" />
        <span className="font-medium">
          22 Ekim 2026'da simülasyon girişinde indeksleme hatası bulundu ve düzeltildi; eski sonuçlar korunmuştur, yeniden hesaplanan sonuçlar burada gösterilmektedir.
        </span>
      </div>

      {/* 1. Ana Hipotez Sonucu + Dönem Seçici + 3 Kompakt Kapasite Kartı */}
      <div className="bg-white border border-slate-200/90 rounded-xl p-4 sm:p-5 shadow-2xs">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 rounded-lg bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-700 shrink-0 mt-0.5">
              <AlertCircle className="w-4 h-4 text-rose-600" />
            </div>
            <div>
              <div className="flex items-center space-x-2 flex-wrap">
                <h2 className="text-base sm:text-lg font-bold text-slate-900 leading-snug">
                  Önkayıtlı hipotez desteklenmedi
                </h2>
                <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-200">
                  Desteklenmedi
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                Önkayıtlı başarı ölçütü karşılanmadı: farkın en az +2 yüzde puan olması ve %95 güven aralığının alt sınırının sıfırın üzerinde bulunması gerekiyordu.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap shrink-0">
            <span className="text-xs font-medium text-slate-600 bg-slate-50 px-2.5 py-1 rounded-md border border-slate-200 tabular-nums">
              Ölçüt: Δ ≥ +2,00 y.p.
            </span>
          </div>
        </div>

        {/* Dönem Seçici Butonları */}
        <div className="mt-4 pt-3 border-t border-slate-100">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
            <div className="flex items-center space-x-1.5 text-xs text-slate-700">
              <Calendar className="w-3.5 h-3.5 text-emerald-700 shrink-0" />
              <span className="font-semibold">Değerlendirme Dönemi:</span>
            </div>
            <div className="flex items-center flex-wrap gap-1.5 text-xs">
              {Object.values(PERIODS).map((p) => {
                const isActive = selectedPeriod === p.id;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setSelectedPeriod(p.id)}
                    className={`px-3 py-1.5 rounded-lg border text-xs font-semibold transition tabular-nums flex items-center space-x-1.5 ${
                      isActive
                        ? 'bg-emerald-700 text-white border-emerald-700 shadow-2xs'
                        : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
                    }`}
                  >
                    <span>{p.kisaAd}</span>
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded font-normal ${
                        isActive ? 'bg-emerald-800 text-emerald-100' : 'bg-slate-200/80 text-slate-600'
                      }`}
                    >
                      {p.oturumSayisi.toLocaleString('tr-TR')} oturum
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Aktif dönem: <strong className="text-slate-800 font-medium">{currentPeriod.ad}</strong> ({currentPeriod.aralik}, {currentPeriod.gunEtiketi}, {formatNumber(currentPeriod.oturumSayisi)} Oturum)
          </p>
        </div>

        {/* 3 Kompakt Kapasite Kartı */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3.5 tabular-nums">
          {activeBulgular.map((b) => {
            const altFmt = Number(b.ci_95[0]).toFixed(2).replace('.', ',');
            const ustFmt = Number(b.ci_95[1]).toFixed(2).replace('.', ',');
            const fFmt = String(b.f).replace('.', ',');
            const farkFmt = Number(b.fark_yp).toFixed(2).replace('.', ',');

            return (
              <div
                key={b.f}
                className="p-3.5 rounded-lg bg-slate-50/80 border border-slate-200/90 flex flex-col justify-between"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800">
                    f = {fFmt} Kapasite
                  </span>
                  <span className="text-[11px] text-slate-500">
                    MPC Güvenli − MPC Beyan
                  </span>
                </div>
                <div className="flex items-baseline justify-between mt-2">
                  <span className="text-xs text-slate-500">Ölçülen Fark</span>
                  <span className="text-lg font-bold text-slate-900">
                    {b.fark_yp > 0 ? `+${farkFmt}` : farkFmt} y.p.
                  </span>
                </div>
                <div className="flex items-baseline justify-between mt-1 pt-1.5 border-t border-slate-200/60 text-xs text-slate-500">
                  <span>%95 GA</span>
                  <span className="font-medium text-slate-700">
                    [{altFmt}, {ustFmt}] y.p.
                  </span>
                </div>
                <div className="mt-2 pt-1 border-t border-slate-200/40 flex items-center justify-between text-[11px]">
                  <span className="text-slate-500">Karar:</span>
                  <span className="font-semibold text-rose-700 bg-rose-50 border border-rose-200 px-1.5 py-0.5 rounded text-[10px]">
                    Desteklenmedi
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Erişilebilir "İstatistiksel ayrıntılar" Açılır Bölümü */}
        <details open className="mt-4 pt-3 border-t border-slate-100 group text-xs text-slate-600">
          <summary className="font-semibold text-slate-800 hover:text-emerald-800 cursor-pointer flex items-center justify-between list-none">
            <span className="flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-emerald-700 shrink-0" />
              <span>İstatistiksel ayrıntılar (Bootstrap B = 2.000, Çalışma Hipotezi ve İkincil Bulgular)</span>
            </span>
            <span className="text-lg text-slate-400 group-open:rotate-180 transition-transform inline-block leading-none select-none">▾</span>
          </summary>

          <div className="mt-3 space-y-3 leading-relaxed">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80">
                <strong className="text-slate-800 block mb-0.5">İstatistiksel Karar:</strong>
                <span>
                  Önkayıtlı ölçüt karşılanmadı: f=0,5 ve 0,7'de fark negatif, f=0,9'da sıfırdan ayırt edilemiyor. Eşleştirilmiş gün bazlı bootstrap (B = 2.000) testlerinde önkayıtlı ana hipotez karşılaştırmalarının güven aralıkları sıfırı kapsamakta veya sıfırın altında kalmaktadır.
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80">
                <strong className="text-slate-800 block mb-0.5">Gözlenen Davranış İçin Olası Açıklama (Çalışma Hipotezi):</strong>
                <span>
                  Güvenli q80 hedefi oturumların yaklaşık %12'sinde (2020 holdout) gerçek ihtiyacın %95'inin altında kalıyor; kullanıcı beyanında bu oran %2,55. Dar kapasitede bu araçlar hedefe ulaşamıyor. Bu, gözlenen farkla uyumlu bir açıklamadır; nedensel olarak kanıtlanmamıştır.
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80">
                <strong className="text-slate-800 block mb-0.5">Değerlendirme Bulgusu:</strong>
                <span>
                  Bu değerlendirmede EDF bazı kapasite düzeylerinde yüksek hedef karşılama sonuçları vermiştir. Algoritmaların performansı kapasite düzeyine ve kullanılan metriğe göre karşılaştırılmalıdır.
                </span>
              </div>
            </div>

            <div className="p-2.5 rounded-lg bg-amber-50/70 border border-amber-200/80 text-[11px] text-amber-900 flex items-start space-x-2">
              <Sparkles className="w-3.5 h-3.5 text-amber-700 shrink-0 mt-0.5" />
              <span>
                <strong>Keşifsel Bulgular Bildirimi:</strong> EDF ve Hibrit MPC karşılaştırmaları keşifsel analizdir; önkayıtlı ana hipotezin (MPC Güvenli vs MPC Beyan) kanıtı olarak sunulamaz ve değerlendirilemez.
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs tabular-nums">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-600 bg-slate-50/70">
                    <th className="py-2 px-3 font-semibold">Kapasite (f)</th>
                    <th className="py-2 px-3 font-semibold">Karşılaştırma</th>
                    <th className="py-2 px-3 font-semibold">Protokol Türü</th>
                    <th className="py-2 px-3 text-right font-semibold">Fark (y.p.)</th>
                    <th className="py-2 px-3 text-right font-semibold">%95 Güven Aralığı</th>
                    <th className="py-2 px-3 text-center font-semibold">Durum</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {activeBoot.map((row, i) => {
                    const isHypothesis = row.tur === 'Ana Hipotez';
                    const isEdf = String(row.tur || '').includes('EDF') || String(row.karsilastirma || '').includes('edf');
                    const isHibrit = String(row.tur || '').includes('Keşifsel') || String(row.karsilastirma || '').includes('hibrit');
                    const altNum = Number(row.ci_95_alt_puan);
                    const ustNum = Number(row.ci_95_ust_puan);
                    const altFmt = altNum.toFixed(2).replace('.', ',');
                    const ustFmt = ustNum.toFixed(2).replace('.', ',');

                    let statusLabel = 'Desteklenmedi';
                    let statusClass = 'bg-slate-100 text-slate-700 border-slate-200';

                    if (isHypothesis) {
                      statusLabel = 'Önkayıtlı Hipotez Desteklenmedi';
                      statusClass = 'bg-rose-50 text-rose-800 border-rose-300';
                    } else if (altNum > 0) {
                      statusLabel = 'Keşifsel bulgu (GA > 0; ana hipotez dışı)';
                      statusClass = 'bg-teal-50 text-teal-800 border-teal-200';
                    } else if (isEdf) {
                      statusLabel = ustNum < 0 ? 'Keşifsel EDF (GA < 0)' : 'Keşifsel EDF (GA 0\'ı kapsar)';
                      statusClass = 'bg-blue-50 text-blue-800 border-blue-200';
                    } else if (isHibrit) {
                      statusLabel = ustNum < 0 ? 'Keşifsel Hibrit (GA < 0)' : 'Keşifsel Hibrit (GA 0\'ı kapsar)';
                      statusClass = 'bg-cyan-50 text-cyan-800 border-cyan-200';
                    } else if (ustNum < 0) {
                      statusLabel = 'İkincil (GA < 0)';
                      statusClass = 'bg-amber-50/80 text-amber-800 border-amber-200';
                    } else {
                      statusLabel = 'İkincil (GA 0\'ı kapsar)';
                      statusClass = 'bg-slate-50 text-slate-600 border-slate-200';
                    }

                    return (
                      <tr key={i} className={isHypothesis ? 'bg-slate-50/60 font-semibold' : ''}>
                        <td className="py-2 px-3 text-slate-700">f = {String(row.f).replace('.', ',')}</td>
                        <td className="py-2 px-3 text-slate-900 font-mono">{row.karsilastirma}</td>
                        <td className="py-2 px-3 text-slate-600">{row.tur}</td>
                        <td className="py-2 px-3 text-right font-bold text-slate-900">
                          {formatYp(row.fark_yuzde_puan, 2)}
                        </td>
                        <td className="py-2 px-3 text-right text-slate-700">
                          [{altFmt}, {ustFmt}] y.p.
                        </td>
                        <td className="py-2 px-3 text-center">
                          <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold border ${statusClass}`}>
                            {statusLabel}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </details>
      </div>

      {/* 2. Kısa ve Sade Örneklem & Veri Akışı Özeti */}
      <div className="bg-white border border-slate-200/90 rounded-xl p-4 shadow-2xs">
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center space-x-2">
            <Info className="w-4 h-4 text-emerald-700 shrink-0" />
            <h3 className="font-bold text-sm text-slate-900">
              Örneklem ve Veri Akışı Özeti
            </h3>
          </div>
          <span className="text-[11px] text-slate-500">
            Protokol: min_arac_gunluk = 8
          </span>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-xs tabular-nums">
          <div className="p-3 rounded-lg bg-slate-50/80 border border-slate-200/80">
            <span className="text-slate-500 block text-[11px]">Doğrulama Kümesi (2019 H1)</span>
            <span className="text-base font-bold text-slate-900 mt-0.5 block">
              {formatNumber(reconciliation.wpC_dogrulama_oturum || 5315)} oturum
            </span>
          </div>
          <div className="p-3 rounded-lg bg-slate-50/80 border border-slate-200/80">
            <span className="text-slate-500 block text-[11px]">Simülasyon (68 gün-saha)</span>
            <span className="text-base font-bold text-emerald-800 mt-0.5 block">
              {formatNumber(reconciliation.wpD_simulasyon_oturum || 5207)} oturum
            </span>
          </div>
          <div className="p-3 rounded-lg bg-slate-50/80 border border-slate-200/80">
            <span className="text-slate-500 block text-[11px]">Seyrek Gün Filtresi Farkı</span>
            <span className="text-base font-bold text-slate-900 mt-0.5 block">
              {formatNumber(reconciliation.dislanan_oturum_sayisi || 108)} oturum
            </span>
          </div>
          <div className="p-3 rounded-lg bg-slate-50/80 border border-slate-200/80">
            <span className="text-slate-500 block text-[11px]">Temmuz–Aralık Test (148 gün-saha)</span>
            <span className="text-base font-bold text-slate-900 mt-0.5 block">
              {formatNumber(reconciliation.ta_oturum_sayisi || 11911)} oturum
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 text-xs tabular-nums mt-3 pt-3 border-t border-slate-100">
          <div className="p-2.5 rounded-lg bg-slate-50/60 border border-slate-200/60">
            <span className="text-slate-500 block text-[11px]">2020 Holdout Temiz Küme</span>
            <span className="text-sm font-bold text-slate-800 mt-0.5 block">
              {formatNumber(reconciliation.holdout_temiz_oturum || 4072)} oturum
            </span>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-50/60 border border-slate-200/60">
            <span className="text-slate-500 block text-[11px]">2020 Holdout Simülasyon (108 gün-saha [59 takvim günü], günde ≥4 araç)</span>
            <span className="text-sm font-bold text-emerald-800 mt-0.5 block">
              {formatNumber(reconciliation.holdout_simulasyon_oturum || 4043)} oturum
            </span>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-50/60 border border-slate-200/60 col-span-2 lg:col-span-1">
            <span className="text-slate-500 block text-[11px]">2020 Seyrek Gün Farkı</span>
            <span className="text-sm font-bold text-slate-800 mt-0.5 block">
              {formatNumber(reconciliation.holdout_dislanan_oturum || 29)} oturum
            </span>
          </div>
        </div>

        <p className="mt-2.5 text-xs text-slate-500">
          Doğrulama kümesindeki 5.315 geçerli beyanlı oturumdan günlük 8 araç altı seyrek günler protokol gereği elenerek 68 gün-sahada 5.207 oturum değerlendirilmiştir (108 oturumluk fark veri kaybı değil, simülasyon yoğunluk eşiği protokol filtresidir). Temmuz–Aralık 2019 dönemler arası test kümesinde 148 gün-sahada 11.911 oturum; 2020 Ocak–Şubat holdout birincil kümesinde ise 4.072 temizlenmiş oturumdan 108 gün-saha (59 takvim günü, günde ≥4 araç) üzerinde 4.043 oturum simüle edilmiştir (29 oturumluk fark protokol filtresidir).
        </p>
      </div>

      {/* 3. Dönem Performans Tablosu */}
      <div className="bg-white border border-slate-200/90 rounded-xl p-4 sm:p-5 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3.5">
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4 text-emerald-700 shrink-0" />
            <h3 className="font-bold text-sm text-slate-900">
              {currentPeriod.ad} Performans Tablosu{baslikDetay}
            </h3>
          </div>

          <div className="flex items-center flex-wrap gap-1.5 text-xs">
            {[
              { id: 'all', label: 'Tümü' },
              { id: '0.5', label: 'f = 0,5' },
              { id: '0.7', label: 'f = 0,7' },
              { id: '0.9', label: 'f = 0,9' },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setSelectedF(tab.id)}
                className={`px-2.5 py-1 rounded-lg border text-xs font-semibold transition tabular-nums ${
                  selectedF === tab.id
                    ? 'bg-emerald-700 text-white border-emerald-700'
                    : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs tabular-nums">
            <thead>
              <tr className="border-b border-slate-200 text-slate-600 bg-slate-50/80 font-semibold">
                <th className="py-2.5 px-3 whitespace-nowrap">Kapasite</th>
                <th className="py-2.5 px-3">Yöntem</th>
                <th className="py-2.5 px-3 text-right whitespace-nowrap">Hedef Karşılama</th>
                <th className="py-2.5 px-3 text-right whitespace-nowrap">Teslim Oranı</th>
                <th className="py-2.5 px-3 text-right whitespace-nowrap">Erken Ayrılan</th>
                <th className="py-2.5 px-3 text-right whitespace-nowrap">p10 Adillik</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {sortedRows.map((row, i) => {
                const meta = ALGORITHM_META[row.yontem];
                const label = BENCHMARK_METHOD_LABELS[row.yontem] || row.yontem;
                const isEdf = row.yontem.includes('edf');
                const isHibrit = row.yontem.includes('hibrit');
                const isHypothesisMpc = row.yontem === 'mpc_tahmin_guvenli';
                const isBeyanMpc = row.yontem === 'mpc_beyan';

                return (
                  <tr key={i} className="hover:bg-slate-50/80 transition">
                    <td className="py-2.5 px-3 text-slate-700 font-medium whitespace-nowrap">
                      f = {String(row.f).replace('.', ',')}
                    </td>
                    <td className="py-2.5 px-3 text-slate-900">
                      <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                        {meta && (
                          <span
                            className="w-2 h-2 rounded-full shrink-0"
                            style={{ backgroundColor: meta.color }}
                            aria-hidden="true"
                          />
                        )}
                        <span className="font-semibold text-slate-900">{label}</span>
                        {isHypothesisMpc && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold">
                            Önkayıtlı MPC
                          </span>
                        )}
                        {isBeyanMpc && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-50 text-amber-800 border border-amber-200 font-semibold">
                            Beyan Bazlı
                          </span>
                        )}
                        {(isEdf || isHibrit) && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
                            Keşifsel
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-900 font-bold whitespace-nowrap">
                      {formatPercent(row.basari_orani, 2, true)}
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-700 whitespace-nowrap">
                      {formatPercent(row.teslim_orani, 2, true)}
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-700 whitespace-nowrap">
                      {formatPercent(row.erken_ayrilan_basari, 2, true)}
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-700 whitespace-nowrap">
                      {formatPercent(row.p10_adillik, 2, true)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="mt-2.5 text-xs text-slate-500">
          * Teslim oranı, EVSE tarafından fiilen aktarılan enerji (kWhDelivered) üzerinden hesaplanmıştır. ACN veri tabanındaki kWhDelivered değeri aracın gerçek batarya kapasitesi veya toplam enerji ihtiyacı değil; o oturumda teslim edilen tarihsel enerjidir (ihtiyaç göstergesi). Tüm yöntemlerde trafo ihlali 0'dır (sert kısıt uygulanmıştır).
        </p>
      </div>
    </div>
  );
}

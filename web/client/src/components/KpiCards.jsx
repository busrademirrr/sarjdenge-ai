import React from 'react';
import { formatPercent, formatKwh, formatKw } from '../utils/formatters.js';
import { ALGORITHM_META } from '../utils/algorithmMeta.js';

export default function KpiCards({ kpis, simulation }) {
  if (!kpis) return null;

  const methodKeys = [
    'fcfs_beyan',
    'esit_beyan',
    'edf_beyan',
    'edf_tahmin_guvenli',
    'mpc_beyan',
    'mpc_tahmin_guvenli',
    'mpc_hibrit_asimetrik',
  ];

  const methods = methodKeys.map((k) => ALGORITHM_META[k]).filter((m) => m && kpis[m.key]);

  // Mevcut simülasyon sonuçlarından en yüksek hedef karşılama oranını belirle
  let bestRate = -1;
  methods.forEach((m) => {
    const rate = Number(kpis[m.key]?.basari_orani_yuzde ?? -1);
    if (rate > bestRate) {
      bestRate = rate;
    }
  });

  const bestMethods = methods.filter(
    (m) => Math.abs(Number(kpis[m.key]?.basari_orani_yuzde ?? -1) - bestRate) < 1e-4
  );
  const isTiedBest = bestMethods.length > 1;
  const primaryMethod = bestMethods[0] || methods[0];
  const primaryKpi = kpis[primaryMethod?.key] || {};

  const earlyVehiclesCount = Array.isArray(simulation?.araclar)
    ? simulation.araclar.filter((v) => v.erken_ayrildi).length
    : null;

  return (
    <section className="mb-4 space-y-3" aria-label="Temel Performans Göstergeleri ve Algoritma Karşılaştırması">
      {/* Üst Bölüm: 4 Kompakt Temel Gösterge */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 tabular-nums">
        <div className="bg-white border border-slate-200/90 rounded-xl p-3.5 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-medium text-slate-500">Hedef Karşılama Oranı</span>
            <span className="text-[11px] font-medium px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
              Eşik ≥%95
            </span>
          </div>
          <div className="mt-2 flex items-baseline justify-between gap-2">
            <span className="text-2xl font-bold text-slate-900 tracking-tight">
              {formatPercent(primaryKpi.basari_orani_yuzde, 1)}
            </span>
            <span className="text-[11px] text-emerald-800 font-medium truncate">
              {isTiedBest ? `${bestMethods.length} yöntem eşit` : primaryMethod?.shortName}
            </span>
          </div>
        </div>

        <div className="bg-white border border-slate-200/90 rounded-xl p-3.5 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-medium text-slate-500">Teslim Edilen Enerji</span>
            {primaryKpi.toplam_teslim_kwh !== undefined && (
              <span className="text-[11px] font-medium px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                {formatKwh(primaryKpi.toplam_teslim_kwh)}
              </span>
            )}
          </div>
          <div className="mt-2 flex items-baseline justify-between gap-2">
            <span className="text-2xl font-bold text-slate-900 tracking-tight">
              {formatPercent(primaryKpi.teslim_orani_yuzde, 1)}
            </span>
            <span className="text-[11px] text-slate-500">Toplam talep oranı</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200/90 rounded-xl p-3.5 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-medium text-slate-500">Erken Ayrılan Başarısı</span>
            {earlyVehiclesCount !== null && (
              <span className="text-[11px] font-medium px-1.5 py-0.5 rounded bg-amber-50 text-amber-800">
                {earlyVehiclesCount} araç
              </span>
            )}
          </div>
          <div className="mt-2 flex items-baseline justify-between gap-2">
            <span className="text-2xl font-bold text-slate-900 tracking-tight">
              {primaryKpi.erken_ayrilan_basari_yuzde !== null &&
              primaryKpi.erken_ayrilan_basari_yuzde !== undefined
                ? formatPercent(primaryKpi.erken_ayrilan_basari_yuzde, 1)
                : '—'}
            </span>
            <span className="text-[11px] text-slate-500">Hedefe ulaşan</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200/90 rounded-xl p-3.5 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-medium text-slate-500">Kapasite İhlali</span>
            <span className="text-[11px] font-medium px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800">
              Güvenli
            </span>
          </div>
          <div className="mt-2 flex items-baseline justify-between gap-2">
            <span className="text-2xl font-bold text-emerald-800 tracking-tight">
              {formatKw(primaryKpi.kapasite_ihlali_kw ?? 0)}
            </span>
            <span className="text-[11px] text-slate-500">Tüm yöntemler</span>
          </div>
        </div>
      </div>

      {/* Alt Bölüm: Algoritma Karşılaştırma Tablosu */}
      <div className="bg-white border border-slate-200/90 rounded-xl shadow-2xs overflow-hidden">
        <div className="px-4 py-2.5 border-b border-slate-100 flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center space-x-2">
            <h3 className="text-xs font-semibold text-slate-800">
              Algoritma Karşılaştırması
            </h3>
            {simulation?.acn_kalibrasyonu === false && (
              <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                ACN kalibrasyonu uygulanmadı
              </span>
            )}
          </div>
          <span className="text-[11px] text-slate-500">
            Hedef karşılama eşiği: ≥%95
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs tabular-nums">
            <thead>
              <tr className="border-b border-slate-200/80 text-slate-500 bg-slate-50/70 font-medium">
                <th className="py-2 px-4">Algoritma</th>
                <th className="py-2 px-4 text-right whitespace-nowrap">Hedef Karşılama</th>
                <th className="py-2 px-4 text-right whitespace-nowrap">Teslim Enerjisi</th>
                <th className="py-2 px-4 text-right whitespace-nowrap">Erken Ayrılan</th>
                <th className="py-2 px-4 text-right whitespace-nowrap">p10 Adillik</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {methods.map((m) => {
                const kpi = kpis[m.key];
                if (!kpi) return null;

                const isBest =
                  Math.abs(Number(kpi.basari_orani_yuzde ?? -1) - bestRate) < 1e-4;

                return (
                  <tr
                    key={m.key}
                    className={`hover:bg-slate-50/80 transition ${
                      isBest ? 'bg-emerald-50/20' : ''
                    }`}
                  >
                    <td className="py-2.5 px-4 font-medium text-slate-900 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <span
                          className="w-2.5 h-2.5 rounded-full shrink-0"
                          style={{ backgroundColor: m.color }}
                        />
                        <span>{m.name}</span>

                        {isBest && (
                          <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200/80 leading-none">
                            {isTiedBest ? 'Eşit En Yüksek' : 'En Yüksek'}
                          </span>
                        )}
                        {m.key === 'mpc_hibrit_asimetrik' && (
                          <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 leading-none">
                            Keşifsel
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="py-2.5 px-4 text-right font-bold text-slate-900 whitespace-nowrap">
                      {formatPercent(kpi.basari_orani_yuzde, 1)}
                    </td>

                    <td className="py-2.5 px-4 text-right text-slate-700 whitespace-nowrap">
                      {formatPercent(kpi.teslim_orani_yuzde, 1)}
                    </td>

                    <td className="py-2.5 px-4 text-right text-slate-700 whitespace-nowrap">
                      {kpi.erken_ayrilan_basari_yuzde !== null &&
                      kpi.erken_ayrilan_basari_yuzde !== undefined
                        ? formatPercent(kpi.erken_ayrilan_basari_yuzde, 1)
                        : '—'}
                    </td>

                    <td className="py-2.5 px-4 text-right text-slate-700 whitespace-nowrap">
                      {formatPercent(kpi.p10_adillik_yuzde, 1)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {simulation?.kuantil_kalibrasyon_notu && (
          <div className="px-4 py-2 bg-slate-50/80 border-t border-slate-100 text-xs text-slate-500">
            {simulation.kuantil_kalibrasyon_notu}
          </div>
        )}
      </div>
    </section>
  );
}

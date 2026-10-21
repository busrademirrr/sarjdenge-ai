import React from 'react';
import { formatPercent, formatKwh, formatKw } from '../utils/formatters.js';
import { ALGORITHM_META } from '../utils/algorithmMeta.js';

export default function KpiCards({ kpis, simulation }) {
  if (!kpis) return null;

  const methodKeys = [
    'fcfs_beyan',
    'edf_beyan',
    'edf_tahmin_guvenli',
    'mpc_beyan',
    'mpc_tahmin_guvenli',
    'mpc_hibrit_asimetrik',
  ];

  const methods = methodKeys.map((k) => ALGORITHM_META[k]).filter(Boolean);

  // Mevcut sim├╝lasyon sonu├ğlar─▒ndan en y├╝ksek hedef kar┼ş─▒lama oran─▒n─▒ belirle
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
    <section className="mb-4 space-y-3" aria-label="Temel Performans G├Âstergeleri ve Algoritma Kar┼ş─▒la┼şt─▒rmas─▒">
      {/* ├£st B├Âl├╝m: 4 Kompakt Temel G├Âsterge */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 tabular-nums">
        <div className="bg-white border border-slate-200/90 rounded-xl p-3.5 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-medium text-slate-500">Hedef Kar┼ş─▒lama Oran─▒</span>
            <span className="text-[11px] font-medium px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
              E┼şik ÔëÑ%95
            </span>
          </div>
          <div className="mt-2 flex items-baseline justify-between gap-2">
            <span className="text-2xl font-bold text-slate-900 tracking-tight">
              {formatPercent(primaryKpi.basari_orani_yuzde, 1)}
            </span>
            <span className="text-[11px] text-emerald-800 font-medium truncate">
              {isTiedBest ? `${bestMethods.length} y├Ântem e┼şit` : primaryMethod?.shortName}
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
            <span className="text-[11px] text-slate-500">Toplam talep oran─▒</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200/90 rounded-xl p-3.5 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-medium text-slate-500">Erken Ayr─▒lan Ba┼şar─▒s─▒</span>
            {earlyVehiclesCount !== null && (
              <span className="text-[11px] font-medium px-1.5 py-0.5 rounded bg-amber-50 text-amber-800">
                {earlyVehiclesCount} ara├ğ
              </span>
            )}
          </div>
          <div className="mt-2 flex items-baseline justify-between gap-2">
            <span className="text-2xl font-bold text-slate-900 tracking-tight">
              {primaryKpi.erken_ayrilan_basari_yuzde !== null &&
              primaryKpi.erken_ayrilan_basari_yuzde !== undefined
                ? formatPercent(primaryKpi.erken_ayrilan_basari_yuzde, 1)
                : 'ÔÇö'}
            </span>
            <span className="text-[11px] text-slate-500">Hedefe ula┼şan</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200/90 rounded-xl p-3.5 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-medium text-slate-500">Kapasite ─░hlali</span>
            <span className="text-[11px] font-medium px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800">
              G├╝venli
            </span>
          </div>
          <div className="mt-2 flex items-baseline justify-between gap-2">
            <span className="text-2xl font-bold text-emerald-800 tracking-tight">
              {formatKw(primaryKpi.kapasite_ihlali_kw ?? 0)}
            </span>
            <span className="text-[11px] text-slate-500">T├╝m y├Ântemler</span>
          </div>
        </div>
      </div>

      {/* Alt B├Âl├╝m: Kompakt 6 Algoritma Kar┼ş─▒la┼şt─▒rma Tablosu */}
      <div className="bg-white border border-slate-200/90 rounded-xl shadow-2xs overflow-hidden">
        <div className="px-4 py-2.5 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-xs font-semibold text-slate-800">
            Algoritma Kar┼ş─▒la┼şt─▒rmas─▒
          </h3>
          <span className="text-[11px] text-slate-500">
            Hedef kar┼ş─▒lama e┼şi─şi: ÔëÑ%95
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs tabular-nums">
            <thead>
              <tr className="border-b border-slate-200/80 text-slate-500 bg-slate-50/70 font-medium">
                <th className="py-2 px-4">Algoritma</th>
                <th className="py-2 px-4 text-right whitespace-nowrap">Hedef Kar┼ş─▒lama</th>
                <th className="py-2 px-4 text-right whitespace-nowrap">Teslim Enerjisi</th>
                <th className="py-2 px-4 text-right whitespace-nowrap">Erken Ayr─▒lan</th>
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
                            {isTiedBest ? 'E┼şit En Y├╝ksek' : 'En Y├╝ksek'}
                          </span>
                        )}
                        {m.isHypothesis && (
                          <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 leading-none">
                            Hipotez
                          </span>
                        )}
                        {m.key === 'mpc_hibrit_asimetrik' && (
                          <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 leading-none">
                            Ke┼şifsel
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
                        : 'ÔÇö'}
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
      </div>
    </section>
  );
}

import React from 'react';
import { Award, CheckCircle2, AlertCircle, Zap } from 'lucide-react';
import { formatPercent, formatKw } from '../utils/formatters.js';

export default function KpiCards({ kpis, simulation }) {
  if (!kpis) return null;

  const methods = [
    { key: 'fcfs_beyan', name: 'FCFS (Beyan)', color: '#EF4444', desc: 'İlk gelen ilk şarj olur' },
    { key: 'edf_beyan', name: 'EDF (Beyan)', color: '#3B82F6', desc: 'Beyan çıkışına göre termin' },
    { key: 'edf_tahmin_guvenli', name: 'EDF Güvenli (Tahmin)', color: '#8B5CF6', desc: 'q20 süre tahminli termin', highlight: true },
    { key: 'mpc_beyan', name: 'MPC (Beyan)', color: '#F59E0B', desc: 'Doğrusal programlama optimizasyonu' },
    { key: 'mpc_tahmin_guvenli', name: 'MPC Güvenli (Ana Hipotez)', color: '#10B981', desc: 'q80 enerji / q20 süre kısıtlı', isHypothesis: true },
    { key: 'mpc_hibrit_asimetrik', name: 'MPC Hibrit (Keşifsel)', color: '#06B6D4', desc: 'Asimetrik hata toleranslı' },
  ];

  // Best method calculation for Hedef Karşılama
  let bestKey = '';
  let bestRate = -1;
  methods.forEach(m => {
    const rate = kpis[m.key]?.basari_orani_yuzde ?? -1;
    if (rate > bestRate) {
      bestRate = rate;
      bestKey = m.key;
    }
  });

  const capKw = simulation?.kapasite_siniri_kw;

  return (
    <div className="mb-6 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xs font-bold tracking-wider text-slate-300 uppercase">
            2. Algoritma Karşılaştırmalı Performans Göstergeleri (KPI)
          </h2>
          <p className="text-xs text-slate-400">
            Tüm yöntemler aynı oturumlar, aynı araç batarya gereksinimleri ve aynı şarj gücü tavanı ({formatKw(capKw)}) altında değerlendirilmiştir.
          </p>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
        {methods.map((m) => {
          const kpi = kpis[m.key];
          if (!kpi) return null;

          const isBest = m.key === bestKey;

          return (
            <div
              key={m.key}
              className={`rounded-2xl p-3.5 border relative transition-all ${
                isBest
                  ? 'bg-slate-900 border-emerald-500/80 shadow-md shadow-emerald-500/10 ring-1 ring-emerald-500/40'
                  : 'bg-slate-900/70 border-slate-800 hover:border-slate-700/80'
              }`}
            >
              {/* Badge for Hypothesis / Best */}
              <div className="flex items-center justify-between mb-2">
                <span
                  className="w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: m.color }}
                />
                {isBest && (
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 flex items-center space-x-1">
                    <Award className="w-3 h-3" />
                    <span>Lider</span>
                  </span>
                )}
                {m.isHypothesis && !isBest && (
                  <span className="text-[9px] font-medium px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30">
                    Ana Hipotez
                  </span>
                )}
              </div>

              {/* Title */}
              <h3 className="font-bold text-xs text-white truncate" title={m.name}>
                {m.name}
              </h3>

              {/* Primary Metric: Hedef Karşılama Oranı */}
              <div className="mt-2.5 mb-2">
                <span className="text-[10px] text-slate-400 block uppercase font-medium">Hedef Karşılama (≥%95)</span>
                <div className="flex items-baseline space-x-1 mt-0.5">
                  <span className="text-xl font-extrabold text-white font-mono">
                    {formatPercent(kpi.basari_orani_yuzde, 1)}
                  </span>
                </div>
              </div>

              {/* Secondary Metrics */}
              <div className="space-y-1.5 pt-2 border-t border-slate-800/80 text-[11px]">
                <div className="flex items-center justify-between text-slate-400">
                  <span>Teslim Enerji:</span>
                  <span className="font-mono text-slate-200">{formatPercent(kpi.teslim_orani_yuzde, 1)}</span>
                </div>

                <div className="flex items-center justify-between text-slate-400">
                  <span>Erken Ayrılan:</span>
                  <span className="font-mono text-slate-200">
                    {kpi.erken_ayrilan_basari_yuzde !== null ? formatPercent(kpi.erken_ayrilan_basari_yuzde, 1) : '—'}
                  </span>
                </div>

                <div className="flex items-center justify-between text-slate-400">
                  <span>p10 Adillik:</span>
                  <span className="font-mono text-slate-200">{formatPercent(kpi.p10_adillik_yuzde, 1)}</span>
                </div>

                <div className="flex items-center justify-between text-slate-400">
                  <span>Kapasite İhlali:</span>
                  <span className="font-mono text-emerald-400 font-bold">0,0 kW</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

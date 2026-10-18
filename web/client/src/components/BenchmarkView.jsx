import React from 'react';
import { Database, ShieldCheck, AlertCircle, FileText, CheckCircle2, TrendingUp, Info } from 'lucide-react';
import { formatPercent, formatYp, formatNumber } from '../utils/formatters.js';

export default function BenchmarkView({ benchmarkData }) {
  if (!benchmarkData) {
    return (
      <div className="p-8 text-center text-slate-400">
        <p>Doğrulama ve deney sonuçları yükleniyor…</p>
      </div>
    );
  }

  const { valTable = [], bootVal = [], taTable = [], reconciliation = {}, primaryHypothesis = {} } = benchmarkData;

  return (
    <div className="space-y-6">
      {/* Top Banner: Hypothesis Verdict & Ghost Reservation */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-xl">
        <div className="flex items-start space-x-4">
          <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/25 text-amber-400 shrink-0">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2 flex-wrap gap-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30">
                Ön Kayıtlı Ana Hipotez Kararı
              </span>
              <span className="text-xs sm:text-sm font-bold text-rose-400">
                H₀ Korundu — Hipotez Desteklenmedi
              </span>
            </div>

            <h3 className="text-sm sm:text-base font-bold text-white mt-1.5 leading-snug">
              {primaryHypothesis.ifade}
            </h3>

            <p className="text-xs text-slate-300 mt-2 leading-relaxed">
              <strong className="text-slate-200">Fiziksel Neden (Hayalet Kapasite Rezervasyonu):</strong> {primaryHypothesis.fiziksel_mekanizma}
            </p>

            <div className="mt-3.5 p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center space-x-3 text-xs">
              <span className="text-emerald-400 font-bold shrink-0">Lider Algoritma:</span>
              <span className="text-slate-300">{primaryHypothesis.en_guclu_planlayici?.ad} — {primaryHypothesis.en_guclu_planlayici?.neden}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Sample Size Reconciliation (WP C vs WP D) */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex items-center space-x-2 mb-3">
          <Info className="w-4 h-4 text-emerald-400" />
          <h3 className="font-bold text-xs sm:text-sm text-white">Örneklem Büyüklüğü Mutabakatı (İş Paketi C vs D)</h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs mb-3">
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-slate-400 block text-[11px]">İş Paketi C Doğrulama Oturumu</span>
            <span className="text-lg font-bold text-white font-mono">{formatNumber(reconciliation.wpC_dogrulama_oturum)}</span>
            <span className="text-[10px] text-slate-500 block">Tüm Ocak–Haziran Doğrulama</span>
          </div>

          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-slate-400 block text-[11px]">İş Paketi D Simülasyon Oturumu</span>
            <span className="text-lg font-bold text-emerald-400 font-mono">{formatNumber(reconciliation.wpD_simulasyon_oturum)}</span>
            <span className="text-[10px] text-slate-500 block">68 Sıkışık Günde Simüle Edilen</span>
          </div>

          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-slate-400 block text-[11px]">Dışlanan Seyrek Oturum Sayısı</span>
            <span className="text-lg font-bold text-amber-400 font-mono">{formatNumber(reconciliation.dislanan_oturum_sayisi)}</span>
            <span className="text-[10px] text-slate-500 block">Fark: 5.315 - 5.207 = 108</span>
          </div>

          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-slate-400 block text-[11px]">Temmuz–Aralık Test Kümesi</span>
            <span className="text-lg font-bold text-purple-400 font-mono">{formatNumber(reconciliation.ta_oturum_sayisi)}</span>
            <span className="text-[10px] text-slate-500 block">153 Gün Boyunca Doğrulama</span>
          </div>
        </div>

        <p className="text-xs text-slate-400 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
          <strong className="text-slate-300">Metodolojik Gerekçe:</strong> {reconciliation.dislanma_nedeni}
        </p>
      </div>

      {/* Paired Bootstrap Comparison Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            <h3 className="font-bold text-xs sm:text-sm text-white">Eşleştirilmiş Gün Bazlı Bootstrap Hipotez Testleri (B = 2.000)</h3>
          </div>
          <span className="text-xs text-slate-400 font-mono self-start sm:self-auto bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
            %95 Güven Aralığı
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="py-2.5 px-3">Kapasite (f)</th>
                <th className="py-2.5 px-3">Karşılaştırma</th>
                <th className="py-2.5 px-3">Tür</th>
                <th className="py-2.5 px-3 text-right">Fark (Yüzde Puanı)</th>
                <th className="py-2.5 px-3 text-right">%95 Güven Aralığı</th>
                <th className="py-2.5 px-3 text-center">Hipotez Durumu</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {bootVal.map((row, i) => {
                const isHypothesis = row.tur === 'Ana Hipotez';
                const altFmt = Number(row.ci_95_alt_puan).toFixed(2).replace('.', ',');
                const ustFmt = Number(row.ci_95_ust_puan).toFixed(2).replace('.', ',');

                return (
                  <tr
                    key={i}
                    className={`hover:bg-slate-800/40 transition ${
                      isHypothesis ? 'bg-amber-500/5 font-semibold' : ''
                    }`}
                  >
                    <td className="py-2.5 px-3 text-slate-300">f = {String(row.f).replace('.', ',')}</td>
                    <td className="py-2.5 px-3 text-white">{row.karsilastirma}</td>
                    <td className="py-2.5 px-3 text-slate-400">{row.tur}</td>
                    <td className={`py-2.5 px-3 text-right ${row.fark_yuzde_puan >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {formatYp(row.fark_yuzde_puan, 2)}
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-300">
                      [{altFmt}, {ustFmt}] y.p.
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                        Desteklenmedi
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Validation Performance Table (68 Days) */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex items-center space-x-2 mb-4">
          <Database className="w-4 h-4 text-emerald-400" />
          <h3 className="font-bold text-xs sm:text-sm text-white">Doğrulama Kümesi Performans Tablosu (Ocak–Haziran 2019, 68 Gün, 5.207 Oturum)</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="py-2.5 px-3">Kapasite (f)</th>
                <th className="py-2.5 px-3">Yöntem</th>
                <th className="py-2.5 px-3 text-right">Hedef Karşılama</th>
                <th className="py-2.5 px-3 text-right">Teslim Oranı</th>
                <th className="py-2.5 px-3 text-right">Erken Ayrılan</th>
                <th className="py-2.5 px-3 text-right">p10 Adillik</th>
                <th className="py-2.5 px-3 text-center">İhlal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {valTable.map((row, i) => (
                <tr key={i} className="hover:bg-slate-800/40 transition">
                  <td className="py-2.5 px-3 text-slate-300">f = {String(row.f).replace('.', ',')}</td>
                  <td className="py-2.5 px-3 text-white font-semibold">{row.yontem}</td>
                  <td className="py-2.5 px-3 text-right text-emerald-400 font-bold">
                    {formatPercent(row.basari_orani, 2, true)}
                  </td>
                  <td className="py-2.5 px-3 text-right text-slate-300">
                    {formatPercent(row.teslim_orani, 2, true)}
                  </td>
                  <td className="py-2.5 px-3 text-right text-slate-300">
                    {formatPercent(row.erken_ayrilan_basari, 2, true)}
                  </td>
                  <td className="py-2.5 px-3 text-right text-slate-300">
                    {formatPercent(row.p10_adillik, 2, true)}
                  </td>
                  <td className="py-2.5 px-3 text-center text-emerald-400 font-bold">0,0 kW</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

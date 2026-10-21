import React, { useState } from 'react';
import { Database, AlertCircle, TrendingUp, Info, RefreshCw } from 'lucide-react';
import { formatPercent, formatYp, formatNumber } from '../utils/formatters.js';
import { BENCHMARK_METHOD_LABELS, ALGORITHM_META } from '../utils/algorithmMeta.js';

export default function BenchmarkView({ benchmarkData, onRetry }) {
  const [selectedF, setSelectedF] = useState('all');

  if (!benchmarkData) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-600 shadow-2xs">
        <RefreshCw className="w-5 h-5 text-emerald-700 animate-spin mx-auto mb-2.5" />
        <p className="text-xs font-semibold text-slate-800">Do─şrulama sonu├ğlar─▒ y├╝kleniyorÔÇĞ</p>
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
    reconciliation = {},
    primaryHypothesis = {},
  } = benchmarkData;

  const bulgular = primaryHypothesis.bulgular || [
    { f: 0.5, fark_yp: -0.17, ci_95: [-0.66, 0.28] },
    { f: 0.7, fark_yp: -0.58, ci_95: [-1.06, -0.10] },
    { f: 0.9, fark_yp: -0.02, ci_95: [-0.22, 0.17] },
  ];

  const filteredValRows = valTable.filter(
    (row) => selectedF === 'all' || String(row.f) === selectedF
  );

  return (
    <div className="space-y-4">
      {/* 1. Ana Hipotez Sonucu + 3 Kompakt Kapasite Kart─▒ */}
      <div className="bg-white border border-slate-200/90 rounded-xl p-4 sm:p-5 shadow-2xs">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-700 shrink-0 mt-0.5">
              <AlertCircle className="w-4 h-4 text-slate-600" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-slate-900 leading-snug">
                ├ûnkay─▒tl─▒ hipotez desteklenmedi
              </h2>
              <p className="text-xs text-slate-600 mt-1">
                ├ûnkay─▒tl─▒ ba┼şar─▒ ├Âl├ğ├╝t├╝ kar┼ş─▒lanmad─▒: fark─▒n en az +2 y├╝zde puan olmas─▒ ve %95 g├╝ven aral─▒─ş─▒n─▒n alt s─▒n─▒r─▒n─▒n s─▒f─▒r─▒n ├╝zerinde bulunmas─▒ gerekiyordu.
              </p>
            </div>
          </div>

          <span className="text-xs font-medium text-slate-600 bg-slate-50 px-2.5 py-1 rounded-md border border-slate-200 tabular-nums shrink-0">
            ├ûl├ğ├╝t: ╬ö ÔëÑ +2,00 y.p.
          </span>
        </div>

        {/* 3 Kompakt Kapasite Kart─▒ */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4 tabular-nums">
          {bulgular.map((b) => {
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
                    MPC G├╝venli ÔêÆ MPC Beyan
                  </span>
                </div>
                <div className="flex items-baseline justify-between mt-2">
                  <span className="text-xs text-slate-500">├ûl├ğ├╝len Fark</span>
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
              </div>
            );
          })}
        </div>

        {/* Eri┼şilebilir "─░statistiksel ayr─▒nt─▒lar" A├ğ─▒l─▒r B├Âl├╝m├╝ */}
        <details className="mt-4 pt-3 border-t border-slate-100 group text-xs text-slate-600">
          <summary className="font-semibold text-slate-800 hover:text-emerald-800 cursor-pointer flex items-center justify-between list-none">
            <span className="flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-emerald-700 shrink-0" />
              <span>─░statistiksel ayr─▒nt─▒lar (Bootstrap B = 2.000, ├çal─▒┼şma Hipotezi ve ─░kincil Bulgular)</span>
            </span>
            <span className="text-slate-400 group-open:rotate-180 transition-transform">Ôû¥</span>
          </summary>

          <div className="mt-3 space-y-3 leading-relaxed">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80">
                <strong className="text-slate-800 block mb-0.5">─░statistiksel Karar</strong>
                <span>
                  S─▒f─▒r hipotezi reddedilemedi. E┼şle┼ştirilmi┼ş g├╝n bazl─▒ bootstrap (B = 2.000) testlerinde ├Ânkay─▒tl─▒ ana hipotez kar┼ş─▒la┼şt─▒rmalar─▒n─▒n g├╝ven aral─▒klar─▒ s─▒f─▒r─▒ kapsamakta veya s─▒f─▒r─▒n alt─▒nda kalmaktad─▒r.
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80">
                <strong className="text-slate-800 block mb-0.5">Olas─▒ A├ğ─▒klama (├çal─▒┼şma Hipotezi)</strong>
                <span>
                  Konservatif q80 enerji ve q20 s├╝re tahminlerinin LP-MPC ├ğ├Âz├╝c├╝s├╝nde kapasiteyi erken ad─▒mlarda belirli ara├ğlara ay─▒rmas─▒na (hayalet kapasite rezervasyonu) ve di─şer ara├ğlar─▒n ┼şarj─▒n─▒ geciktirmesine yol a├ğm─▒┼ş olabilece─şi de─şerlendirilmektedir.
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80">
                <strong className="text-slate-800 block mb-0.5">De─şerlendirme Bulgusu</strong>
                <span>
                  Bu de─şerlendirmede EDF baz─▒ kapasite d├╝zeylerinde y├╝ksek hedef kar┼ş─▒lama sonu├ğlar─▒ vermi┼ştir. Algoritmalar─▒n performans─▒ kapasite d├╝zeyine ve kullan─▒lan metri─şe g├Âre kar┼ş─▒la┼şt─▒r─▒lmal─▒d─▒r.
                </span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs tabular-nums">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-600 bg-slate-50/70">
                    <th className="py-2 px-3 font-semibold">Kapasite (f)</th>
                    <th className="py-2 px-3 font-semibold">Kar┼ş─▒la┼şt─▒rma</th>
                    <th className="py-2 px-3 font-semibold">Protokol T├╝r├╝</th>
                    <th className="py-2 px-3 text-right font-semibold">Fark (y.p.)</th>
                    <th className="py-2 px-3 text-right font-semibold">%95 G├╝ven Aral─▒─ş─▒</th>
                    <th className="py-2 px-3 text-center font-semibold">Durum</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {bootVal.map((row, i) => {
                    const isHypothesis = row.tur === 'Ana Hipotez';
                    const altNum = Number(row.ci_95_alt_puan);
                    const ustNum = Number(row.ci_95_ust_puan);
                    const altFmt = altNum.toFixed(2).replace('.', ',');
                    const ustFmt = ustNum.toFixed(2).replace('.', ',');

                    let statusLabel = 'Desteklenmedi';
                    let statusClass = 'bg-slate-100 text-slate-700 border-slate-200';

                    if (isHypothesis) {
                      statusLabel = '├ûnkay─▒tl─▒ Hipotez Desteklenmedi';
                      statusClass = 'bg-slate-100 text-slate-800 border-slate-300';
                    } else if (altNum > 0) {
                      statusLabel = 'Ke┼şifsel bulgu (GA > 0)';
                      statusClass = 'bg-teal-50 text-teal-800 border-teal-200';
                    } else if (ustNum < 0) {
                      statusLabel = '─░kincil (GA < 0)';
                      statusClass = 'bg-amber-50/80 text-amber-800 border-amber-200';
                    } else {
                      statusLabel = '─░kincil (GA 0\'─▒ kapsar)';
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

      {/* 2. K─▒sa ve Sade ├ûrneklem & Veri Ak─▒┼ş─▒ ├ûzeti */}
      <div className="bg-white border border-slate-200/90 rounded-xl p-4 shadow-2xs">
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center space-x-2">
            <Info className="w-4 h-4 text-emerald-700 shrink-0" />
            <h3 className="font-bold text-sm text-slate-900">
              ├ûrneklem ve Veri Ak─▒┼ş─▒ ├ûzeti
            </h3>
          </div>
          <span className="text-[11px] text-slate-500">
            Protokol: min_arac_gunluk = 8
          </span>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-xs tabular-nums">
          <div className="p-3 rounded-lg bg-slate-50/80 border border-slate-200/80">
            <span className="text-slate-500 block text-[11px]">Do─şrulama K├╝mesi (2019 H1)</span>
            <span className="text-base font-bold text-slate-900 mt-0.5 block">
              {formatNumber(reconciliation.wpC_dogrulama_oturum)} oturum
            </span>
          </div>
          <div className="p-3 rounded-lg bg-slate-50/80 border border-slate-200/80">
            <span className="text-slate-500 block text-[11px]">Sim├╝lasyon (68 S─▒k─▒┼ş─▒k G├╝n)</span>
            <span className="text-base font-bold text-emerald-800 mt-0.5 block">
              {formatNumber(reconciliation.wpD_simulasyon_oturum)} oturum
            </span>
          </div>
          <div className="p-3 rounded-lg bg-slate-50/80 border border-slate-200/80">
            <span className="text-slate-500 block text-[11px]">Seyrek G├╝n Filtresi Fark─▒</span>
            <span className="text-base font-bold text-slate-900 mt-0.5 block">
              {formatNumber(reconciliation.dislanan_oturum_sayisi)} oturum
            </span>
          </div>
          <div className="p-3 rounded-lg bg-slate-50/80 border border-slate-200/80">
            <span className="text-slate-500 block text-[11px]">TemmuzÔÇôAral─▒k Test (148 G├╝n)</span>
            <span className="text-base font-bold text-slate-900 mt-0.5 block">
              {formatNumber(reconciliation.ta_oturum_sayisi)} oturum
            </span>
          </div>
        </div>

        <p className="mt-2.5 text-xs text-slate-500">
          Do─şrulama k├╝mesindeki 5.315 ge├ğerli beyanl─▒ oturumdan g├╝nl├╝k 8 ara├ğ alt─▒ seyrek g├╝nler protokol gere─şi elenerek 68 g├╝nde 5.207 oturum de─şerlendirilmi┼ştir (fark: 108 oturum).
        </p>
      </div>

      {/* 3. Do─şrulama K├╝mesi Performans Tablosu */}
      <div className="bg-white border border-slate-200/90 rounded-xl p-4 sm:p-5 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3.5">
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4 text-emerald-700 shrink-0" />
            <h3 className="font-bold text-sm text-slate-900">
              Do─şrulama K├╝mesi Performans Tablosu (68 G├╝n, 5.207 Oturum)
            </h3>
          </div>

          <div className="flex items-center flex-wrap gap-1.5 text-xs">
            {[
              { id: 'all', label: 'T├╝m├╝' },
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
                <th className="py-2.5 px-3">Y├Ântem</th>
                <th className="py-2.5 px-3 text-right whitespace-nowrap">Hedef Kar┼ş─▒lama</th>
                <th className="py-2.5 px-3 text-right whitespace-nowrap">Teslim Oran─▒</th>
                <th className="py-2.5 px-3 text-right whitespace-nowrap">Erken Ayr─▒lan</th>
                <th className="py-2.5 px-3 text-right whitespace-nowrap">p10 Adillik</th>
                <th className="py-2.5 px-3 text-center whitespace-nowrap">─░hlal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredValRows.map((row, i) => {
                const meta = ALGORITHM_META[row.yontem];
                const label = BENCHMARK_METHOD_LABELS[row.yontem] || row.yontem;
                return (
                  <tr key={i} className="hover:bg-slate-50/80 transition">
                    <td className="py-2.5 px-3 text-slate-700 font-medium whitespace-nowrap">
                      f = {String(row.f).replace('.', ',')}
                    </td>
                    <td className="py-2.5 px-3 text-slate-900">
                      <div className="flex items-center space-x-2">
                        {meta && (
                          <span
                            className="w-2 h-2 rounded-full shrink-0"
                            style={{ backgroundColor: meta.color }}
                            aria-hidden="true"
                          />
                        )}
                        <span className="font-semibold text-slate-900">{label}</span>
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
                    <td className="py-2.5 px-3 text-center text-emerald-800 font-semibold whitespace-nowrap">
                      0,0 kW
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

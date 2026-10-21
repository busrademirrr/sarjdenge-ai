import React, { useState, useEffect } from 'react';
import { Cpu, AlertTriangle, CheckCircle2, Info, RefreshCw } from 'lucide-react';
import { ADVISOR_METHOD_META } from '../utils/algorithmMeta.js';

export default function CapacityAdvisor({
  scenarios,
  selectedScenarioId,
  onSelectScenario,
  day,
  onChangeDay,
}) {
  const [loading, setLoading] = useState(false);
  const [advisorData, setAdvisorData] = useState(null);
  const [error, setError] = useState(null);

  const currentScenario = scenarios?.find((s) => s.id === selectedScenarioId) || scenarios?.[0];

  const runAdvisor = async (scId = selectedScenarioId, dayVal = day) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/capacity-advisor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenarioId: scId,
          day: dayVal,
        }),
      });

      const data = await res.json();
      if (data.success && data.advisor) {
        setAdvisorData(data.advisor);
      } else {
        setError(data.error || 'Kapasite analizi hesaplanamad─▒.');
      }
    } catch (err) {
      console.error('Advisor fetch error:', err);
      setError('Kapasite Dan─▒┼şman─▒ servisine ba─şlan─▒rken a─ş hatas─▒ olu┼ştu.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedScenarioId) {
      runAdvisor(selectedScenarioId, day);
    }
  }, [selectedScenarioId, day]);

  // Se├ğilen y├Ântemin ad─▒n─▒ "EDF ÔÇö En Erken Termin ├ûncelikli" format─▒nda temiz g├Âster
  const formatMethodDisplay = (rawName) => {
    if (!rawName) return 'ÔÇö';
    return String(rawName).replace(/\s*\(([^)]+)\)/, ' ÔÇö $1');
  };

  return (
    <div className="space-y-5">
      {/* 1. Belirgin ├£st Se├ğim ve Kontrol Alan─▒ */}
      <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 shrink-0 shadow-2xs">
              <Cpu className="w-5 h-5" />
            </div>
            <div className="flex items-center flex-wrap gap-2.5">
              <h2 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight">
                Kapasite Dan─▒┼şman─▒
              </h2>
              {advisorData && (
                <span
                  className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-md text-xs font-medium ${
                    advisorData.sentetik_mi
                      ? 'bg-amber-50 text-amber-800 border border-amber-200/70'
                      : 'bg-blue-50 text-blue-800 border border-blue-200/70'
                  }`}
                >
                  {advisorData.sentetik_mi ? (
                    <>
                      <AlertTriangle className="w-3 h-3 text-amber-600 shrink-0" />
                      <span>Sentetik</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3 h-3 text-blue-600 shrink-0" />
                      <span>ACN Ger├ğek Saha</span>
                    </>
                  )}
                </span>
              )}
            </div>
          </div>

          {/* Kontroller: Senaryo + Tarih + Belirgin Birincil "Yeniden Hesapla" Butonu */}
          <div className="flex flex-wrap sm:flex-nowrap items-center gap-2.5">
            <select
              aria-label="Senaryo Se├ğimi"
              value={selectedScenarioId}
              onChange={(e) => onSelectScenario(e.target.value)}
              className="bg-slate-50 hover:bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-emerald-700 transition min-w-[220px]"
            >
              {scenarios?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>

            <select
              aria-label="Sim├╝lasyon Tarihi"
              value={day}
              onChange={(e) => onChangeDay(e.target.value)}
              className="bg-slate-50 hover:bg-white border border-slate-200 rounded-lg px-2.5 py-2 text-xs font-medium text-slate-800 tabular-nums focus:outline-none focus:ring-1 focus:ring-emerald-700 transition w-32"
            >
              {currentScenario?.availableDays?.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              )) || <option value={day}>{day}</option>}
            </select>

            <button
              onClick={() => runAdvisor(selectedScenarioId, day)}
              disabled={loading}
              className="inline-flex items-center justify-center space-x-2 px-4 py-2 bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white rounded-lg text-xs sm:text-sm font-semibold shadow-xs transition whitespace-nowrap"
            >
              <RefreshCw className={`w-4 h-4 shrink-0 ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? 'Hesaplan─▒yorÔÇĞ' : 'Yeniden Hesapla'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Kompakt Y├╝klenme Durumu */}
      {loading && (
        <div className="bg-white border border-slate-200 rounded-xl py-6 px-4 flex items-center justify-center space-x-2.5 shadow-2xs">
          <RefreshCw className="w-4 h-4 text-emerald-700 animate-spin shrink-0" />
          <span className="text-xs font-semibold text-slate-700">
            Kapasite hesaplan─▒yorÔÇĞ
          </span>
        </div>
      )}

      {/* Hata Durumu */}
      {error && !loading && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-3.5 text-xs text-rose-900 flex items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={() => runAdvisor(selectedScenarioId, day)}
            className="px-3 py-1 rounded-lg text-xs font-semibold bg-rose-700 text-white shrink-0"
          >
            Tekrar Dene
          </button>
        </div>
      )}

      {advisorData && !loading && (
        <>
          {/* 2. Ana Sonu├ğ Paneli: Asgari Trafo G├╝c├╝ ve Se├ğilen Y├Ântem Odakl─▒ */}
          <div className="bg-white border border-slate-200/90 rounded-xl p-5 sm:p-6 shadow-2xs">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center tabular-nums">
              {/* Birincil Sonu├ğ: Asgari Trafo G├╝c├╝ + Se├ğilen Y├Ântem */}
              <div className="lg:col-span-8 flex flex-col sm:flex-row sm:items-center gap-5 sm:gap-8 lg:border-r border-slate-100 lg:pr-6">
                <div className="shrink-0">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Asgari Trafo G├╝c├╝
                    </span>
                    <span className="text-[11px] font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                      ┬▒{advisorData.arama_cozunurlugu_kw ?? 0.5} kW
                    </span>
                  </div>
                  <div className="flex items-baseline space-x-1.5 mt-1.5">
                    <span className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight leading-none">
                      {advisorData.onerilen_asgari_kapasite_kw ?? 'ÔÇö'}
                    </span>
                    <span className="text-lg sm:text-xl text-slate-600 font-bold">kW</span>
                  </div>
                </div>

                <div className="sm:border-l border-slate-100 sm:pl-7">
                  <span className="text-xs font-medium text-slate-500 block">
                    {advisorData.esitlik_var ? 'E┼şit Minimum Y├Ântemler' : 'En D├╝┼ş├╝k Kapasiteli Y├Ântem'}
                  </span>
                  <span className="text-base sm:text-lg font-bold text-emerald-800 mt-1 block leading-snug">
                    {formatMethodDisplay(advisorData.onerilen_yontem)}
                  </span>
                  <span className="text-xs text-slate-500 mt-1 block">
                    {advisorData.esitlik_var
                      ? (advisorData.esit_yontemler || []).map(formatMethodDisplay).join(' ÔÇó ')
                      : `${advisorData.arac_sayisi} ara├ğl─▒k se├ğili kesit sonucu`}
                  </span>
                </div>
              </div>

              {/* ─░kincil Bilgiler: Kontrols├╝z Pik, Nominal Kapasite ve Karar Kriteri */}
              <div className="lg:col-span-4 space-y-1.5 text-xs">
                <div className="flex items-center justify-between text-slate-500">
                  <span>Kontrols├╝z Pik</span>
                  <span className="font-semibold text-slate-700">{advisorData.kontrolsuz_tepe_kw} kW</span>
                </div>
                {advisorData.nominal_trafo_kapasitesi_kw && (
                  <div className="flex items-center justify-between text-slate-500">
                    <span>Nominal Kapasite</span>
                    <span className="font-semibold text-slate-700">{advisorData.nominal_trafo_kapasitesi_kw} kW</span>
                  </div>
                )}
                <div className="flex items-center justify-between text-slate-500">
                  <span>Karar Kriteri</span>
                  <span className="font-medium text-slate-600">ÔëÑ%95 Hedef Kar┼ş─▒lama</span>
                </div>
              </div>
            </div>
          </div>

          {/* 3. D├Ârt Algoritma Kart─▒: Daha G├Âr├╝n├╝r ve Dengeli Boyut */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {advisorData.yontemler.map((y) => {
              const isLowest = advisorData.esit_yontem_kodlari?.includes(y.kod);
              const meta = ADVISOR_METHOD_META[y.kod] || { symbol: 'ÔùÅ', tag: 'Algoritma', color: y.renk || '#059669' };

              return (
                <div
                  key={y.kod}
                  className={`rounded-xl p-5 flex flex-col justify-between transition min-h-[152px] ${
                    isLowest
                      ? 'bg-emerald-50/20 border-2 border-emerald-600 shadow-xs'
                      : 'bg-white border border-slate-200/90 shadow-2xs hover:border-slate-300'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2.5">
                      <span className="inline-flex items-center space-x-1.5 text-xs font-medium text-slate-500 truncate">
                        <span
                          className="w-2.5 h-2.5 rounded-full shrink-0"
                          style={{ backgroundColor: meta.color }}
                        />
                        <span className="truncate">{meta.tag}</span>
                      </span>
                      {isLowest && (
                        <span className="text-xs font-semibold px-2.5 py-0.5 rounded-md bg-emerald-100/80 text-emerald-900 border border-emerald-300 leading-none shrink-0">
                          {advisorData.esitlik_var ? 'E┼şit Min.' : 'En D├╝┼ş├╝k'}
                        </span>
                      )}
                    </div>

                    <h3 className="text-sm sm:text-base font-bold text-slate-900 leading-snug">
                      {y.ad}
                    </h3>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-200/60 flex items-baseline justify-between tabular-nums">
                    <span className="text-xs font-medium text-slate-500">Asgari G├╝├ğ</span>
                    <div className="flex items-baseline space-x-1">
                      <span
                        className={`text-2xl sm:text-3xl font-extrabold tracking-tight ${
                          isLowest ? 'text-emerald-900' : 'text-slate-900'
                        }`}
                      >
                        {y.asgari_kapasite_kw !== null ? y.asgari_kapasite_kw : 'Eri┼şilemedi'}
                      </span>
                      {y.asgari_kapasite_kw !== null && (
                        <span className="text-xs sm:text-sm font-bold text-slate-600">kW</span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* 4. Kapasite Tarama Matrisi: D├╝zenli Sat─▒r Aral─▒klar─▒ ve Ba┼şl─▒klar */}
          <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3.5">
              <h3 className="text-sm sm:text-base font-bold text-slate-900">
                Kapasite Tarama Matrisi
              </h3>
              <span className="text-xs font-medium text-slate-500 tabular-nums">
                Hedef kar┼ş─▒lama e┼şi─şi: ÔëÑ%95,0
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs sm:text-sm tabular-nums">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-600 bg-slate-50/80">
                    <th className="py-3 px-4 font-semibold whitespace-nowrap">Aday Kapasite</th>
                    {advisorData.yontemler.map((y) => {
                      const meta = ADVISOR_METHOD_META[y.kod] || { symbol: 'ÔùÅ', color: y.renk };
                      return (
                        <th key={y.kod} className="py-3 px-4 text-center font-semibold">
                          <span style={{ color: meta.color }} className="font-bold inline-flex items-center space-x-1.5">
                            <span aria-hidden="true">{meta.symbol}</span>
                            <span>{y.ad}</span>
                          </span>
                        </th>
                      );
                    })}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {advisorData.aday_kapasiteler_kw.map((capKw, idx) => {
                    const isMinRow =
                      Math.abs(Number(capKw) - Number(advisorData.onerilen_asgari_kapasite_kw)) < 0.05;
                    return (
                      <tr
                        key={capKw}
                        className={`hover:bg-slate-50/80 transition ${
                          isMinRow ? 'bg-emerald-50/20' : ''
                        }`}
                      >
                        <td className="py-3 px-4 font-bold text-slate-900 whitespace-nowrap">
                          <div className="flex items-center space-x-2">
                            <span>{capKw} kW</span>
                            {isMinRow && (
                              <span className="px-2 py-0.5 text-[11px] font-bold bg-emerald-100/80 text-emerald-900 border border-emerald-300 rounded">
                                ASGAR─░
                              </span>
                            )}
                          </div>
                        </td>

                        {advisorData.yontemler.map((y) => {
                          const step =
                            y.tarama.find((t) => Math.abs(Number(t.kapasite_kw) - Number(capKw)) < 0.05) ||
                            y.tarama[idx];
                          const ok = step?.yeterli;
                          return (
                            <td key={y.kod} className="py-3 px-4 text-center whitespace-nowrap">
                              <span
                                className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-md text-xs font-semibold ${
                                  ok
                                    ? 'bg-emerald-50 text-emerald-900 border border-emerald-200'
                                    : 'text-slate-500'
                                }`}
                              >
                                <span aria-hidden="true">{ok ? 'Ô£ô' : 'ÔÇö'}</span>
                                <span>%{step?.hedef_karsilama_yuzde ?? 'ÔÇö'}</span>
                              </span>
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* 5. A├ğ─▒l─▒r Kapsam S─▒n─▒rlar─▒ ve Y├Ântem A├ğ─▒klamalar─▒ */}
          <details className="bg-white border border-slate-200/90 rounded-xl p-4 shadow-2xs group text-xs text-slate-600">
            <summary className="font-semibold text-slate-800 cursor-pointer flex items-center justify-between list-none">
              <span className="flex items-center space-x-2">
                <Info className="w-4 h-4 text-emerald-700 shrink-0" />
                <span>Kapsam S─▒n─▒rlar─▒ ve Y├Ântem A├ğ─▒klamalar─▒</span>
              </span>
              <span className="text-slate-400 group-open:rotate-180 transition-transform">Ôû¥</span>
            </summary>
            <div className="mt-2.5 pt-2.5 border-t border-slate-100 space-y-2 leading-relaxed">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {advisorData.yontemler.map((y) => (
                  <div key={y.kod} className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <strong className="text-slate-800 block">{y.ad}</strong>
                    <span className="text-slate-500">{y.aciklama}</span>
                  </div>
                ))}
              </div>
              <p className="text-slate-500">
                <strong>Kapsam ve Veri Kayna─ş─▒:</strong> {advisorData.veri_kaynagi_etiketi}. Sonu├ğlar yaln─▒zca se├ğili g├╝nl├╝k kesitin ({advisorData.arac_sayisi} ara├ğ) sim├╝lasyon ├ğ─▒kt─▒s─▒d─▒r; genel algoritma ├╝st├╝nl├╝─ş├╝ kan─▒t─▒ olarak yorumlanamaz.
              </p>
            </div>
          </details>
        </>
      )}
    </div>
  );
}

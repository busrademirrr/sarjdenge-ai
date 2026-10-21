import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar.jsx';
import ScenarioSelector from './components/ScenarioSelector.jsx';
import CapacityControl from './components/CapacityControl.jsx';
import CapacityAdvisor from './components/CapacityAdvisor.jsx';
import KpiCards from './components/KpiCards.jsx';
import PowerCurveChart from './components/PowerCurveChart.jsx';
import GanttChart from './components/GanttChart.jsx';
import VehicleInspectorModal from './components/VehicleInspectorModal.jsx';
import BenchmarkView from './components/BenchmarkView.jsx';
import MethodologyView from './components/MethodologyView.jsx';
import ExportModal from './components/ExportModal.jsx';
import AuthModal from './components/AuthModal.jsx';
import Toast from './components/Toast.jsx';
import { ChevronRight, Car, AlertTriangle, CheckCircle2, RefreshCw, Zap, ShieldCheck } from 'lucide-react';
import { formatTimeHour, formatPercent, formatKwh, formatKw } from './utils/formatters.js';
import { supabase, isSupabaseConfigured } from './lib/supabaseClient.js';

export default function App() {
  const [activeTab, setActiveTab] = useState('simulation');
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState('isyeri_gunduz');
  const [f, setF] = useState(0.5);
  const [day, setDay] = useState('2026-03-10');
  const [simulation, setSimulation] = useState(null);
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [session, setSession] = useState(null); // Supabase session veya misafir (null)
  const [loading, setLoading] = useState(false);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [authModalView, setAuthModalView] = useState('signin');
  const [toast, setToast] = useState(null);

  // G├╝venli hata mesaj─▒ temizleyicisi (Token, header veya ham stack trace s─▒zmas─▒n─▒ ├Ânler)
  const sanitizeErrorMessage = (msg) => {
    if (!msg || typeof msg !== 'string') {
      return 'Sim├╝lasyon y├╝r├╝t├╝l├╝rken beklenmeyen bir hata olu┼ştu.';
    }
    let clean = msg
      .replace(/bearer\s+[a-zA-Z0-9_\-\.]+/gi, '[KORUMALI]')
      .replace(/(api[_-]?key|token|auth(orization)?)\s*[:=]\s*[^\s,]+/gi, '$1: [KORUMALI]')
      .replace(/Traceback \(most recent call last\):[\s\S]*/gi, '')
      .trim();
    if (clean.length > 220) {
      clean = clean.slice(0, 217) + '...';
    }
    return clean || 'Sim├╝lasyon y├╝r├╝t├╝l├╝rken bir hata olu┼ştu.';
  };

  // 1. Supabase Auth Durumunu ve ┼Şifre Kurtarma Ba─şlant─▒lar─▒n─▒ Dinle
  useEffect(() => {
    if (!isSupabaseConfigured || !supabase) return;

    // Mevcut aktif oturumu kontrol et
    supabase.auth.getSession().then(({ data: { session: currentSession } }) => {
      if (currentSession) {
        setSession(currentSession);
      }
    });

    // Oturum olaylar─▒n─▒ dinle (Giri┼ş, ├ç─▒k─▒┼ş, ┼Şifre S─▒f─▒rlama)
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, currentSession) => {
      if (event === 'PASSWORD_RECOVERY') {
        setAuthModalView('reset');
        setIsAuthOpen(true);
      } else if (event === 'SIGNED_IN' || event === 'USER_UPDATED') {
        if (currentSession) setSession(currentSession);
      } else if (event === 'SIGNED_OUT') {
        setSession(null);
      }
    });

    // URL hash kontrol├╝ (Kurtarma oturumu linkiyle gelindi─şinde)
    if (
      window.location.hash.includes('type=recovery') ||
      window.location.hash.includes('reset-password')
    ) {
      setAuthModalView('reset');
      setIsAuthOpen(true);
    }

    return () => {
      subscription?.unsubscribe();
    };
  }, []);

  // Kullan─▒c─▒ ├ç─▒k─▒┼ş Yapma ─░┼şlemi
  const handleSignOut = async () => {
    if (supabase) {
      try {
        await supabase.auth.signOut();
      } catch (err) {
        console.error('Sign out error:', err);
      }
    }
    setSession(null);
  };

  const fetchBenchmarkData = async () => {
    try {
      const bmRes = await fetch('/api/benchmark-results');
      const bmData = await bmRes.json();
      if (bmData.success) {
        setBenchmarkData(bmData);
      }
    } catch (err) {
      console.error('Benchmark fetch error:', err);
    }
  };

  // Initial Load: Fetch Scenarios and Benchmarks
  useEffect(() => {
    async function initData() {
      try {
        // Scenarios
        const scRes = await fetch('/api/scenarios');
        const scData = await scRes.json();
        if (scData.success && scData.scenarios) {
          setScenarios(scData.scenarios);
          const defaultSc = scData.scenarios[0];
          setSelectedScenarioId(defaultSc.id);
          setDay(defaultSc.defaultDay);
        }

        // Benchmark data
        await fetchBenchmarkData();
      } catch (err) {
        console.error('Initial data fetch error:', err);
      }
    }

    initData();
  }, []);

  // Run simulation when scenario or day changes
  const runSimulation = async (scId = selectedScenarioId, fVal = f, dayVal = day, isRetry = false) => {
    setLoading(true);
    if (!isRetry) {
      setToast(null); // Yeni ba─ş─▒ms─▒z sim├╝lasyon ba┼şlarken ├Ânceki Toast'─▒ temizle
    }
    try {
      const res = await fetch('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenarioId: scId,
          f: fVal,
          day: dayVal,
        }),
      });

      const data = await res.json();
      if (data.success && data.simulation) {
        setSimulation(data.simulation);
        setToast(null); // Ba┼şar─▒l─▒ sim├╝lasyonda ├Ânceki hata uyar─▒s─▒n─▒ kapat
      } else {
        const errorText = sanitizeErrorMessage(data.error);
        setToast({
          id: Date.now(),
          type: 'error',
          title: 'Sim├╝lasyon Y├╝r├╝t├╝lemedi',
          message: errorText,
          canRetry: true,
          retryParams: { scId, fVal, dayVal },
        });
      }
    } catch (err) {
      console.error('Simulation run error:', err);
      setToast({
        id: Date.now(),
        type: 'error',
        title: 'Ba─şlant─▒ Hatas─▒',
        message: 'Sim├╝lasyon servisine ba─şlan─▒lamad─▒. L├╝tfen sunucunun ├ğal─▒┼şt─▒─ş─▒ndan emin olun.',
        canRetry: true,
        retryParams: { scId, fVal, dayVal },
      });
    } finally {
      setLoading(false);
    }
  };

  // Toast ├╝zerinden ayn─▒ parametrelerle yeniden deneme
  const handleRetrySimulation = () => {
    if (!toast?.retryParams || loading) return;
    const { scId, fVal, dayVal } = toast.retryParams;
    runSimulation(scId, fVal, dayVal, true);
  };

  // Run initial simulation once scenarios are ready
  useEffect(() => {
    if (scenarios.length > 0) {
      runSimulation(selectedScenarioId, f, day);
    }
  }, [scenarios]);

  // Handle Scenario Switch
  const handleSelectScenario = (id) => {
    const sc = scenarios.find((s) => s.id === id);
    setSelectedScenarioId(id);
    if (sc) {
      const newDay = sc.defaultDay || sc.availableDays?.[0] || '2026-03-10';
      setDay(newDay);
      runSimulation(id, f, newDay);
    }
  };

  // Handle Day Switch
  const handleChangeDay = (newDay) => {
    setDay(newDay);
    runSimulation(selectedScenarioId, f, newDay);
  };

  // Handle F Ratio Switch
  const handleChangeF = (newF) => {
    setF(newF);
    runSimulation(selectedScenarioId, newF, day);
  };

  const currentScenario = scenarios.find((s) => s.id === selectedScenarioId) || scenarios[0];

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-900 flex flex-col font-sans">
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        session={session}
        onOpenExport={() => setIsExportOpen(true)}
        onOpenAuth={() => {
          setAuthModalView('signin');
          setIsAuthOpen(true);
        }}
        onSignOut={handleSignOut}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Tab 1: Live Simulation */}
        {activeTab === 'simulation' && (
          <div>
            {/* 1. Scenario Selector */}
            <ScenarioSelector
              scenarios={scenarios}
              selectedScenarioId={selectedScenarioId}
              onSelectScenario={handleSelectScenario}
            />

            {/* 2. Capacity Control & Run Button */}
            <CapacityControl
              scenario={currentScenario}
              f={f}
              onChangeF={handleChangeF}
              day={day}
              onChangeDay={handleChangeDay}
              onRunSimulation={() => runSimulation(selectedScenarioId, f, day)}
              loading={loading}
              simSummary={simulation}
            />

            {/* Sleek Single-Line Context & Capacity Advisor Bar */}
            <div className="bg-white border border-slate-200/90 rounded-xl px-4 py-2.5 mb-5 flex flex-col lg:flex-row lg:items-center justify-between gap-3 shadow-2xs">
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-slate-600 tabular-nums">
                <span className="inline-flex items-center space-x-1.5 font-semibold text-slate-900">
                  <span className="w-2 h-2 rounded-full bg-emerald-600 shrink-0" />
                  <span>{currentScenario?.name || simulation?.senaryo_bilgi?.name || 'Aktif Senaryo'}</span>
                </span>
                {simulation && (
                  <>
                    <span className="text-slate-300 hidden sm:inline">|</span>
                    <span>
                      Oturum: <strong className="text-slate-900">{simulation.arac_sayisi} Ara├ğ</strong> ({formatKwh(simulation.talep_toplam_kwh)})
                    </span>
                    <span className="text-slate-300 hidden sm:inline">|</span>
                    <span>
                      Tavan: <strong className="text-slate-900">{formatKw(simulation.kapasite_siniri_kw)}</strong> / Pik: <strong className="text-slate-700">{formatKw(simulation.kontrolsuz_tepe_kw)}</strong>
                    </span>
                    <span className="text-slate-300 hidden sm:inline">|</span>
                    <span className="inline-flex items-center space-x-1 text-emerald-800 font-semibold">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                      <span>0,0 kW ─░hlal</span>
                    </span>
                  </>
                )}
              </div>

              <button
                onClick={() => setActiveTab('advisor')}
                className="text-xs font-semibold text-emerald-800 hover:text-emerald-950 bg-emerald-50/80 hover:bg-emerald-100/80 border border-emerald-200/90 px-3 py-1.5 rounded-lg inline-flex items-center space-x-1 self-start lg:self-auto shrink-0 transition"
              >
                <span>Asgari Trafo Kapasite Dan─▒┼şman─▒</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Loading State when simulation is not yet available */}
            {loading && !simulation && (
              <div className="bg-white border border-slate-200 rounded-xl py-8 px-4 mb-5 flex items-center justify-center space-x-2.5 shadow-2xs">
                <RefreshCw className="w-4 h-4 text-emerald-700 animate-spin shrink-0" />
                <span className="text-xs font-semibold text-slate-700">
                  Sim├╝lasyon hesaplan─▒yorÔÇĞ
                </span>
              </div>
            )}

            {/* Empty / Error Fallback State when simulation failed and no previous data exists */}
            {!loading && !simulation && (
              <div className="bg-white border border-slate-200 rounded-xl p-6 mb-5 text-center shadow-2xs">
                <AlertTriangle className="w-5 h-5 text-amber-600 mx-auto mb-2" />
                <h3 className="text-sm font-bold text-slate-900">
                  Sim├╝lasyon Verisi Hen├╝z Y├╝klenemedi
                </h3>
                <button
                  type="button"
                  onClick={() => runSimulation(selectedScenarioId, f, day)}
                  className="mt-3 inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-700 hover:bg-emerald-800 text-white transition shadow-2xs"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Sim├╝lasyonu Ba┼şlat</span>
                </button>
              </div>
            )}

            {/* 3. KPI Comparison Cards */}
            <KpiCards kpis={simulation?.kpi_ozet} simulation={simulation} />

            {/* 4. 24-Hour Load Curve */}
            <PowerCurveChart simulation={simulation} />

            {/* 5. Gantt Timeline */}
            <GanttChart
              simulation={simulation}
              onSelectVehicle={(v) => setSelectedVehicle(v)}
            />

            {/* 6. Vehicle List & "Why?" Table */}
            {simulation?.araclar && (
              <section className="bg-white border border-slate-200/90 rounded-xl p-4 sm:p-5 mt-5 shadow-2xs" aria-label="Oturum Bazl─▒ Karar ├ûzeti">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3.5">
                  <div className="flex items-center space-x-2">
                    <Car className="w-4 h-4 text-emerald-700 shrink-0" />
                    <h3 className="font-semibold text-sm sm:text-base text-slate-900">
                      Oturum Bazl─▒ Karar ├ûzeti
                    </h3>
                    <span className="text-xs text-slate-500">
                      (Detay i├ğin sat─▒ra t─▒klay─▒n)
                    </span>
                  </div>
                  <span className="text-xs text-slate-600 self-start sm:self-auto bg-slate-100 px-2.5 py-1 rounded-md font-medium tabular-nums">
                    {simulation.arac_sayisi} Ara├ğ
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs tabular-nums">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-700 bg-slate-50/80 font-semibold">
                        <th className="py-3 px-3 whitespace-nowrap">Ara├ğ ID</th>
                        <th className="py-3 px-3 whitespace-nowrap">Giri┼ş ÔÇô ├ç─▒k─▒┼ş</th>
                        <th className="py-3 px-3 text-right whitespace-nowrap">Ger├ğek Talep</th>
                        <th className="py-3 px-3 text-right whitespace-nowrap">Ôùê EDF G├╝venli</th>
                        <th className="py-3 px-3 text-right whitespace-nowrap">ÔùÅ MPC G├╝venli</th>
                        <th className="py-3 px-3 text-right whitespace-nowrap">Ôû▓ FCFS</th>
                        <th className="py-3 px-3 min-w-[240px]">Fiziksel Karar ├ûzeti</th>
                        <th className="py-3 px-3 text-center whitespace-nowrap">─░ncele</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {simulation.araclar.map((v) => {
                        const satEdf = v.doyum_orani.edf_tahmin_guvenli >= 0.95;
                        const satMpc = v.doyum_orani.mpc_tahmin_guvenli >= 0.95;
                        const satFcfs = v.doyum_orani.fcfs_beyan >= 0.95;

                        return (
                          <tr
                            key={v.arac_id}
                            onClick={() => setSelectedVehicle(v)}
                            className="hover:bg-slate-50/90 cursor-pointer transition align-middle"
                          >
                            <td className="py-3 px-3 text-slate-900 font-semibold whitespace-nowrap">
                              <div className="flex items-center space-x-1.5">
                                <span>{v.arac_id}</span>
                                {v.erken_ayrildi && (
                                  <span
                                    className="text-xs px-1.5 py-0.5 rounded bg-amber-50 text-amber-900 border border-amber-200 font-semibold"
                                    title="Planlanandan Erken Ayr─▒ld─▒"
                                  >
                                    Erken
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="py-3 px-3 text-slate-700 whitespace-nowrap">
                              {formatTimeHour(v.giris_saat)} ÔÇô {formatTimeHour(v.ayril_saat)}
                            </td>
                            <td className="py-3 px-3 text-right text-slate-900 font-semibold whitespace-nowrap">
                              {formatKwh(v.talep_gercek_kwh)}
                            </td>
                            <td className="py-3 px-3 text-right whitespace-nowrap">
                              <span className={satEdf ? 'text-emerald-800 font-bold' : 'text-amber-800 font-semibold'}>
                                {satEdf ? 'Ô£ô ' : '! '}
                                {formatPercent(v.doyum_orani.edf_tahmin_guvenli, 0, true)}
                              </span>
                            </td>
                            <td className="py-3 px-3 text-right whitespace-nowrap">
                              <span className={satMpc ? 'text-emerald-800 font-bold' : 'text-amber-800 font-semibold'}>
                                {satMpc ? 'Ô£ô ' : '! '}
                                {formatPercent(v.doyum_orani.mpc_tahmin_guvenli, 0, true)}
                              </span>
                            </td>
                            <td className="py-3 px-3 text-right whitespace-nowrap">
                              <span className={satFcfs ? 'text-emerald-800 font-semibold' : 'text-slate-600 font-medium'}>
                                {satFcfs ? 'Ô£ô ' : 'ÔÇö '}
                                {formatPercent(v.doyum_orani.fcfs_beyan, 0, true)}
                              </span>
                            </td>
                            <td className="py-3 px-3 text-slate-700 text-xs leading-snug min-w-[240px] max-w-md">
                              {v.neden_analizi?.ozet_hukum}
                            </td>
                            <td className="py-3 px-3 text-center whitespace-nowrap">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setSelectedVehicle(v);
                                }}
                                className="px-3 py-1 rounded-lg bg-slate-100 hover:bg-emerald-700 text-slate-800 hover:text-white text-xs font-semibold transition"
                              >
                                Neden?
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </section>
            )}
          </div>
        )}

        {/* Tab 2: Capacity Advisor */}
        {activeTab === 'advisor' && (
          <CapacityAdvisor
            scenarios={scenarios}
            selectedScenarioId={selectedScenarioId}
            onSelectScenario={handleSelectScenario}
            day={day}
            onChangeDay={handleChangeDay}
          />
        )}

        {/* Tab 3: Verification & Benchmarks */}
        {activeTab === 'benchmark' && (
          <BenchmarkView benchmarkData={benchmarkData} onRetry={fetchBenchmarkData} />
        )}

        {/* Tab 4: Methodology & Glossary */}
        {activeTab === 'methodology' && (
          <MethodologyView />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200/70 bg-[#F8FAFC] py-2.5 text-center">
        <span className="text-[11px] font-medium tracking-wide text-slate-500">
          ┼ŞarjDenge AI
        </span>
      </footer>

      {/* Modals */}
      {selectedVehicle && (
        <VehicleInspectorModal
          vehicle={selectedVehicle}
          onClose={() => setSelectedVehicle(null)}
        />
      )}

      {isExportOpen && (
        <ExportModal
          simulation={simulation}
          onClose={() => setIsExportOpen(false)}
        />
      )}

      {/* Supabase Authentication Modal (Giri┼ş / Kay─▒t / ┼Şifre Yenileme) */}
      {isAuthOpen && (
        <AuthModal
          isOpen={isAuthOpen}
          initialView={authModalView}
          onClose={() => setIsAuthOpen(false)}
          onAuthSuccess={(newSession) => {
            setSession(newSession);
          }}
        />
      )}

      {/* Accessible Toast Notification */}
      <Toast
        toast={toast}
        onClose={() => setToast(null)}
        onRetry={handleRetrySimulation}
        retryLoading={loading}
      />
    </div>
  );
}

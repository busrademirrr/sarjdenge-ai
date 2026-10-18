import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar.jsx';
import TransparencyBanner from './components/TransparencyBanner.jsx';
import ScenarioSelector from './components/ScenarioSelector.jsx';
import CapacityControl from './components/CapacityControl.jsx';
import KpiCards from './components/KpiCards.jsx';
import PowerCurveChart from './components/PowerCurveChart.jsx';
import GanttChart from './components/GanttChart.jsx';
import VehicleInspectorModal from './components/VehicleInspectorModal.jsx';
import BenchmarkView from './components/BenchmarkView.jsx';
import MethodologyView from './components/MethodologyView.jsx';
import ExportModal from './components/ExportModal.jsx';
import AuthModal from './components/AuthModal.jsx';
import { HelpCircle, ChevronRight, RefreshCw, Car } from 'lucide-react';
import { formatTimeHour, formatPercent, formatKwh } from './utils/formatters.js';

export default function App() {
  const [activeTab, setActiveTab] = useState('simulation');
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState('isyeri_gunduz');
  const [f, setF] = useState(0.5);
  const [day, setDay] = useState('2026-03-10');
  const [simulation, setSimulation] = useState(null);
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [session, setSession] = useState({ isAuthenticated: true, isGuest: true, user: { name: 'Jüri Üyesi (Misafir)' } });
  const [loading, setLoading] = useState(false);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [isAuthOpen, setIsAuthOpen] = useState(false);

  // Initial Load: Fetch Scenarios, Session, and Benchmarks
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

        // Auth status
        const authRes = await fetch('/api/auth/status');
        const authData = await authRes.json();
        if (authData.success && authData.session) {
          setSession(authData.session);
        }

        // Benchmark data
        const bmRes = await fetch('/api/benchmark-results');
        const bmData = await bmRes.json();
        if (bmData.success) {
          setBenchmarkData(bmData);
        }
      } catch (err) {
        console.error('Initial data fetch error:', err);
      }
    }

    initData();
  }, []);

  // Run simulation when scenario or day changes
  const runSimulation = async (scId = selectedScenarioId, fVal = f, dayVal = day) => {
    setLoading(true);
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
      } else {
        alert(data.error || 'Simülasyon yürütülürken hata oluştu.');
      }
    } catch (err) {
      console.error('Simulation run error:', err);
      alert('Simülasyon servisine bağlanılamadı.');
    } finally {
      setLoading(false);
    }
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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        session={session}
        onOpenAuth={() => setIsAuthOpen(true)}
        onOpenExport={() => setIsExportOpen(true)}
        onOpenHelp={() => setActiveTab('methodology')}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Tab 1: Live Simulation */}
        {activeTab === 'simulation' && (
          <div>
            {/* Scientific Transparency Banner (Compact status on simulation tab) */}
            <TransparencyBanner />

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
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 sm:p-5 mt-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
                  <div>
                    <div className="flex items-center space-x-2">
                      <Car className="w-4 h-4 text-emerald-400" />
                      <h3 className="font-bold text-xs sm:text-sm text-white">
                        Simüle Edilen Araç Listesi ve Fiziksel Karar Denetçisi
                      </h3>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Herhangi bir satıra veya "Neden?" butonuna tıklayarak batarya şarj dinamiklerini ve karar gerekçelerini inceleyebilirsiniz.
                    </p>
                  </div>
                  <span className="text-xs font-mono text-slate-400 self-start sm:self-auto bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
                    Toplam: {simulation.arac_sayisi} Araç
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400">
                        <th className="py-2.5 px-3">Araç ID</th>
                        <th className="py-2.5 px-3">Giriş – Çıkış</th>
                        <th className="py-2.5 px-3 text-right">Gerçek Talep</th>
                        <th className="py-2.5 px-3 text-right">EDF Güvenli</th>
                        <th className="py-2.5 px-3 text-right">MPC Güvenli</th>
                        <th className="py-2.5 px-3 text-right">FCFS</th>
                        <th className="py-2.5 px-3">Fiziksel Karar Özeti</th>
                        <th className="py-2.5 px-3 text-center">İncele</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {simulation.araclar.map((v) => {
                        const satEdf = v.doyum_orani.edf_tahmin_guvenli >= 0.95;
                        const satMpc = v.doyum_orani.mpc_tahmin_guvenli >= 0.95;
                        const satFcfs = v.doyum_orani.fcfs_beyan >= 0.95;

                        return (
                          <tr
                            key={v.arac_id}
                            onClick={() => setSelectedVehicle(v)}
                            className="hover:bg-slate-800/40 cursor-pointer transition"
                          >
                            <td className="py-2.5 px-3 text-white font-semibold flex items-center space-x-1.5">
                              <span>{v.arac_id}</span>
                              {v.erken_ayrildi && (
                                <span className="text-[10px] px-1 py-0.2 rounded bg-amber-500/20 text-amber-300 font-sans border border-amber-500/30" title="Planlanandan Erken Ayrıldı">
                                  Erken
                                </span>
                              )}
                            </td>
                            <td className="py-2.5 px-3 text-slate-300">
                              {formatTimeHour(v.giris_saat)} – {formatTimeHour(v.ayril_saat)}
                            </td>
                            <td className="py-2.5 px-3 text-right text-slate-200">
                              {formatKwh(v.talep_gercek_kwh)}
                            </td>
                            <td className="py-2.5 px-3 text-right">
                              <span className={satEdf ? 'text-emerald-400 font-bold' : 'text-amber-400'}>
                                {formatPercent(v.doyum_orani.edf_tahmin_guvenli, 0, true)}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 text-right">
                              <span className={satMpc ? 'text-emerald-400 font-bold' : 'text-amber-400'}>
                                {formatPercent(v.doyum_orani.mpc_tahmin_guvenli, 0, true)}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 text-right">
                              <span className={satFcfs ? 'text-emerald-400' : 'text-slate-500'}>
                                {formatPercent(v.doyum_orani.fcfs_beyan, 0, true)}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 text-slate-300 truncate max-w-xs font-sans text-[11px]">
                              {v.neden_analizi?.ozet_hukum}
                            </td>
                            <td className="py-2.5 px-3 text-center">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setSelectedVehicle(v);
                                }}
                                className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-emerald-600 text-slate-300 hover:text-white text-[11px] font-sans font-medium transition"
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
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Verification & Benchmarks */}
        {activeTab === 'benchmark' && (
          <BenchmarkView benchmarkData={benchmarkData} />
        )}

        {/* Tab 3: Methodology & Glossary */}
        {activeTab === 'methodology' && (
          <MethodologyView />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900/60 py-6 text-xs text-slate-500 text-center">
        <div className="max-w-7xl mx-auto px-4 space-y-1">
          <p className="text-slate-400">
            <strong>ŞarjDenge AI</strong> — Climathon 2026 Otopark Akıllı Şarj ve Kapasite Planlayıcı
          </p>
          <p>
            Dondurulmuş Çekirdek Kuralı: data.py, sim.py, tahmin.py, deney.py ve 2020 holdout verisi korunmuştur.
          </p>
          <p className="text-[11px]">
            Frontend: React + Tailwind CSS • Backend: Node.js • ML/Simülasyon: Python 3.12 (Quantile Regressor + MPC)
          </p>
        </div>
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

      {isAuthOpen && (
        <AuthModal
          session={session}
          onUpdateSession={(s) => setSession(s)}
          onClose={() => setIsAuthOpen(false)}
        />
      )}
    </div>
  );
}

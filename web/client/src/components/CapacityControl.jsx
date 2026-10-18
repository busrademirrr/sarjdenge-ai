import React from 'react';
import { Sliders, Play, Calendar, Zap, RefreshCw } from 'lucide-react';
import { formatKw, formatPercent } from '../utils/formatters.js';

export default function CapacityControl({
  scenario,
  f,
  onChangeF,
  day,
  onChangeDay,
  onRunSimulation,
  loading,
  simSummary,
}) {
  const fPresets = [
    { value: 0.4, label: 'f = 0,40 (%40 - Aşırı Kısıtlı)' },
    { value: 0.5, label: 'f = 0,50 (%50 - Temel Deney)' },
    { value: 0.7, label: 'f = 0,70 (%70 - Orta Kapasite)' },
    { value: 0.9, label: 'f = 0,90 (%90 - Geniş Kapasite)' },
  ];

  const currentCapKw = simSummary?.kapasite_siniri_kw || (f * (scenario?.transformerKw || 100));

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 sm:p-5 mb-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5">
        {/* Left: Capacity Ratio Slider & Quick Presets */}
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-emerald-400" />
              <label className="text-xs sm:text-sm font-bold text-white">
                Şarj Gücü Tavan Katsayısı (f = {Number(f).toFixed(2).replace('.', ',')})
              </label>
            </div>
            <div className="text-xs font-mono px-2.5 py-1 rounded-lg bg-slate-950 text-emerald-400 font-semibold border border-slate-800">
              Tavan: {formatPercent(f * 100, 0)} • {formatKw(currentCapKw)}
            </div>
          </div>

          <p className="text-[11px] text-slate-400 mb-2">
            Şarj altyapısına ayrılabilir anlık azami güç tavanıdır (kontrolsüz pik yükün f katı olarak belirlenir).
          </p>

          <input
            type="range"
            min="0.35"
            max="1.0"
            step="0.05"
            value={f}
            onChange={(e) => onChangeF(parseFloat(e.target.value))}
            className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
          />

          {/* Preset Buttons */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 mt-2.5">
            {fPresets.map((item) => {
              const isActive = Math.abs(f - item.value) < 0.01;
              return (
                <button
                  key={item.value}
                  onClick={() => onChangeF(item.value)}
                  className={`px-2 py-1 rounded-md text-[11px] font-medium transition text-center ${
                    isActive
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-bold'
                      : 'bg-slate-950/60 hover:bg-slate-800 text-slate-400 border border-slate-800/80'
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Center: Day Selector */}
        <div className="lg:w-64 border-t lg:border-t-0 lg:border-l border-slate-800 lg:pl-5 pt-3 lg:pt-0">
          <label className="text-xs font-bold text-slate-300 flex items-center space-x-1.5 mb-1.5">
            <Calendar className="w-3.5 h-3.5 text-emerald-400" />
            <span>Simülasyon Günü</span>
          </label>
          <select
            value={day}
            onChange={(e) => onChangeDay(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-3 py-2 text-xs font-mono focus:outline-none focus:border-emerald-500"
          >
            {scenario?.availableDays?.map((d) => (
              <option key={d} value={d}>
                {d} {scenario.badgeType === 'real' ? '(Saha Oturumları)' : '(Sentetik Örnek)'}
              </option>
            ))}
          </select>
          <p className="text-[10px] text-slate-500 mt-1">
            {scenario?.badgeType === 'real' ? 'ACN-Data doğrulanmış yoğun günü' : 'Parametrelerle üretilmiş sentetik gün'}
          </p>
        </div>

        {/* Right: Run Button */}
        <div className="flex items-center">
          <button
            onClick={onRunSimulation}
            disabled={loading}
            className={`w-full lg:w-auto flex items-center justify-center space-x-2 px-6 py-3 rounded-xl font-bold text-xs sm:text-sm transition-all shadow-lg ${
              loading
                ? 'bg-emerald-900/60 text-slate-400 border border-emerald-800/60 cursor-not-allowed'
                : 'bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-slate-950 shadow-emerald-500/20 active:scale-95'
            }`}
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin text-slate-300" />
                <span>Simüle Ediliyor…</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-slate-950 stroke-slate-950" />
                <span>Simülasyonu Çalıştır</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

import React from 'react';
import { Sliders, Play, Calendar, RefreshCw } from 'lucide-react';
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
    { value: 0.4, label: 'f = 0,40' },
    { value: 0.5, label: 'f = 0,50' },
    { value: 0.7, label: 'f = 0,70' },
    { value: 0.9, label: 'f = 0,90' },
  ];

  const currentCapKw = simSummary?.kapasite_siniri_kw || f * (scenario?.transformerKw || 100);

  return (
    <div className="bg-white border border-slate-200/90 rounded-xl p-3.5 mb-3.5 shadow-2xs">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3.5">
        {/* Left: Capacity Slider + Ratio/kW + Presets */}
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center space-x-2">
              <Sliders className="w-3.5 h-3.5 text-emerald-700" />
              <span className="text-xs font-semibold text-slate-900">
                Kapasite Tavan─▒
              </span>
            </div>
            <span className="text-xs px-2 py-0.5 rounded-md bg-slate-100 text-slate-800 font-semibold tabular-nums">
              f = {Number(f).toFixed(2).replace('.', ',')} ({formatPercent(f * 100, 0)} ÔÇó {formatKw(currentCapKw)})
            </span>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            <input
              type="range"
              min="0.35"
              max="1.0"
              step="0.05"
              value={f}
              onChange={(e) => onChangeF(parseFloat(e.target.value))}
              className="flex-1 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-emerald-700"
            />

            <div className="grid grid-cols-4 gap-1.5 shrink-0">
              {fPresets.map((item) => {
                const isActive = Math.abs(f - item.value) < 0.01;
                return (
                  <button
                    key={item.value}
                    type="button"
                    onClick={() => onChangeF(item.value)}
                    className={`px-2 py-1 rounded-md text-[11px] transition tabular-nums text-center ${
                      isActive
                        ? 'bg-emerald-700 text-white font-semibold'
                        : 'bg-slate-100 hover:bg-slate-200/70 text-slate-700 font-medium'
                    }`}
                  >
                    {item.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right: Date Selector & Run Button on the same row */}
        <div className="flex items-center gap-2.5 lg:border-l border-slate-100 lg:pl-4 shrink-0">
          <div className="flex items-center space-x-1.5">
            <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <select
              value={day}
              onChange={(e) => onChangeDay(e.target.value)}
              aria-label="Sim├╝lasyon G├╝n├╝"
              className="bg-slate-50 border border-slate-200 text-slate-900 rounded-lg px-2.5 py-1.5 text-xs tabular-nums focus:outline-none focus:border-emerald-600 focus:bg-white"
            >
              {scenario?.availableDays?.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              )) || <option value={day}>{day}</option>}
            </select>
          </div>

          <button
            onClick={onRunSimulation}
            disabled={loading}
            className={`flex items-center justify-center space-x-1.5 px-3.5 py-1.5 rounded-lg font-semibold text-xs transition-all whitespace-nowrap ${
              loading
                ? 'bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed'
                : 'bg-emerald-700 hover:bg-emerald-800 text-white shadow-2xs'
            }`}
          >
            {loading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-slate-400" />
                <span>├çal─▒┼şt─▒r─▒l─▒yorÔÇĞ</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-white stroke-white" />
                <span>Sim├╝lasyonu ├çal─▒┼şt─▒r</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

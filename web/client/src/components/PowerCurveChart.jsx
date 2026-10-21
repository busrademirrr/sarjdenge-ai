import React, { useState } from 'react';
import { Activity } from 'lucide-react';
import { formatKw } from '../utils/formatters.js';
import { ALGORITHM_META } from '../utils/algorithmMeta.js';

export default function PowerCurveChart({ simulation }) {
  if (!simulation || !simulation.zaman_etiketleri) return null;

  const [visibleSeries, setVisibleSeries] = useState({
    fcfs_beyan: true,
    edf_beyan: true,
    edf_tahmin_guvenli: true,
    mpc_beyan: true,
    mpc_tahmin_guvenli: true,
    mpc_hibrit_asimetrik: false,
    kontrolsuz: true,
    kapasite: true,
  });

  const [hoveredIdx, setHoveredIdx] = useState(null);

  const seriesMeta = [
    ALGORITHM_META.fcfs_beyan,
    ALGORITHM_META.edf_beyan,
    ALGORITHM_META.edf_tahmin_guvenli,
    ALGORITHM_META.mpc_beyan,
    ALGORITHM_META.mpc_tahmin_guvenli,
    ALGORITHM_META.mpc_hibrit_asimetrik,
  ];

  const timeLabels = simulation.zaman_etiketleri; // 96 steps
  const capLimit = simulation.kapasite_siniri_kw || 50;
  const unctrl = simulation.kontrolsuz_profil_kw || [];

  // Determine max Y value for SVG scaling
  let maxY = Math.max(capLimit, ...(unctrl || [0]));
  seriesMeta.forEach((s) => {
    const prof = simulation.yontem_profilleri[s.key] || [];
    maxY = Math.max(maxY, ...prof);
  });
  maxY = Math.ceil(maxY * 1.15) || 50;

  // Chart dimensions
  const svgWidth = 960;
  const svgHeight = 300;
  const padding = { top: 24, right: 32, bottom: 40, left: 64 };
  const graphWidth = svgWidth - padding.left - padding.right;
  const graphHeight = svgHeight - padding.top - padding.bottom;

  const getX = (idx) => padding.left + (idx / 95) * graphWidth;
  const getY = (val) => padding.top + graphHeight - (val / maxY) * graphHeight;

  // Helper to generate SVG path
  const makePath = (data) => {
    if (!data || data.length === 0) return '';
    return data.map((v, i) => `${i === 0 ? 'M' : 'L'} ${getX(i).toFixed(1)} ${getY(v).toFixed(1)}`).join(' ');
  };

  const toggleSeries = (key) => {
    setVisibleSeries((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // Hovered details
  const activeHover = hoveredIdx !== null ? {
    time: timeLabels[hoveredIdx],
    unctrl: unctrl[hoveredIdx],
    series: seriesMeta.map((s) => ({
      ...s,
      val: (simulation.yontem_profilleri[s.key] || [])[hoveredIdx] || 0,
    })),
  } : null;

  return (
    <section className="bg-white border border-slate-200/90 rounded-xl p-4 sm:p-5 mb-4 shadow-2xs" aria-label="24 Saatlik G├╝├ğ E─şrisi">
      {/* Compact Header & Legend */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-2.5 mb-2.5">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-emerald-700 shrink-0" />
          <h3 className="font-semibold text-sm sm:text-base text-slate-900">
            24 Saatlik G├╝├ğ E─şrisi
          </h3>
          <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-rose-50 text-rose-800 border border-rose-200/80 tabular-nums">
            Tavan: {formatKw(capLimit)}
          </span>
        </div>

        {/* Compact Legend Toggles */}
        <div className="flex items-center flex-wrap gap-1.5 text-[11px]">
          {seriesMeta.map((s) => {
            const isVis = visibleSeries[s.key];
            return (
              <button
                key={s.key}
                type="button"
                onClick={() => toggleSeries(s.key)}
                aria-pressed={isVis}
                className={`flex items-center space-x-1.5 px-2 py-0.5 rounded-md border transition whitespace-nowrap ${
                  isVis
                    ? 'bg-white border-slate-200/90 text-slate-800 font-medium shadow-2xs'
                    : 'bg-slate-50 border-slate-200/60 text-slate-400 line-through'
                }`}
              >
                <svg className="w-3 h-2 shrink-0" viewBox="0 0 16 8" aria-hidden="true">
                  <line
                    x1="0"
                    y1="4"
                    x2="16"
                    y2="4"
                    stroke={s.color}
                    strokeWidth="2.5"
                    strokeDasharray={s.dashArray === 'none' ? undefined : s.dashArray}
                  />
                </svg>
                <span>{s.shortName}</span>
              </button>
            );
          })}
          <button
            type="button"
            onClick={() => toggleSeries('kontrolsuz')}
            aria-pressed={visibleSeries.kontrolsuz}
            className={`flex items-center space-x-1.5 px-2 py-0.5 rounded-md border transition whitespace-nowrap ${
              visibleSeries.kontrolsuz
                ? 'bg-white border-slate-200/90 text-slate-700 font-medium shadow-2xs'
                : 'bg-slate-50 border-slate-200/60 text-slate-400 line-through'
            }`}
          >
            <svg className="w-3 h-2 shrink-0" viewBox="0 0 16 8" aria-hidden="true">
              <line x1="0" y1="4" x2="16" y2="4" stroke="#64748b" strokeWidth="2" strokeDasharray="3 3" />
            </svg>
            <span>Kontrols├╝z</span>
          </button>
        </div>
      </div>

      {/* SVG Interactive Chart */}
      <div className="relative overflow-x-auto pb-1">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full h-auto min-w-[680px] select-none"
          onMouseLeave={() => setHoveredIdx(null)}
          onMouseMove={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const relX = (e.clientX - rect.left) * (svgWidth / rect.width);
            const clampedX = Math.max(padding.left, Math.min(padding.left + graphWidth, relX));
            const step = Math.round(((clampedX - padding.left) / graphWidth) * 95);
            setHoveredIdx(Math.max(0, Math.min(95, step)));
          }}
        >
          {/* Horizontal Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1.0].map((ratio) => {
            const val = ratio * maxY;
            const y = getY(val);
            return (
              <g key={ratio}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={padding.left + graphWidth}
                  y2={y}
                  stroke="#e2e8f0"
                  strokeDasharray="4 4"
                />
                <text
                  x={padding.left - 10}
                  y={y + 4}
                  fill="#334155"
                  fontSize="12"
                  fontWeight="500"
                  textAnchor="end"
                >
                  {val.toFixed(0)} kW
                </text>
              </g>
            );
          })}

          {/* Vertical Time Labels (Every 3 hours = 12 steps) */}
          {Array.from({ length: 9 }).map((_, i) => {
            const stepIdx = i * 12;
            const x = getX(stepIdx);
            const label = timeLabels[stepIdx] || '';
            return (
              <g key={stepIdx}>
                <line
                  x1={x}
                  y1={padding.top}
                  x2={x}
                  y2={padding.top + graphHeight}
                  stroke="#f1f5f9"
                  strokeWidth="1"
                />
                <text
                  x={x}
                  y={padding.top + graphHeight + 22}
                  fill="#334155"
                  fontSize="12"
                  fontWeight="500"
                  textAnchor="middle"
                >
                  {label}
                </text>
              </g>
            );
          })}

          {/* Uncontrolled Profile (Dotted Slate) */}
          {visibleSeries.kontrolsuz && unctrl.length > 0 && (
            <path
              d={makePath(unctrl)}
              fill="none"
              stroke="#64748b"
              strokeWidth="1.8"
              strokeDasharray="3 3"
              opacity="0.85"
            />
          )}

          {/* Algorithm Power Curves (Color + Distinct Dash Pattern) */}
          {seriesMeta.map((s) => {
            if (!visibleSeries[s.key]) return null;
            const prof = simulation.yontem_profilleri[s.key] || [];
            return (
              <path
                key={s.key}
                d={makePath(prof)}
                fill="none"
                stroke={s.color}
                strokeWidth={s.strokeWidth}
                strokeDasharray={s.dashArray === 'none' ? undefined : s.dashArray}
                opacity={s.key === 'mpc_tahmin_guvenli' ? 1.0 : 0.9}
              />
            );
          })}

          {/* Capacity Limit Line (Dashed Rose) */}
          {visibleSeries.kapasite && (
            <g>
              <line
                x1={padding.left}
                y1={getY(capLimit)}
                x2={padding.left + graphWidth}
                y2={getY(capLimit)}
                stroke="#be123c"
                strokeWidth="2.2"
                strokeDasharray="6 4"
              />
              <rect
                x={padding.left + graphWidth - 132}
                y={Math.max(4, getY(capLimit) - 24)}
                width="126"
                height="20"
                rx="4"
                fill="#fff1f2"
                stroke="#fecdd3"
              />
              <text
                x={padding.left + graphWidth - 12}
                y={Math.max(18, getY(capLimit) - 10)}
                fill="#be123c"
                fontSize="12"
                fontWeight="bold"
                textAnchor="end"
              >
                Tavan: {capLimit.toFixed(1).replace('.', ',')} kW
              </text>
            </g>
          )}

          {/* Hover Cursor Vertical Line */}
          {hoveredIdx !== null && (
            <line
              x1={getX(hoveredIdx)}
              y1={padding.top}
              x2={getX(hoveredIdx)}
              y2={padding.top + graphHeight}
              stroke="#0f172a"
              strokeWidth="1"
              strokeDasharray="2 2"
            />
          )}
        </svg>

        {/* Hover Tooltip Box */}
        {activeHover && (
          <div
            className="absolute top-2 right-4 bg-white/95 backdrop-blur-md border border-slate-200/90 rounded-xl p-3 shadow-lg text-xs pointer-events-none transition-all z-10 tabular-nums"
            style={{ minWidth: '230px' }}
          >
            <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-slate-100">
              <span className="font-bold text-slate-900">Saat: {activeHover.time}</span>
              <span className="text-xs text-slate-500">15 dk Ad─▒m</span>
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between text-slate-600">
                <span>Kontrols├╝z Pik:</span>
                <span className="font-semibold text-slate-900">{formatKw(activeHover.unctrl)}</span>
              </div>

              {activeHover.series.map((s) => {
                if (!visibleSeries[s.key]) return null;
                return (
                  <div key={s.key} className="flex items-center justify-between gap-2">
                    <span className="flex items-center space-x-1.5 font-medium" style={{ color: s.color }}>
                      <span aria-hidden="true">{s.symbol}</span>
                      <span>{s.shortName}:</span>
                    </span>
                    <span className="font-bold text-slate-900">{formatKw(s.val)}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

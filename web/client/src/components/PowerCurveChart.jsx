import React, { useState } from 'react';
import { Activity, Eye, EyeOff } from 'lucide-react';
import { formatKw } from '../utils/formatters.js';

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
    { key: 'fcfs_beyan', name: 'FCFS (Beyan)', color: '#EF4444' },
    { key: 'edf_beyan', name: 'EDF (Beyan)', color: '#3B82F6' },
    { key: 'edf_tahmin_guvenli', name: 'EDF Güvenli', color: '#8B5CF6' },
    { key: 'mpc_beyan', name: 'MPC (Beyan)', color: '#F59E0B' },
    { key: 'mpc_tahmin_guvenli', name: 'MPC Güvenli (Hipotez)', color: '#10B981' },
    { key: 'mpc_hibrit_asimetrik', name: 'MPC Hibrit', color: '#06B6D4' },
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
  const svgHeight = 280;
  const padding = { top: 20, right: 30, bottom: 35, left: 55 };
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
    series: seriesMeta.map(s => ({
      ...s,
      val: (simulation.yontem_profilleri[s.key] || [])[hoveredIdx] || 0,
    })),
  } : null;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 sm:p-5 mb-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <h3 className="font-bold text-xs sm:text-sm text-white">24 Saatlik Güç-Zaman Yük Eğrisi (96 Adım / 15 dk)</h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Ayrılabilir şarj gücü tavanı (<span className="text-rose-400 font-semibold">{formatKw(capLimit)}</span>) ve kontrolsüz pik karşısında algoritmaların yük profilleri.
          </p>
        </div>

        {/* Legend / Toggles */}
        <div className="flex items-center flex-wrap gap-1.5 text-[11px]">
          {seriesMeta.map((s) => (
            <button
              key={s.key}
              onClick={() => toggleSeries(s.key)}
              className={`flex items-center space-x-1.5 px-2 py-1 rounded-md border transition ${
                visibleSeries[s.key]
                  ? 'bg-slate-800 border-slate-700 text-slate-200'
                  : 'bg-slate-950/40 border-slate-800/80 text-slate-600 line-through'
              }`}
            >
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: s.color }} />
              <span>{s.name}</span>
            </button>
          ))}
          <button
            onClick={() => toggleSeries('kontrolsuz')}
            className={`flex items-center space-x-1 px-2 py-1 rounded-md border transition ${
              visibleSeries.kontrolsuz
                ? 'bg-slate-800 border-slate-700 text-slate-400'
                : 'bg-slate-950/40 border-slate-800 text-slate-600 line-through'
            }`}
          >
            <span className="w-2.5 h-0.5 bg-slate-400" />
            <span>Kontrolsüz</span>
          </button>
        </div>
      </div>

      {/* SVG Interactive Chart */}
      <div className="relative overflow-x-auto">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full h-auto min-w-[700px] select-none"
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
                  stroke="#1e293b"
                  strokeDasharray="4 4"
                />
                <text
                  x={padding.left - 10}
                  y={y + 4}
                  fill="#64748b"
                  fontSize="10"
                  textAnchor="end"
                  fontFamily="monospace"
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
                  stroke="#1e293b"
                  strokeWidth="0.8"
                />
                <text
                  x={x}
                  y={padding.top + graphHeight + 18}
                  fill="#64748b"
                  fontSize="10"
                  textAnchor="middle"
                  fontFamily="monospace"
                >
                  {label}
                </text>
              </g>
            );
          })}

          {/* Uncontrolled Profile (Dotted Gray) */}
          {visibleSeries.kontrolsuz && unctrl.length > 0 && (
            <path
              d={makePath(unctrl)}
              fill="none"
              stroke="#64748b"
              strokeWidth="1.5"
              strokeDasharray="3 3"
              opacity="0.8"
            />
          )}

          {/* Algorithm Power Curves */}
          {seriesMeta.map((s) => {
            if (!visibleSeries[s.key]) return null;
            const data = simulation.yontem_profilleri[s.key] || [];
            return (
              <path
                key={s.key}
                d={makePath(data)}
                fill="none"
                stroke={s.color}
                strokeWidth={s.key === 'mpc_tahmin_guvenli' || s.key === 'edf_tahmin_guvenli' ? '2.5' : '1.8'}
                strokeLinecap="round"
                strokeLinejoin="round"
                opacity={hoveredIdx !== null ? 0.95 : 0.85}
              />
            );
          })}

          {/* Allocatable Charging Power Ceiling Line (Dashed Red) */}
          {visibleSeries.kapasite && (
            <g>
              <line
                x1={padding.left}
                y1={getY(capLimit)}
                x2={padding.left + graphWidth}
                y2={getY(capLimit)}
                stroke="#F43F5E"
                strokeWidth="2"
                strokeDasharray="6 4"
              />
              <text
                x={padding.left + graphWidth - 5}
                y={getY(capLimit) - 6}
                fill="#F43F5E"
                fontSize="10"
                fontWeight="bold"
                textAnchor="end"
              >
                Şarj Gücü Tavanı ({formatKw(capLimit)})
              </text>
            </g>
          )}

          {/* Hover Vertical Guide */}
          {hoveredIdx !== null && (
            <line
              x1={getX(hoveredIdx)}
              y1={padding.top}
              x2={getX(hoveredIdx)}
              y2={padding.top + graphHeight}
              stroke="#e2e8f0"
              strokeWidth="1"
              strokeDasharray="2 2"
            />
          )}
        </svg>

        {/* Hover Tooltip Overlay */}
        {activeHover && (
          <div
            className="absolute top-3 bg-slate-950/95 border border-slate-700/80 rounded-xl p-3 shadow-2xl pointer-events-none text-xs backdrop-blur z-20"
            style={{
              left: `${Math.min(75, Math.max(10, (hoveredIdx / 95) * 100))}%`,
              transform: 'translateX(-50%)',
            }}
          >
            <div className="font-bold text-white mb-1.5 flex items-center justify-between border-b border-slate-800 pb-1 font-mono">
              <span>Saat: {activeHover.time}</span>
              <span className="text-rose-400 text-[10px]">Tavan: {formatKw(capLimit)}</span>
            </div>
            <div className="space-y-1 font-mono">
              {activeHover.series
                .filter((s) => visibleSeries[s.key])
                .map((s) => (
                  <div key={s.key} className="flex items-center justify-between space-x-3 text-[11px]">
                    <span className="flex items-center space-x-1.5 text-slate-300">
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: s.color }} />
                      <span>{s.name}:</span>
                    </span>
                    <span className="font-bold text-white">{formatKw(s.val, 2)}</span>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

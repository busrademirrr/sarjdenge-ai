import React from 'react';
import { Clock } from 'lucide-react';
import { formatTimeHour, formatPercent, formatKwh } from '../utils/formatters.js';

export default function GanttChart({ simulation, onSelectVehicle }) {
  if (!simulation || !simulation.araclar) return null;

  const totalVehicles = simulation.arac_sayisi || simulation.araclar.length;
  const vehicles = simulation.araclar.slice(0, 25); // show up to 25 vehicles for readability
  const maxStep = 96;

  const countLabel = totalVehicles <= 25
    ? `${totalVehicles} aracın tamamı gösteriliyor (${totalVehicles} toplam)`
    : `İlk 25 araç gösteriliyor (${totalVehicles} toplam)`;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 sm:p-5 mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-emerald-400" />
            <h3 className="font-bold text-xs sm:text-sm text-white">Araç Bazlı Otopark Kalış ve Şarj Zaman Çizelgesi</h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Renkli bloklar aracın bağlı olduğu süreyi gösterir. Detay ve "Neden?" analizi için satıra tıklayın.
          </p>
        </div>
        <span className="text-xs text-slate-400 font-mono self-start sm:self-auto bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
          {countLabel}
        </span>
      </div>

      {/* Gantt Rows */}
      <div className="space-y-2">
        {/* Time axis header */}
        <div className="grid grid-cols-12 text-[10px] text-slate-500 font-mono pb-1 border-b border-slate-800 pl-24">
          <span>00:00</span>
          <span>02:00</span>
          <span>04:00</span>
          <span>06:00</span>
          <span>08:00</span>
          <span>10:00</span>
          <span>12:00</span>
          <span>14:00</span>
          <span>16:00</span>
          <span>18:00</span>
          <span>20:00</span>
          <span>22:00</span>
        </div>

        {vehicles.map((v) => {
          const startPct = (v.giris_adim / maxStep) * 100;
          const endPct = (v.ayril_adim / maxStep) * 100;
          const widthPct = Math.max(1.5, endPct - startPct);

          const okMpc = v.doyum_orani.mpc_tahmin_guvenli >= 0.95;
          const okEdf = v.doyum_orani.edf_beyan >= 0.95;

          const girisFormatted = formatTimeHour(v.giris_saat);
          const ayrilFormatted = formatTimeHour(v.ayril_saat);

          return (
            <div
              key={v.arac_id}
              onClick={() => onSelectVehicle(v)}
              className="flex items-center space-x-2 group cursor-pointer hover:bg-slate-800/40 p-1 rounded-lg transition"
            >
              {/* Left Label */}
              <div className="w-24 text-left font-mono text-[11px] text-slate-300 truncate shrink-0">
                <span className="font-semibold text-white">{v.arac_id}</span>
                <span className="text-[10px] text-slate-500 block">{formatKwh(v.talep_gercek_kwh)}</span>
              </div>

              {/* Bar track */}
              <div className="relative flex-1 h-6 bg-slate-950 rounded-md overflow-hidden border border-slate-800/80">
                {/* Stay bar */}
                <div
                  className={`absolute top-1 bottom-1 rounded transition ${
                    okMpc
                      ? 'bg-emerald-500/25 border border-emerald-500/50'
                      : okEdf
                      ? 'bg-blue-500/25 border border-blue-500/50'
                      : 'bg-rose-500/25 border border-rose-500/50'
                  }`}
                  style={{
                    left: `${startPct}%`,
                    width: `${widthPct}%`,
                  }}
                >
                  <div className="px-1 text-[9px] font-mono truncate text-white leading-4">
                    {girisFormatted} – {ayrilFormatted}
                  </div>
                </div>

                {/* Declared departure tick */}
                {v.erken_ayrildi && (
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-amber-400 z-10"
                    style={{ left: `${Math.min(99, (v.ayril_adim + (v.sure_beyan_dk - v.sure_gercek_dk) / 15) / maxStep * 100)}%` }}
                    title={`Beyan Edilen Çıkış: ${formatTimeHour(v.beyan_ayril_saat)}`}
                  />
                )}
              </div>

              {/* Status pill */}
              <div className="w-16 text-right font-mono text-[10px] shrink-0">
                <span
                  className={`px-1.5 py-0.5 rounded font-bold ${
                    okMpc
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                      : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                  }`}
                >
                  {formatPercent(v.doyum_orani.mpc_tahmin_guvenli, 0, true)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

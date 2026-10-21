import React from 'react';
import { Clock } from 'lucide-react';
import { formatTimeHour, formatKwh } from '../utils/formatters.js';

const PX_PER_STEP = 10; // 15 dk = 10px, 1 saat = 40px, 24 saat (96 ad─▒m) = 960px
const RIGHT_PAD_PX = 48; // Sa─ş kenarda son saat etiketi i├ğin g├╝venli bo┼şluk

export default function GanttChart({ simulation, onSelectVehicle }) {
  if (!simulation || !simulation.araclar) return null;

  const totalVehicles = simulation.arac_sayisi || simulation.araclar.length;
  const vehicles = simulation.araclar.slice(0, 25);

  const rawMaxStep = vehicles.reduce((acc, v) => {
    const giris = Number(v.giris_adim) || 0;
    const ayril = Number(v.ayril_adim) || 0;
    const beyan = v.erken_ayrildi
      ? giris + Number(v.sure_beyan_dk || 0) / 15
      : ayril;
    return Math.max(acc, ayril, beyan);
  }, 96);

  const hasOvernight = rawMaxStep > 96;
  const timelineSteps = hasOvernight
    ? Math.ceil(rawMaxStep / 12) * 12
    : 96;

  const trackWidthPx = timelineSteps * PX_PER_STEP;

  const tickIntervalSteps = 12; // 3 saat (120px)
  const axisTicks = [];
  for (let s = 0; s <= timelineSteps; s += tickIntervalSteps) {
    const totalHours = Math.floor((s * 15) / 60);
    const modHours = totalHours % 24;
    const isNextDay = s > 96;
    const isMidnight = s === 96;

    let label = `${String(modHours).padStart(2, '0')}:00`;
    if (isMidnight) {
      label = hasOvernight ? '24:00 (+1)' : '24:00';
    } else if (isNextDay) {
      label = `${String(modHours).padStart(2, '0')}:00 (+1)`;
    }

    axisTicks.push({
      step: s,
      leftPx: s * PX_PER_STEP,
      label,
      isMidnight,
      isNextDay,
    });
  }

  const countLabel =
    totalVehicles <= 25
      ? `${totalVehicles} ara├ğ`
      : `─░lk 25 / ${totalVehicles} ara├ğ`;

  return (
    <section
      className="bg-white border border-slate-200/90 rounded-xl p-4 sm:p-5 mb-4 shadow-2xs"
      aria-label="Ara├ğ Kal─▒┼ş ve ┼Şarj Zaman ├çizelgesi"
    >
      {/* Ba┼şl─▒k ve Kompakt Lejant */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-2.5 pb-3 mb-3 border-b border-slate-100">
        <div className="flex items-center space-x-2">
          <Clock className="w-4 h-4 text-emerald-700 shrink-0" />
          <h3 className="font-semibold text-sm sm:text-base text-slate-900">
            Ara├ğ Kal─▒┼ş ve ┼Şarj Zaman ├çizelgesi
          </h3>
          <span className="text-[11px] font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded-md tabular-nums">
            {countLabel}
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-x-3.5 gap-y-1 text-[11px] text-slate-600">
          <span className="inline-flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-xs bg-emerald-100 border border-emerald-500" />
            <span>MPC ÔëÑ%95</span>
          </span>
          <span className="inline-flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-xs bg-blue-100 border border-blue-500" />
            <span>EDF ÔëÑ%95</span>
          </span>
          <span className="inline-flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-xs bg-rose-100 border border-rose-500" />
            <span>K─▒s─▒tl─▒ (&lt;%95)</span>
          </span>
          <span className="inline-flex items-center space-x-1.5">
            <span className="inline-block w-[3px] h-3 bg-amber-500 rounded-full" />
            <span>Erken Ayr─▒l─▒┼ş</span>
          </span>
        </div>
      </div>

      {/* Yatay + Dikey Kayd─▒r─▒labilir Kompakt Panel */}
      <div className="overflow-auto max-h-[360px] border border-slate-200/80 rounded-lg bg-white">
        <div
          className="min-w-full"
          style={{ width: `${168 + trackWidthPx + RIGHT_PAD_PX}px` }}
        >
          {/* ├£st Saat Ekseni Sat─▒r─▒ (Sticky Top) */}
          <div className="sticky top-0 z-30 flex items-center border-b border-slate-200/90 bg-slate-50 h-8 text-[11px] text-slate-500 tabular-nums select-none">
            <div className="sticky left-0 z-40 w-[168px] shrink-0 px-3 h-full flex items-center bg-slate-50 border-r border-slate-200/90 font-semibold text-slate-700">
              Ara├ğ / Talep
            </div>

            <div
              className="relative h-full shrink-0"
              style={{ width: `${trackWidthPx + RIGHT_PAD_PX}px` }}
            >
              {axisTicks.map((t) => (
                <span
                  key={t.step}
                  className={`absolute top-1/2 -translate-y-1/2 whitespace-nowrap ${
                    t.step === 0 ? 'translate-x-1.5' : '-translate-x-1/2'
                  } ${
                    t.isMidnight
                      ? 'font-semibold text-emerald-800 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200/80'
                      : t.isNextDay
                      ? 'text-slate-600 font-medium'
                      : 'text-slate-500'
                  }`}
                  style={{ left: `${t.leftPx}px` }}
                >
                  {t.label}
                </span>
              ))}
            </div>
          </div>

          {/* Kompakt Ara├ğ Sat─▒rlar─▒ */}
          <div className="divide-y divide-slate-100">
            {vehicles.map((v) => {
              const girisAdim = Math.max(0, Number(v.giris_adim) || 0);
              const ayrilAdim = Math.max(girisAdim + 1, Number(v.ayril_adim) || 0);

              const startPx = girisAdim * PX_PER_STEP;
              const endPx = Math.max(startPx + 10, ayrilAdim * PX_PER_STEP);
              const widthPx = endPx - startPx;

              const beyanAdim = girisAdim + Number(v.sure_beyan_dk || 0) / 15;
              const beyanPx = v.erken_ayrildi
                ? Math.min(trackWidthPx, Math.max(endPx + 6, beyanAdim * PX_PER_STEP))
                : null;

              const okMpc = v.doyum_orani?.mpc_tahmin_guvenli >= 0.95;
              const okEdf = v.doyum_orani?.edf_beyan >= 0.95;

              const girisFormatted = formatTimeHour(v.giris_saat);
              const ayrilFormatted = formatTimeHour(v.ayril_saat);
              const timeRangeLabel = `${girisFormatted} ÔÇô ${ayrilFormatted}`;
              const isOvernightLabel = timeRangeLabel.includes('+1');
              const beyanFormatted = v.beyan_ayril_saat ? formatTimeHour(v.beyan_ayril_saat) : '';

              const minInsidePx = isOvernightLabel ? 152 : 104;
              const fitsInsideBar = widthPx >= minInsidePx;

              const placeLeftOfBar =
                !fitsInsideBar &&
                startPx >= 150 &&
                (beyanPx !== null || endPx > trackWidthPx - 140);

              const rightLabelLeftPx =
                beyanPx !== null && beyanPx - endPx < 130
                  ? beyanPx + 8
                  : endPx + 6;

              return (
                <div
                  key={v.arac_id}
                  onClick={() => onSelectVehicle(v)}
                  title={`${v.arac_id} ÔÇó Kal─▒┼ş: ${timeRangeLabel} ÔÇó Talep: ${formatKwh(v.talep_gercek_kwh)}${
                    v.erken_ayrildi && beyanFormatted ? ` ÔÇó Beyan ├ç─▒k─▒┼ş─▒: ${beyanFormatted}` : ''
                  }`}
                  className="flex items-center h-9 group cursor-pointer hover:bg-slate-50/80 transition"
                >
                  {/* Sabit (Sticky) Sol S├╝tun: Ara├ğ Ad─▒ ve kWh */}
                  <div className="sticky left-0 z-20 w-[168px] shrink-0 px-3 h-full flex items-center justify-between gap-2 bg-white group-hover:bg-slate-50 border-r border-slate-200/80 text-left tabular-nums transition">
                    <span className="text-[11px] font-medium text-slate-800 truncate">
                      {v.arac_id}
                    </span>
                    <span className="text-[11px] text-slate-500 shrink-0">
                      {formatKwh(v.talep_gercek_kwh)}
                    </span>
                  </div>

                  {/* Senkronize Zaman Blo─şu Alan─▒ */}
                  <div
                    className="relative h-full shrink-0 flex items-center"
                    style={{ width: `${trackWidthPx + RIGHT_PAD_PX}px` }}
                  >
                    {/* 3 Saatlik Dikey K─▒lavuz ├çizgileri ve 24:00 S─▒n─▒r─▒ */}
                    {axisTicks.map((t) => (
                      <div
                        key={t.step}
                        className={`absolute top-0 bottom-0 pointer-events-none ${
                          t.isMidnight
                            ? 'border-l border-dashed border-emerald-500/40 bg-slate-50/30'
                            : 'border-l border-slate-100'
                        }`}
                        style={{ left: `${t.leftPx}px` }}
                      />
                    ))}

                    {/* Erken Ayr─▒l─▒┼ş Kesikli Ba─şlant─▒ */}
                    {beyanPx !== null && beyanPx > endPx && (
                      <div
                        className="absolute top-1/2 -translate-y-1/2 border-t border-dashed border-amber-400/90 pointer-events-none"
                        style={{
                          left: `${endPx}px`,
                          width: `${beyanPx - endPx}px`,
                        }}
                      />
                    )}

                    {/* ┼Şarj / Kal─▒┼ş Blo─şu */}
                    <div
                      className={`absolute top-1.5 bottom-1.5 rounded flex items-center overflow-hidden ${
                        okMpc
                          ? 'bg-emerald-100/95 border border-emerald-400 text-emerald-950'
                          : okEdf
                          ? 'bg-blue-100/95 border border-blue-400 text-blue-950'
                          : 'bg-rose-100/95 border border-rose-400 text-rose-950'
                      }`}
                      style={{
                        left: `${startPx}px`,
                        width: `${widthPx}px`,
                      }}
                    >
                      {fitsInsideBar && (
                        <span className="px-2 text-[11px] font-medium whitespace-nowrap tabular-nums leading-none">
                          {timeRangeLabel}
                        </span>
                      )}
                    </div>

                    {/* K─▒sa Bloklar ─░├ğin Blok D─▒┼ş─▒ Etiket (Sol) */}
                    {!fitsInsideBar && placeLeftOfBar && (
                      <span
                        className="absolute top-1/2 -translate-y-1/2 -translate-x-full text-[11px] font-medium text-slate-700 bg-white/95 px-1.5 py-0.5 rounded border border-slate-200/80 whitespace-nowrap tabular-nums pointer-events-none z-10"
                        style={{ left: `${startPx - 6}px` }}
                      >
                        {timeRangeLabel}
                      </span>
                    )}

                    {/* K─▒sa Bloklar ─░├ğin Blok D─▒┼ş─▒ Etiket (Sa─ş) */}
                    {!fitsInsideBar && !placeLeftOfBar && (
                      <span
                        className="absolute top-1/2 -translate-y-1/2 text-[11px] font-medium text-slate-700 bg-white/95 px-1.5 py-0.5 rounded border border-slate-200/80 whitespace-nowrap tabular-nums pointer-events-none z-10"
                        style={{ left: `${rightLabelLeftPx}px` }}
                      >
                        {timeRangeLabel}
                      </span>
                    )}

                    {/* ─░nce Turuncu Erken Ayr─▒l─▒┼ş ─░┼şareti */}
                    {beyanPx !== null && (
                      <div
                        className="absolute top-1.5 bottom-1.5 w-[3px] bg-amber-500 rounded-full z-10"
                        style={{ left: `${beyanPx}px` }}
                        title={`Beyan Edilen ├ç─▒k─▒┼ş: ${beyanFormatted}`}
                      />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

import React from 'react';
import { X, HelpCircle, Clock, Zap } from 'lucide-react';
import { formatTimeHour, formatPercent, formatKwh } from '../utils/formatters.js';
import { ALGORITHM_META } from '../utils/algorithmMeta.js';

export default function VehicleInspectorModal({ vehicle, onClose }) {
  if (!vehicle) return null;

  const sat = vehicle.doyum_orani || {};
  const del = vehicle.teslim_kwh || {};

  const getDegreeStyle = (deg) => {
    switch (deg) {
      case 'kritik':
        return 'bg-rose-50 text-rose-900 border-rose-200';
      case 'uyari':
        return 'bg-amber-50 text-amber-900 border-amber-200';
      case 'olumlu':
        return 'bg-emerald-50 text-emerald-900 border-emerald-200';
      default:
        return 'bg-blue-50 text-blue-900 border-blue-200';
    }
  };

  const girisFmt = formatTimeHour(vehicle.giris_saat);
  const ayrilFmt = formatTimeHour(vehicle.ayril_saat);

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 rounded-2xl max-w-2xl w-full p-5 sm:p-6 shadow-2xl overflow-y-auto max-h-[90vh]">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-slate-200">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 font-semibold">
                S─▒ra #{vehicle.sira}
              </span>
              <h3 className="text-base sm:text-lg font-bold text-slate-900 flex items-center space-x-2">
                <span>Ara├ğ: {vehicle.arac_id}</span>
                {vehicle.erken_ayrildi && (
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200 font-semibold flex items-center space-x-1">
                    <Clock className="w-3 h-3 text-amber-600" />
                    <span>Erken Ayr─▒ld─▒</span>
                  </span>
                )}
              </h3>
            </div>
            <p className="text-xs text-slate-500 mt-1 font-mono">
              Kullan─▒c─▒ ID: {vehicle.kullanici_id} ÔÇó Giri┼ş: {girisFmt} ÔÇó ├ç─▒k─▒┼ş: {ayrilFmt}
            </p>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Telemetry Comparison Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-4">
          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <span className="text-xs text-slate-600 uppercase block font-semibold">Ger├ğek Talep</span>
            <span className="text-base font-bold text-slate-900 font-mono">{formatKwh(vehicle.talep_gercek_kwh)}</span>
            <span className="text-xs text-slate-600 block mt-0.5">
              Kal─▒┼ş: {vehicle.sure_gercek_dk} dk ({(Number(vehicle.sure_gercek_dk) / 60).toFixed(1).replace('.', ',')} sa)
            </span>
          </div>

          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <span className="text-xs text-slate-600 uppercase block font-semibold">Kullan─▒c─▒ Beyan─▒</span>
            <span className="text-base font-bold text-amber-800 font-mono">{formatKwh(vehicle.talep_beyan_kwh)}</span>
            <span className="text-xs text-slate-600 block mt-0.5">
              Beyan: {vehicle.sure_beyan_dk} dk ({(Number(vehicle.sure_beyan_dk) / 60).toFixed(1).replace('.', ',')} sa)
            </span>
          </div>

          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <span className="text-xs text-slate-600 uppercase block font-semibold">Tahmin (q20 S├╝re)</span>
            <span className="text-base font-bold text-emerald-800 font-mono">
              {vehicle.sure_tahmin_q20_dk} dk ({(Number(vehicle.sure_tahmin_q20_dk) / 60).toFixed(1).replace('.', ',')} sa)
            </span>
            <span className="text-xs text-slate-600 block mt-0.5">
              q50: {vehicle.sure_tahmin_q50_dk} dk ({(Number(vehicle.sure_tahmin_q50_dk) / 60).toFixed(1).replace('.', ',')} sa)
            </span>
          </div>

          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <span className="text-xs text-slate-600 uppercase block font-semibold">Tahmin (q80 Enerji)</span>
            <span className="text-base font-bold text-slate-900 font-mono">{formatKwh(vehicle.tahmin_kwh_q80)}</span>
            <span className="text-xs text-slate-600 block mt-0.5">q50: {formatKwh(vehicle.tahmin_kwh_q50)}</span>
          </div>
        </div>

        {/* Algorithm Delivery Table */}
        <div className="mb-4">
          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
            Algoritma Bazl─▒ Teslim Edilen Enerji ve Kar┼ş─▒lama
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 tabular-nums">
            {[
              ALGORITHM_META.fcfs_beyan,
              ALGORITHM_META.edf_beyan,
              ALGORITHM_META.edf_tahmin_guvenli,
              ALGORITHM_META.mpc_beyan,
              ALGORITHM_META.mpc_tahmin_guvenli,
              ALGORITHM_META.mpc_hibrit_asimetrik,
            ].map((m) => {
              const delivered = del[m.key] ?? 0;
              const ratio = sat[m.key] ?? 0;
              const isOk = ratio >= 0.95;

              return (
                <div
                  key={m.key}
                  className={`p-3 rounded-xl border text-xs ${
                    isOk ? 'bg-emerald-50/50 border-emerald-300' : 'bg-slate-50 border-slate-200'
                  }`}
                >
                  <span className="text-xs text-slate-700 font-semibold flex items-center space-x-1">
                    <span aria-hidden="true" style={{ color: m.color }}>{m.symbol}</span>
                    <span>{m.shortName}</span>
                  </span>
                  <div className="flex items-baseline justify-between mt-1.5">
                    <span className="font-bold text-slate-900">{formatKwh(delivered)}</span>
                    <span className={`text-xs font-bold ${isOk ? 'text-emerald-800' : 'text-amber-800'}`}>
                      {isOk ? 'Ô£ô ' : '! '}
                      {formatPercent(ratio, 0, true)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Physical Explainability ("Neden?") */}
        <div className="space-y-3 pt-3 border-t border-slate-200">
          <div className="flex items-center space-x-2">
            <HelpCircle className="w-4 h-4 text-emerald-700" />
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Olas─▒ Mekanizma ve Karar A├ğ─▒klamas─▒ (Explainability)
            </h4>
          </div>

          <div className="space-y-2">
            {vehicle.neden_analizi?.nedenler?.map((n, i) => {
              const cleanTitle = n.baslik?.replace(
                'Hayalet Kapasite Rezervasyonu',
                'Hayalet Kapasite Rezervasyonu (├çal─▒┼şma Hipotezi)'
              );

              return (
                <div
                  key={i}
                  className={`p-3 rounded-xl border ${getDegreeStyle(n.derece)}`}
                >
                  <div className="font-bold text-xs mb-1 flex items-center space-x-1.5">
                    <Zap className="w-3.5 h-3.5" />
                    <span>{cleanTitle}</span>
                  </div>
                  <p className="text-xs leading-relaxed opacity-90">
                    {n.metin}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-5 pt-3 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-800 transition"
          >
            Kapat
          </button>
        </div>
      </div>
    </div>
  );
}

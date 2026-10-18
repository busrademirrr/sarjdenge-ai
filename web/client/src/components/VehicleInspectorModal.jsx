import React from 'react';
import { X, HelpCircle, AlertCircle, CheckCircle2, Clock, BatteryCharging, Zap } from 'lucide-react';
import { formatTimeHour, formatPercent, formatKwh } from '../utils/formatters.js';

export default function VehicleInspectorModal({ vehicle, onClose }) {
  if (!vehicle) return null;

  const sat = vehicle.doyum_orani || {};
  const del = vehicle.teslim_kwh || {};

  const getDegreeStyle = (deg) => {
    switch (deg) {
      case 'kritik':
        return 'bg-rose-500/10 text-rose-300 border-rose-500/30';
      case 'uyari':
        return 'bg-amber-500/10 text-amber-300 border-amber-500/30';
      case 'olumlu':
        return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30';
      default:
        return 'bg-blue-500/10 text-blue-300 border-blue-500/30';
    }
  };

  const girisFmt = formatTimeHour(vehicle.giris_saat);
  const ayrilFmt = formatTimeHour(vehicle.ayril_saat);

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-2xl w-full p-5 sm:p-6 shadow-2xl overflow-y-auto max-h-[90vh]">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                Sıra #{vehicle.sira}
              </span>
              <h3 className="text-base sm:text-lg font-bold text-white flex items-center space-x-2">
                <span>Araç: {vehicle.arac_id}</span>
                {vehicle.erken_ayrildi && (
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 font-medium flex items-center space-x-1">
                    <Clock className="w-3 h-3 text-amber-400" />
                    <span>Erken Ayrıldı</span>
                  </span>
                )}
              </h3>
            </div>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              Kullanıcı ID: {vehicle.kullanici_id} • Giriş: {girisFmt} • Çıkış: {ayrilFmt}
            </p>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Telemetry Comparison Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-4">
          <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase block font-medium">Gerçek Talep</span>
            <span className="text-base font-bold text-white font-mono">{formatKwh(vehicle.talep_gercek_kwh)}</span>
            <span className="text-[10px] text-slate-500 block">Kalış: {vehicle.sure_gercek_dk} dk</span>
          </div>

          <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase block font-medium">Kullanıcı Beyanı</span>
            <span className="text-base font-bold text-amber-300 font-mono">{formatKwh(vehicle.talep_beyan_kwh)}</span>
            <span className="text-[10px] text-slate-500 block">Beyan: {vehicle.sure_beyan_dk} dk</span>
          </div>

          <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase block font-medium">Tahmin (q20 Süre)</span>
            <span className="text-base font-bold text-emerald-400 font-mono">{vehicle.sure_tahmin_q20_dk} dk</span>
            <span className="text-[10px] text-slate-500 block">q50: {vehicle.sure_tahmin_q50_dk} dk</span>
          </div>

          <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase block font-medium">Tahmin (q80 Enerji)</span>
            <span className="text-base font-bold text-purple-400 font-mono">{formatKwh(vehicle.tahmin_kwh_q80)}</span>
            <span className="text-[10px] text-slate-500 block">q50: {formatKwh(vehicle.tahmin_kwh_q50)}</span>
          </div>
        </div>

        {/* Algorithm Delivery Table */}
        <div className="mb-4">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
            Algoritma Bazlı Teslim Edilen Enerji ve Karşılama
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {[
              { key: 'fcfs_beyan', name: 'FCFS (Beyan)' },
              { key: 'edf_beyan', name: 'EDF (Beyan)' },
              { key: 'edf_tahmin_guvenli', name: 'EDF Güvenli' },
              { key: 'mpc_beyan', name: 'MPC (Beyan)' },
              { key: 'mpc_tahmin_guvenli', name: 'MPC Güvenli' },
              { key: 'mpc_hibrit_asimetrik', name: 'MPC Hibrit' },
            ].map((m) => {
              const delivered = del[m.key] ?? 0;
              const ratio = sat[m.key] ?? 0;
              const isOk = ratio >= 0.95;

              return (
                <div
                  key={m.key}
                  className={`p-2.5 rounded-xl border text-xs ${
                    isOk ? 'bg-slate-950 border-emerald-500/30' : 'bg-slate-950 border-slate-800'
                  }`}
                >
                  <span className="text-[11px] text-slate-400 block font-medium truncate">{m.name}</span>
                  <div className="flex items-baseline justify-between mt-1">
                    <span className="font-bold text-white font-mono">{formatKwh(delivered)}</span>
                    <span className={`font-mono text-[11px] font-bold ${isOk ? 'text-emerald-400' : 'text-amber-400'}`}>
                      {formatPercent(ratio, 0, true)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Physical Explainability ("Neden?") */}
        <div className="space-y-3 pt-3 border-t border-slate-800">
          <div className="flex items-center space-x-2">
            <HelpCircle className="w-4 h-4 text-emerald-400" />
            <h4 className="text-xs font-bold text-white uppercase tracking-wider">
              Fiziksel Karar ve Neden Açıklaması (Explainability)
            </h4>
          </div>

          <div className="space-y-2">
            {vehicle.neden_analizi?.nedenler?.map((n, i) => {
              // Ensure working hypothesis clarification
              const cleanTitle = n.baslik?.replace(
                'Hayalet Kapasite Rezervasyonu',
                'Hayalet Kapasite Rezervasyonu (Çalışma Hipotezi)'
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
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {n.metin}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-5 pt-3 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-white transition"
          >
            Kapat
          </button>
        </div>
      </div>
    </div>
  );
}

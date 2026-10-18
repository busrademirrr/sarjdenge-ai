import React, { useState } from 'react';
import { X, Download, FileSpreadsheet, FileCode, CheckCircle } from 'lucide-react';

export default function ExportModal({ simulation, onClose }) {
  const [downloading, setDownloading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const handleDownload = async (format) => {
    if (!simulation) return;
    setDownloading(true);
    setSuccessMsg('');

    try {
      const endpoint = format === 'csv' ? '/api/export/csv' : '/api/export/json';
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ simulation }),
      });

      if (!res.ok) throw new Error('Dışa aktarma başarısız oldu.');

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `sarjdenge_${simulation.senaryo_id}_${simulation.tarih}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      setSuccessMsg(`${format.toUpperCase()} dosyası başarıyla indirildi.`);
    } catch (err) {
      alert(err.message);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-md w-full p-6 shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <Download className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-white">Simülasyon Sonuçlarını İndir</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="py-4 space-y-3">
          <p className="text-xs text-slate-300">
            Aktif simülasyonun 96 adımlı güç eğrilerini, araç bazlı telemetrisini ve karar açıklamalarını dışa aktarabilirsiniz.
          </p>

          <div className="grid grid-cols-2 gap-3 pt-2">
            <button
              onClick={() => handleDownload('csv')}
              disabled={downloading || !simulation}
              className="flex flex-col items-center justify-center p-4 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-emerald-500/50 transition group"
            >
              <FileSpreadsheet className="w-8 h-8 text-emerald-400 mb-2 group-hover:scale-110 transition-transform" />
              <span className="font-bold text-xs text-white">CSV İndir</span>
              <span className="text-[10px] text-slate-500 mt-0.5">Excel / Pandas Uyumlu</span>
            </button>

            <button
              onClick={() => handleDownload('json')}
              disabled={downloading || !simulation}
              className="flex flex-col items-center justify-center p-4 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-blue-500/50 transition group"
            >
              <FileCode className="w-8 h-8 text-blue-400 mb-2 group-hover:scale-110 transition-transform" />
              <span className="font-bold text-xs text-white">JSON İndir</span>
              <span className="text-[10px] text-slate-500 mt-0.5">Ham API Çıktısı</span>
            </button>
          </div>

          {successMsg && (
            <div className="flex items-center space-x-1.5 p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs mt-3">
              <CheckCircle className="w-4 h-4 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}
        </div>

        <div className="pt-3 border-t border-slate-800 flex justify-end">
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

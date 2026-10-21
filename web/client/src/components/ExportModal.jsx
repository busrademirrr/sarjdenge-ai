import React, { useState } from 'react';
import { X, Download, FileSpreadsheet, FileCode, CheckCircle, AlertCircle } from 'lucide-react';

export default function ExportModal({ simulation, onClose }) {
  const [downloading, setDownloading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const handleDownload = async (format) => {
    if (!simulation) return;
    setDownloading(true);
    setSuccessMsg('');
    setErrorMsg('');

    try {
      const endpoint = format === 'csv' ? '/api/export/csv' : '/api/export/json';
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ simulation }),
      });

      if (!res.ok) throw new Error('D─▒┼şa aktarma ba┼şar─▒s─▒z oldu.');

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `sarjdenge_${simulation.senaryo_id}_${simulation.tarih}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      setSuccessMsg(`${format.toUpperCase()} dosyas─▒ ba┼şar─▒yla indirildi.`);
    } catch (err) {
      setErrorMsg(err.message || 'Dosya indirilirken bir hata olu┼ştu.');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 rounded-2xl max-w-md w-full p-6 shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-200">
          <div className="flex items-center space-x-2">
            <Download className="w-5 h-5 text-emerald-700" />
            <h3 className="text-base font-bold text-slate-900">Sim├╝lasyon Sonu├ğlar─▒n─▒ ─░ndir</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="py-4 space-y-3">
          <p className="text-xs text-slate-600">
            Aktif sim├╝lasyonun 96 ad─▒ml─▒ g├╝├ğ e─şrilerini, ara├ğ bazl─▒ telemetrisini ve karar a├ğ─▒klamalar─▒n─▒ d─▒┼şa aktarabilirsiniz.
          </p>

          <div className="grid grid-cols-2 gap-3 pt-2">
            <button
              onClick={() => handleDownload('csv')}
              disabled={downloading || !simulation}
              className="flex flex-col items-center justify-center p-4 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 hover:border-emerald-600 transition group"
            >
              <FileSpreadsheet className="w-8 h-8 text-emerald-700 mb-2 group-hover:scale-105 transition-transform" />
              <span className="font-bold text-xs text-slate-900">CSV ─░ndir</span>
              <span className="text-xs text-slate-500 mt-0.5">Excel / Pandas Uyumlu</span>
            </button>

            <button
              onClick={() => handleDownload('json')}
              disabled={downloading || !simulation}
              className="flex flex-col items-center justify-center p-4 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 hover:border-blue-600 transition group"
            >
              <FileCode className="w-8 h-8 text-blue-700 mb-2 group-hover:scale-105 transition-transform" />
              <span className="font-bold text-xs text-slate-900">JSON ─░ndir</span>
              <span className="text-xs text-slate-500 mt-0.5">Ham API ├ç─▒kt─▒s─▒</span>
            </button>
          </div>

          {successMsg && (
            <div className="flex items-center space-x-1.5 p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs mt-3">
              <CheckCircle className="w-4 h-4 shrink-0 text-emerald-700" />
              <span>{successMsg}</span>
            </div>
          )}

          {errorMsg && (
            <div className="flex items-center space-x-1.5 p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs mt-3">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-700" />
              <span>{errorMsg}</span>
            </div>
          )}
        </div>

        <div className="pt-3 border-t border-slate-200 flex justify-end">
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

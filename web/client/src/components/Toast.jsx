import React from 'react';
import { AlertCircle, RefreshCw, X } from 'lucide-react';

export default function Toast({ toast, onClose, onRetry, retryLoading = false }) {
  if (!toast) return null;

  const {
    title = 'Simülasyon Hatası',
    message = 'Bir hata oluştu.',
    canRetry = true,
  } = toast;

  return (
    <div
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
      className="fixed top-5 right-5 z-50 max-w-md w-full sm:w-96 bg-slate-900/95 backdrop-blur-md border border-rose-500/50 shadow-2xl shadow-rose-950/40 rounded-2xl p-4 text-slate-100 transition-all duration-200"
    >
      <div className="flex items-start space-x-3">
        {/* Error Icon */}
        <div className="p-2 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-400 shrink-0 mt-0.5">
          <AlertCircle className="w-5 h-5" aria-hidden="true" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 pr-1">
          <div className="flex items-center justify-between gap-2">
            <h4 className="font-bold text-xs sm:text-sm text-white truncate">
              {title}
            </h4>
            <button
              onClick={onClose}
              type="button"
              aria-label="Bildirimi kapat"
              className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition focus:outline-none focus:ring-2 focus:ring-rose-500/80 focus:ring-offset-1 focus:ring-offset-slate-900"
            >
              <X className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>

          <p className="text-xs text-slate-300 mt-1 leading-relaxed break-words">
            {message}
          </p>

          {/* Action Row: Yeniden Dene & Kapat */}
          {canRetry && onRetry && (
            <div className="mt-3 flex items-center space-x-2">
              <button
                type="button"
                onClick={onRetry}
                disabled={retryLoading}
                aria-label="Simülasyonu aynı parametrelerle yeniden dene"
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition focus:outline-none focus:ring-2 focus:ring-rose-500/80 focus:ring-offset-1 focus:ring-offset-slate-900 ${
                  retryLoading
                    ? 'bg-rose-950/60 text-rose-300/60 border border-rose-800/40 cursor-not-allowed'
                    : 'bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 border border-rose-500/40 active:scale-95'
                }`}
              >
                <RefreshCw
                  className={`w-3.5 h-3.5 ${retryLoading ? 'animate-spin' : ''}`}
                  aria-hidden="true"
                />
                <span>{retryLoading ? 'Yeniden Deneniyor…' : 'Yeniden Dene'}</span>
              </button>

              <button
                type="button"
                onClick={onClose}
                className="px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-1 focus:ring-offset-slate-900"
              >
                Kapat
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

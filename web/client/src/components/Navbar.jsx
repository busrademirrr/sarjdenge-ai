import React from 'react';
import { Zap, ShieldCheck, Download, Activity, BarChart3, BookOpen } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, session, onOpenAuth, onOpenExport }) {
  const isGuest = session?.isGuest ?? true;
  const userName = session?.user?.name || (isGuest ? 'Misafir Jüri' : 'Kullanıcı');

  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo & Title */}
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-md shadow-emerald-500/20 text-slate-950 font-black shrink-0">
            <Zap className="w-5 h-5 fill-slate-950 stroke-slate-950" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-base sm:text-lg tracking-tight text-white">ŞarjDenge AI</span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                Climathon 2026
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              Otopark EV Akıllı Şarj & Dinamik Kapasite Karar Destek Sistemi
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex items-center space-x-1 sm:space-x-1.5 bg-slate-950/80 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('simulation')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'simulation'
                ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Canlı Simülasyon</span>
          </button>
          <button
            onClick={() => setActiveTab('benchmark')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'benchmark'
                ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Doğrulama & Hipotez</span>
          </button>
          <button
            onClick={() => setActiveTab('methodology')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'methodology'
                ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Metodoloji & Sözlük</span>
          </button>
        </nav>

        {/* Actions & Auth Badge */}
        <div className="flex items-center space-x-2">
          <button
            onClick={onOpenExport}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700/80 transition"
            title="Simülasyon ve deney sonuçlarını dışa aktar (CSV/JSON)"
          >
            <Download className="w-3.5 h-3.5 text-slate-400" />
            <span className="hidden md:inline">Dışa Aktar</span>
          </button>

          <button
            onClick={onOpenAuth}
            className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border transition ${
              isGuest
                ? 'bg-amber-500/10 text-amber-300 border-amber-500/30 hover:bg-amber-500/20'
                : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/20'
            }`}
            title="Kullanıcı durumu (Misafir / Google Giriş)"
          >
            <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
            <span className="whitespace-nowrap font-medium text-[11px]">
              {isGuest ? 'Misafir demo' : userName}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}

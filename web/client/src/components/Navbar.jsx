import React, { useState } from 'react';
import {
  Zap,
  Download,
  Activity,
  BarChart3,
  BookOpen,
  Cpu,
  Menu,
  X,
} from 'lucide-react';

export default function Navbar({
  activeTab,
  setActiveTab,
  onOpenExport,
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { id: 'simulation', label: 'Canlı Simülasyon', icon: Activity },
    { id: 'advisor', label: 'Kapasite Danışmanı', icon: Cpu },
    { id: 'benchmark', label: 'Doğrulama & Hipotez', icon: BarChart3 },
    { id: 'methodology', label: 'Metodoloji & Sözlük', icon: BookOpen },
  ];

  const handleTabClick = (id) => {
    setActiveTab(id);
    setMobileMenuOpen(false);
  };

  return (
    <header className="border-b border-slate-200/80 bg-white sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="h-14 flex items-center justify-between gap-4">
          {/* Left: Fixed-Width Brand Area */}
          <div className="flex items-center space-x-2.5 min-w-[156px] shrink-0">
            <div className="w-8 h-8 rounded-lg bg-emerald-800 text-white flex items-center justify-center shrink-0">
              <Zap className="w-4 h-4 fill-white stroke-white" />
            </div>
            <span className="font-bold text-base tracking-tight text-slate-900 whitespace-nowrap">
              ŞarjDenge AI
            </span>
          </div>

          {/* Center: Balanced Single-Row Navigation */}
          <nav className="hidden lg:flex items-center gap-1 bg-slate-100/80 p-1 rounded-xl shrink-0">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => handleTabClick(item.id)}
                  className={`flex items-center justify-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs whitespace-nowrap transition-all ${
                    isActive
                      ? 'bg-white text-emerald-900 font-semibold shadow-2xs ring-1 ring-slate-200/80'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-white/60 font-medium'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-emerald-700' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right: Export Button & Mobile Menu Toggle */}
          <div className="flex items-center justify-end space-x-2 min-w-[156px] shrink-0">
            <button
              onClick={onOpenExport}
              className="inline-flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition whitespace-nowrap"
              title="Simülasyon sonuçlarını dışa aktar (CSV/JSON)"
            >
              <Download className="w-3.5 h-3.5 text-slate-500 shrink-0" />
              <span>Dışa Aktar</span>
            </button>

            {/* Mobile / Tablet Menu Toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-slate-200 transition"
              aria-label="Menüyü Aç/Kapat"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Responsive Dropdown Menu (< lg) */}
        {mobileMenuOpen && (
          <nav className="lg:hidden border-t border-slate-200 py-2.5 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => handleTabClick(item.id)}
                  className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium text-left transition ${
                    isActive
                      ? 'bg-emerald-50 text-emerald-900 font-semibold'
                      : 'text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-700' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}

            <div className="pt-2 border-t border-slate-100 space-y-1.5 px-1">
              <button
                onClick={() => {
                  onOpenExport();
                  setMobileMenuOpen(false);
                }}
                className="w-full flex items-center justify-center space-x-1.5 py-2 text-xs font-medium bg-slate-50 hover:bg-slate-100 text-slate-700 rounded-lg border border-slate-200"
              >
                <Download className="w-3.5 h-3.5 text-slate-500" />
                <span>Dışa Aktar</span>
              </button>
            </div>
          </nav>
        )}
      </div>
    </header>
  );
}

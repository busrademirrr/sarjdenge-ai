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
  LogIn,
  LogOut,
  ChevronDown,
} from 'lucide-react';
import { getInitials } from '../lib/supabaseClient.js';

export default function Navbar({
  activeTab,
  setActiveTab,
  onOpenExport,
  session,
  onOpenAuth,
  onSignOut,
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);

  const navItems = [
    { id: 'simulation', label: 'Canl─▒ Sim├╝lasyon', icon: Activity },
    { id: 'advisor', label: 'Kapasite Dan─▒┼şman─▒', icon: Cpu },
    { id: 'benchmark', label: 'Do─şrulama & Hipotez', icon: BarChart3 },
    { id: 'methodology', label: 'Metodoloji & S├Âzl├╝k', icon: BookOpen },
  ];

  const handleTabClick = (id) => {
    setActiveTab(id);
    setMobileMenuOpen(false);
  };

  const user = session?.user;
  const fullName = user?.user_metadata?.full_name || user?.user_metadata?.name || '';
  const email = user?.email || '';
  const initials = getInitials(fullName, email);
  const displayName = fullName || (email ? email.split('@')[0] : 'Kullan─▒c─▒');

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
              ┼ŞarjDenge AI
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

          {/* Right: Export & User Menu */}
          <div className="flex items-center justify-end space-x-2 min-w-[156px] shrink-0">
            <button
              onClick={onOpenExport}
              className="hidden sm:inline-flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition whitespace-nowrap"
              title="Sim├╝lasyon sonu├ğlar─▒n─▒ d─▒┼şa aktar (CSV/JSON)"
            >
              <Download className="w-3.5 h-3.5 text-slate-500 shrink-0" />
              <span>D─▒┼şa Aktar</span>
            </button>

            {user ? (
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setProfileMenuOpen((prev) => !prev)}
                  className="flex items-center space-x-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200/90 rounded-lg px-2 py-1 transition"
                >
                  <div className="w-6 h-6 rounded-md bg-emerald-700 text-white font-semibold text-xs flex items-center justify-center shrink-0">
                    {initials}
                  </div>
                  <span className="hidden sm:block text-xs font-medium text-slate-800 whitespace-nowrap max-w-[110px] truncate">
                    {displayName}
                  </span>
                  <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                </button>

                {profileMenuOpen && (
                  <div className="absolute right-0 mt-1.5 w-56 bg-white border border-slate-200 rounded-xl shadow-lg p-3 z-50 text-left">
                    <div className="pb-2.5 mb-2 border-b border-slate-100">
                      <span className="font-semibold text-xs text-slate-900 block truncate">{displayName}</span>
                      {email && (
                        <span className="text-xs text-slate-500 block truncate mt-0.5" title={email}>
                          {email}
                        </span>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setProfileMenuOpen(false);
                        onSignOut();
                      }}
                      aria-label="├ç─▒k─▒┼ş Yap"
                      className="w-full flex items-center space-x-2 px-2.5 py-1.5 rounded-lg text-xs font-medium text-rose-700 hover:bg-rose-50 transition"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      <span>Oturumu Kapat</span>
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={onOpenAuth}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-700 hover:bg-emerald-800 text-white transition whitespace-nowrap"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Giri┼ş Yap</span>
              </button>
            )}

            {/* Mobile / Tablet Menu Toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-slate-200 transition"
              aria-label="Men├╝y├╝ A├ğ/Kapat"
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
                <span>D─▒┼şa Aktar</span>
              </button>

              {user ? (
                <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-200">
                  <div className="flex items-center space-x-2 min-w-0">
                    <div className="w-7 h-7 rounded bg-emerald-700 text-white font-semibold text-xs flex items-center justify-center shrink-0">
                      {initials}
                    </div>
                    <div className="text-left text-xs min-w-0">
                      <span className="font-semibold text-slate-900 block truncate">{displayName}</span>
                      <span className="text-xs text-slate-500 block truncate">{email}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      onSignOut();
                      setMobileMenuOpen(false);
                    }}
                    className="px-2.5 py-1 text-xs font-medium text-rose-700 bg-rose-50 rounded border border-rose-200 shrink-0 ml-2"
                  >
                    ├ç─▒k─▒┼ş
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => {
                    onOpenAuth();
                    setMobileMenuOpen(false);
                  }}
                  className="w-full flex items-center justify-center space-x-1.5 py-2 text-xs font-semibold bg-emerald-700 text-white rounded-lg"
                >
                  <LogIn className="w-3.5 h-3.5" />
                  <span>Giri┼ş Yap / Kay─▒t Ol</span>
                </button>
              )}
            </div>
          </nav>
        )}
      </div>
    </header>
  );
}

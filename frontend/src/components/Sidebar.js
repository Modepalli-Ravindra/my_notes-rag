'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Sidebar({ activeTab = 'dashboard', setActiveTab }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const router = useRouter();

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊', route: '/' },
    { id: 'documents', label: 'Documents', icon: '📚', route: '/?tab=documents' },
    { id: 'resume', label: 'Resume', icon: '📄', route: '/resume' },
    { id: 'ask', label: 'Ask My Notes', icon: '💡', route: '/?tab=ask' },
    { id: 'viva', label: 'Viva', icon: '🎤', route: '/viva' },
    { id: 'interview', label: 'Interview', icon: '💼', route: '/interview' },
    { id: 'coding', label: 'Coding Interview', icon: '💻', route: '/coding' },
    { id: 'settings', label: 'Settings', icon: '⚙️', route: '/?tab=settings' },
  ];

  const handleNavigation = (item) => {
    if (setActiveTab) {
      setActiveTab(item.id);
    }
    setMobileOpen(false);
    if (item.route) {
      router.push(item.route);
    }
  };

  return (
    <>
      {/* Mobile Top Navigation Bar */}
      <div className="lg:hidden flex items-center justify-between p-4 bg-[#0d1322] border-b border-slate-800 text-white">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center font-bold text-sm shadow-md shadow-indigo-500/20">
            ⚡
          </div>
          <div>
            <span className="font-bold tracking-tight text-white">MyNotes RAG</span>
            <span className="text-[10px] block text-slate-400 font-medium -mt-1">Handwritten AI</span>
          </div>
        </div>
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="p-2 text-slate-300 hover:text-white rounded-lg bg-slate-800/60 border border-slate-700/50"
          aria-label="Toggle menu"
        >
          {mobileOpen ? '✕' : '☰'}
        </button>
      </div>

      {/* Backdrop for Mobile */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Main Sidebar */}
      <aside
        className={`fixed lg:static top-0 left-0 bottom-0 z-50 w-64 md:w-56 lg:w-64 bg-[#0b101d] border-r border-slate-800/80 flex flex-col justify-between transition-transform duration-200 ease-in-out ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="p-5">
          {/* Logo & Branding */}
          <div className="flex items-center space-x-3 pb-6 border-b border-slate-800/80">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center font-bold text-base shadow-lg shadow-indigo-500/25">
              ⚡
            </div>
            <div>
              <h1 className="font-extrabold text-base tracking-tight text-white">MyNotes RAG</h1>
              <p className="text-[11px] text-indigo-400/90 font-medium">Handwritten Knowledge AI</p>
            </div>
          </div>

          {/* Nav Items */}
          <nav className="mt-6 space-y-1.5">
            <p className="px-3 text-[11px] font-semibold tracking-wider text-slate-400 uppercase mb-2">
              Menu
            </p>
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleNavigation(item)}
                  className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-indigo-600/90 to-purple-600/90 text-white shadow-md shadow-indigo-500/20 font-semibold'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/50'
                  }`}
                >
                  <span className="text-base">{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* User Footer / Info */}
        <div className="p-4 m-3 rounded-xl bg-slate-900/80 border border-slate-800/90">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-600 flex items-center justify-center font-semibold text-xs text-white">
              RK
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-white truncate">Ravindra</p>
              <p className="text-[10px] text-emerald-400 flex items-center gap-1 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block animate-pulse"></span>
                FastAPI Connected
              </p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

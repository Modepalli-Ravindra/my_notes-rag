'use client';

export default function Header() {
  return (
    <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800/60">
      <div>
        <div className="flex items-center space-x-2">
          <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
            Good morning, <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">Ravindra</span> 👋
          </h2>
        </div>
        <p className="text-sm text-slate-400 mt-1 font-medium">
          Ask questions from your handwritten AI, Python & SQL notes.
        </p>
      </div>

      {/* Search / Quick Question Area */}
      <div className="w-full md:w-80 lg:w-96 relative">
        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 text-sm">
          🔍
        </div>
        <input
          type="text"
          placeholder="Search your notes or ask a question..."
          className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-slate-900/90 border border-slate-800 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all shadow-inner"
          readOnly
        />
        <div className="absolute inset-y-0 right-0 pr-2.5 flex items-center">
          <span className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded border border-slate-700/60 font-mono">
            ⌘K
          </span>
        </div>
      </div>
    </header>
  );
}

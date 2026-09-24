'use client';

export default function StatCard({ label, value, icon, badge = "Demo" }) {
  return (
    <div className="glass-card glass-card-hover rounded-2xl p-5 flex flex-col justify-between relative overflow-hidden group">
      {/* Top row: Icon and Badge */}
      <div className="flex items-center justify-between">
        <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-lg text-indigo-400 group-hover:scale-110 transition-transform">
          {icon}
        </div>
        {badge && (
          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700/50">
            {badge}
          </span>
        )}
      </div>

      {/* Main Stat Value & Label */}
      <div className="mt-4">
        <div className="flex items-baseline space-x-2">
          <span className="text-3xl font-extrabold text-white tracking-tight">{value}</span>
        </div>
        <p className="text-xs font-medium text-slate-400 mt-1">{label}</p>
      </div>

      {/* Subtle bottom gradient accent */}
      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-indigo-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
    </div>
  );
}

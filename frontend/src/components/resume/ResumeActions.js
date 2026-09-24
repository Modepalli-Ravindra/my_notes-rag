'use client';

export default function ResumeActions({ documentId, onSelectAction }) {
  const actions = [
    { id: 'analyze', title: 'Analyze Resume', icon: '🔍', desc: 'Extract structured stack, experience, and question triggers', color: 'border-indigo-500/40 hover:border-indigo-500 text-indigo-400' },
    { id: 'viva', title: 'Start Viva', icon: '🎤', desc: 'Interactive live Q&A with real-time feedback & Mana explanations', color: 'border-purple-500/40 hover:border-purple-500 text-purple-400' },
    { id: 'hr', title: 'HR Interview', icon: '💼', desc: 'Behavioral, situational, and culture-fit coaching questions', color: 'border-blue-500/40 hover:border-blue-500 text-blue-400' },
    { id: 'technical', title: 'Technical Interview', icon: '⚡', desc: 'Deep technical questions grounded in your resume skills', color: 'border-amber-500/40 hover:border-amber-500 text-amber-400' },
    { id: 'project', title: 'Project Defense', icon: '🛡️', desc: 'Architecture, trade-offs, and technical defense of your projects', color: 'border-pink-500/40 hover:border-pink-500 text-pink-400' },
    { id: 'coding', title: 'Coding Interview', icon: '💻', desc: 'Hands-on coding challenges matched to your resume stack', color: 'border-emerald-500/40 hover:border-emerald-500 text-emerald-400' },
  ];

  return (
    <div className="w-full bg-[#111827]/80 backdrop-blur-md rounded-2xl border border-slate-800 p-6 shadow-xl">
      <h3 className="text-lg font-extrabold text-white mb-4 flex items-center gap-2">
        <span>🚀</span> Interview Preparation Suite
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {actions.map((act) => (
          <button
            key={act.id}
            onClick={() => onSelectAction && onSelectAction(act.id, documentId)}
            className={`p-4 bg-slate-900/90 hover:bg-slate-800/90 border rounded-xl text-left transition-all group flex flex-col justify-between ${act.color}`}
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-2xl">{act.icon}</span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                  Launch →
                </span>
              </div>
              <h4 className="text-sm font-bold text-white group-hover:text-indigo-200 transition-colors">
                {act.title}
              </h4>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                {act.desc}
              </p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

'use client';

import { useState, useEffect } from 'react';

export default function InterviewSection({ defaultDocumentId }) {
  const [mode, setMode] = useState('technical');
  const [role, setRole] = useState('AI/ML Engineer');
  const [difficulty, setDifficulty] = useState('medium');
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [coachingData, setCoachingData] = useState({});

  const loadQuestions = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/resume/questions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: defaultDocumentId || 'b8f2cb48',
          mode,
          role,
          difficulty,
          count: 5
        })
      });
      const data = await res.json();
      setQuestions(data.questions || []);
    } catch (err) {
      console.log('Fetch interview questions error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQuestions();
  }, [mode, role, difficulty, defaultDocumentId]);

  const fetchCoaching = async (qText, qId) => {
    if (coachingData[qId]) return;

    try {
      const res = await fetch('http://127.0.0.1:8000/resume/coaching', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: qText,
          document_id: defaultDocumentId || 'b8f2cb48',
          include_notes_rag: true
        })
      });
      const data = await res.json();
      setCoachingData((prev) => ({ ...prev, [qId]: data }));
    } catch (err) {
      console.log('Coaching fetch error:', err);
    }
  };

  return (
    <section id="interview-section" className="space-y-6 pt-4">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-800/80">
        <div>
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <span>💼 Interview Mode & Answer Coaching</span>
            <span className="text-xs bg-indigo-500/20 text-indigo-400 font-semibold px-2.5 py-0.5 rounded-full border border-indigo-500/30">
              Mana-Style Coaching
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Practice interview questions with structured responses, key points, and Mana-style explanations.
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Target Role Selector */}
          <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="bg-slate-900 border border-slate-700/80 text-xs font-semibold text-indigo-300 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
          >
            <option value="AI/ML Engineer">AI/ML Engineer</option>
            <option value="Python Developer">Python Developer</option>
            <option value="Full Stack Developer">Full Stack Developer</option>
            <option value="Data Analyst">Data Analyst</option>
          </select>

          {/* Mode Selector */}
          {['technical', 'hr', 'project', 'mixed'].map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold capitalize transition-all cursor-pointer ${
                mode === m
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center bg-slate-900/60 rounded-2xl border border-slate-800 space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Generating grounded interview questions...</p>
        </div>
      ) : (
        <div className="space-y-4">
          {questions.map((q, idx) => {
            const coaching = coachingData[q.id];
            return (
              <div
                key={q.id || idx}
                className="glass-card rounded-2xl p-6 border border-slate-800 hover:border-indigo-500/40 transition-all space-y-4 bg-slate-900/80"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-indigo-400">Question {idx + 1}</span>
                      <span className="text-[10px] bg-indigo-500/10 text-indigo-300 font-semibold px-2 py-0.5 rounded-full border border-indigo-500/30 uppercase">
                        {q.topic || q.related_section || 'Technical'}
                      </span>
                    </div>
                    <h4 className="text-base font-bold text-white leading-snug">
                      "{q.question}"
                    </h4>
                  </div>
                  <button
                    onClick={() => fetchCoaching(q.question, q.id)}
                    className="px-4 py-2 rounded-xl bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 font-semibold text-xs transition-all whitespace-nowrap cursor-pointer"
                  >
                    {coaching ? 'Coaching Active ✓' : 'Get Coaching 💡'}
                  </button>
                </div>

                {/* Coaching Card Display */}
                {coaching && (
                  <div className="mt-3 p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 text-xs animate-in fade-in duration-200">
                    <div className="space-y-1">
                      <p className="font-bold text-emerald-400">💼 Interview-Ready Answer:</p>
                      <p className="text-slate-200 leading-relaxed bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                        {coaching.interview_ready_answer}
                      </p>
                    </div>

                    {coaching.mana_style_explanation && (
                      <div className="space-y-1 bg-indigo-950/40 p-3.5 rounded-lg border border-indigo-500/30">
                        <p className="font-bold text-indigo-300">🗣️ Mana-Style Explanation:</p>
                        <p className="text-indigo-100 font-medium leading-relaxed font-sans">
                          {coaching.mana_style_explanation}
                        </p>
                      </div>
                    )}

                    {coaching.key_points && (
                      <div className="space-y-1">
                        <p className="font-bold text-amber-300">📌 Key Points to Remember:</p>
                        <div className="flex flex-wrap gap-1.5 pt-0.5">
                          {coaching.key_points.map((kp, kidx) => (
                            <span key={kidx} className="px-2.5 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30 text-[11px]">
                              • {kp}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {coaching.follow_up_question && (
                      <div className="space-y-1 pt-1 border-t border-slate-800/80">
                        <p className="font-bold text-slate-400 text-[11px]">🔮 Possible Follow-up Question:</p>
                        <p className="text-slate-300 text-xs italic">"{coaching.follow_up_question}"</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';

function InterviewPageContent() {
  const searchParams = useSearchParams();
  const initialDocId = searchParams.get('document_id') || '';
  const initialMode = searchParams.get('mode') || 'technical';

  const [resumes, setResumes] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(initialDocId);
  const [mode, setMode] = useState(initialMode);
  const [targetRole, setTargetRole] = useState('Full Stack Software Engineer');
  const [difficulty, setDifficulty] = useState('medium');
  const [questionCount, setQuestionCount] = useState(5);
  const [includeNotes, setIncludeNotes] = useState(true);

  const [loading, setLoading] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [coaching, setCoaching] = useState(null);
  const [loadingCoaching, setLoadingCoaching] = useState(false);

  const API_BASE = 'http://127.0.0.1:8000';

  useEffect(() => {
    fetch(`${API_BASE}/documents`)
      .then((res) => res.json())
      .then((data) => {
        if (data.documents) {
          const resDocs = data.documents.filter((d) => d.document_type === 'RESUME' || d.document_id === initialDocId);
          setResumes(resDocs.length > 0 ? resDocs : data.documents);
          if (!selectedDocId && resDocs.length > 0) {
            setSelectedDocId(resDocs[0].document_id);
          }
        }
      })
      .catch((err) => console.error(err));
  }, []);

  const handleGenerateQuestions = async () => {
    setLoading(true);
    setQuestions([]);
    setSelectedQuestion(null);
    setCoaching(null);

    try {
      const res = await fetch(`${API_BASE}/resume/questions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: selectedDocId || 'b8f2cb48',
          mode: mode,
          role: targetRole,
          difficulty: difficulty,
          count: parseInt(questionCount, 10),
        }),
      });

      const data = await res.json();
      if (res.ok) {
        setQuestions(data.questions || []);
      } else {
        alert(data.detail || 'Failed to generate interview questions');
      }
    } catch (err) {
      alert('Error generating questions: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGetCoaching = async (questionText) => {
    setSelectedQuestion(questionText);
    setLoadingCoaching(true);
    setCoaching(null);

    try {
      const res = await fetch(`${API_BASE}/resume/coaching`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: questionText,
          document_id: selectedDocId || null,
          include_notes_rag: includeNotes,
        }),
      });

      const data = await res.json();
      if (res.ok) {
        setCoaching(data);
      } else {
        alert(data.detail || 'Failed to generate coaching');
      }
    } catch (err) {
      alert('Error getting coaching: ' + err.message);
    } finally {
      setLoadingCoaching(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#090d16] text-slate-100 overflow-hidden">
      <Sidebar activeTab="interview" />
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Header activeTab="interview" />
        <main className="p-6 md:p-8 max-w-6xl mx-auto w-full space-y-6">
          <div className="border-b border-slate-800 pb-4">
            <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
              <span>💼</span> Interview Coaching Engine
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Practice HR, Technical, Project Defense, and Role-Based interview questions tailored to your experience and study notes.
            </p>
          </div>

          {/* Configuration Form */}
          <div className="bg-[#111827]/80 backdrop-blur-md rounded-2xl border border-slate-800 p-6 shadow-xl space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Interview Mode
                </label>
                <select
                  value={mode}
                  onChange={(e) => setMode(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="hr">HR / Behavioral</option>
                  <option value="technical">Technical Deep-Dive</option>
                  <option value="project">Project Defense</option>
                  <option value="mixed">Role-Based (Custom)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Target Job Role
                </label>
                <input
                  type="text"
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                  placeholder="e.g. AI Engineer, Full Stack Developer"
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Resume Document
                </label>
                <select
                  value={selectedDocId}
                  onChange={(e) => setSelectedDocId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="">(None - General Practice)</option>
                  {resumes.map((doc) => (
                    <option key={doc.document_id} value={doc.document_id}>
                      {doc.original_filename || doc.document_id}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Difficulty
                </label>
                <select
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Question Count
                </label>
                <select
                  value={questionCount}
                  onChange={(e) => setQuestionCount(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value={3}>3 Questions</option>
                  <option value={5}>5 Questions</option>
                  <option value={10}>10 Questions</option>
                </select>
              </div>

              <div className="flex items-center pt-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeNotes}
                    onChange={(e) => setIncludeNotes(e.target.checked)}
                    className="w-4 h-4 rounded text-indigo-600 bg-slate-900 border-slate-700"
                  />
                  <span className="text-xs font-semibold text-slate-300">
                    Incorporate study notes
                  </span>
                </label>
              </div>
            </div>

            <div className="flex justify-end pt-3">
              <button
                onClick={handleGenerateQuestions}
                disabled={loading}
                className="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-sm rounded-xl shadow-lg transition-all flex items-center gap-2"
              >
                {loading && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                <span>Generate Questions</span>
              </button>
            </div>
          </div>

          {/* Generated Questions List */}
          {questions.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-base font-bold text-white uppercase tracking-wider">
                Tailored Interview Questions ({questions.length})
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {questions.map((q, idx) => (
                  <div
                    key={idx}
                    className="bg-[#111827]/80 backdrop-blur-md rounded-xl border border-slate-800 p-5 shadow-lg flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[11px] font-bold text-indigo-400 uppercase px-2 py-0.5 rounded bg-indigo-950/60 border border-indigo-800/40">
                          {q.type || mode}
                        </span>
                        <span className="text-[11px] font-semibold text-slate-400">
                          {q.difficulty || difficulty}
                        </span>
                      </div>
                      <p className="text-sm font-semibold text-white leading-relaxed">
                        {q.question}
                      </p>
                      {q.context && (
                        <p className="text-xs text-slate-400 mt-2 bg-slate-900/60 p-2 rounded border border-slate-800">
                          🎯 Context: {q.context}
                        </p>
                      )}
                    </div>

                    <button
                      onClick={() => handleGetCoaching(q.question)}
                      className="mt-4 w-full py-2 bg-slate-800 hover:bg-slate-700 text-indigo-300 font-semibold text-xs rounded-lg border border-slate-700 transition-colors"
                    >
                      Get Coaching & Mana Explanation →
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Selected Question Coaching Card */}
          {selectedQuestion && (
            <div className="bg-[#111827]/90 backdrop-blur-md rounded-2xl border border-indigo-800/60 p-6 shadow-2xl space-y-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>💡</span> Expert Answer Coaching
              </h3>

              <div className="p-3 bg-slate-900 rounded-xl border border-slate-800 text-sm font-semibold text-indigo-300">
                "{selectedQuestion}"
              </div>

              {loadingCoaching ? (
                <div className="p-6 text-center text-slate-400 space-y-2">
                  <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                  <p className="text-xs">Generating model response & Mana-style explanation...</p>
                </div>
              ) : (
                coaching && (
                  <div className="space-y-4">
                    {/* Standard Model Answer */}
                    <div className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 text-xs text-slate-200">
                      <p className="font-bold text-indigo-300 mb-1">🎯 Model Answer Structure:</p>
                      <p className="leading-relaxed whitespace-pre-line">{coaching.coaching_answer || coaching.model_answer}</p>
                    </div>

                    {/* Mana-Style Explanation */}
                    <div className="p-4 bg-purple-950/40 rounded-xl border border-purple-800/60 text-xs">
                      <p className="font-extrabold text-purple-300 mb-1 flex items-center gap-1">
                        <span>✨</span> Mana-Style Explanation:
                      </p>
                      <p className="text-purple-100 leading-relaxed">
                        {coaching.mana_explanation}
                      </p>
                    </div>

                    {/* Key points to include */}
                    {coaching.key_points && (
                      <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 text-xs">
                        <p className="font-bold text-emerald-400 mb-1">📌 Key points to emphasize:</p>
                        <ul className="list-disc list-inside space-y-1 text-slate-300">
                          {coaching.key_points.map((pt, i) => (
                            <li key={i}>{pt}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default function InterviewPage() {
  return (
    <Suspense fallback={<div className="p-8 text-white">Loading Interview Coaching...</div>}>
      <InterviewPageContent />
    </Suspense>
  );
}

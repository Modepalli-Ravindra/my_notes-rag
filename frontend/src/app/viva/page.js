'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';

function VivaPageContent() {
  const searchParams = useSearchParams();
  const initialDocId = searchParams.get('document_id') || '';

  const [resumes, setResumes] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(initialDocId);
  const [vivaMode, setVivaMode] = useState('resume');
  const [difficulty, setDifficulty] = useState('medium');
  const [includeNotes, setIncludeNotes] = useState(true);

  // Session state
  const [sessionActive, setSessionActive] = useState(false);
  const [loadingStart, setLoadingStart] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [userAnswer, setUserAnswer] = useState('');
  const [submittingAnswer, setSubmittingAnswer] = useState(false);
  const [feedbackHistory, setFeedbackHistory] = useState([]);
  const [currentFeedback, setCurrentFeedback] = useState(null);

  const API_BASE = 'http://127.0.0.1:8000';

  useEffect(() => {
    // Fetch available documents to find RESUME docs
    fetch(`${API_BASE}/documents`)
      .then((res) => res.json())
      .then((data) => {
        if (data.documents) {
          const resDocs = data.documents.filter(
            (d) => d.document_type === 'RESUME' || d.document_id === initialDocId
          );
          setResumes(resDocs.length > 0 ? resDocs : data.documents);
          if (!selectedDocId && resDocs.length > 0) {
            setSelectedDocId(resDocs[0].document_id);
          }
        }
      })
      .catch((err) => console.error('Failed to load documents:', err));
  }, []);

  const handleStartViva = async () => {
    setLoadingStart(true);
    setFeedbackHistory([]);
    setCurrentFeedback(null);

    try {
      const res = await fetch(`${API_BASE}/resume/session/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: selectedDocId || null,
          mode: vivaMode,
          difficulty: difficulty,
        }),
      });

      const data = await res.json();
      if (res.ok) {
        setQuestions(data.questions || []);
        setCurrentIndex(0);
        setSessionActive(true);
      } else {
        alert(data.detail || 'Failed to start viva session');
      }
    } catch (err) {
      alert('Error starting viva session: ' + err.message);
    } finally {
      setLoadingStart(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!userAnswer.trim()) return;

    setSubmittingAnswer(true);
    const currentQ = questions[currentIndex]?.question || 'General Question';

    try {
      const res = await fetch(`${API_BASE}/resume/session/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: selectedDocId || null,
          question: currentQ,
          user_answer: userAnswer,
          mode: vivaMode,
          include_notes_rag: includeNotes,
        }),
      });

      const data = await res.json();
      if (res.ok) {
        setCurrentFeedback(data);
        setFeedbackHistory((prev) => [...prev, { question: currentQ, answer: userAnswer, feedback: data }]);
      } else {
        alert(data.detail || 'Failed to submit answer');
      }
    } catch (err) {
      alert('Error evaluating answer: ' + err.message);
    } finally {
      setSubmittingAnswer(false);
    }
  };

  const handleNextQuestion = () => {
    setCurrentFeedback(null);
    setUserAnswer('');
    if (currentIndex < questions.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    } else {
      setSessionActive(false);
      alert('🎉 Viva Session Completed!');
    }
  };

  return (
    <div className="flex h-screen bg-[#090d16] text-slate-100 overflow-hidden">
      <Sidebar activeTab="viva" />
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Header activeTab="viva" />
        <main className="p-6 md:p-8 max-w-5xl mx-auto w-full space-y-6">
          <div className="border-b border-slate-800 pb-4">
            <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
              <span>🎤</span> Viva Examination Room
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Practice live technical & resume defenses with instant qualitative evaluation and Mana-style explanations.
            </p>
          </div>

          {!sessionActive ? (
            <div className="bg-[#111827]/80 backdrop-blur-md rounded-2xl border border-slate-800 p-6 shadow-xl space-y-5">
              <h2 className="text-lg font-bold text-white">Setup Your Viva Session</h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Select Target Resume / Document
                  </label>
                  <select
                    value={selectedDocId}
                    onChange={(e) => setSelectedDocId(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="">(None - General Technical Viva)</option>
                    {resumes.map((doc) => (
                      <option key={doc.document_id} value={doc.document_id}>
                        {doc.original_filename || doc.document_id} [{doc.document_type || 'PDF'}]
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Viva Type / Mode
                  </label>
                  <select
                    value={vivaMode}
                    onChange={(e) => setVivaMode(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="resume">Resume Deep-Dive</option>
                    <option value="technical">Core Technical Concepts</option>
                    <option value="project">Project Defense</option>
                    <option value="general">General CS Viva</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Difficulty Level
                  </label>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="easy">Easy (Fundamentals)</option>
                    <option value="medium">Medium (Standard Defense)</option>
                    <option value="hard">Hard (Rigorous Architectural)</option>
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
                      Use my RAG notes to enhance questions
                    </span>
                  </label>
                </div>
              </div>

              <div className="pt-4 flex justify-end">
                <button
                  onClick={handleStartViva}
                  disabled={loadingStart}
                  className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-sm rounded-xl shadow-lg shadow-indigo-500/25 transition-all flex items-center gap-2"
                >
                  {loadingStart && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                  <span>Start Viva Examination</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Question Card */}
              <div className="bg-[#111827]/90 backdrop-blur-md rounded-2xl border border-slate-800 p-6 shadow-xl space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider bg-indigo-950/60 border border-indigo-800/40 px-3 py-1 rounded-full">
                    Question {currentIndex + 1} of {questions.length}
                  </span>
                  <button
                    onClick={() => setSessionActive(false)}
                    className="text-xs text-slate-400 hover:text-white underline"
                  >
                    End Session
                  </button>
                </div>

                <h3 className="text-lg font-bold text-white leading-snug">
                  {questions[currentIndex]?.question}
                </h3>

                {/* Answer Area */}
                {!currentFeedback ? (
                  <div className="space-y-3 pt-2">
                    <textarea
                      rows={4}
                      value={userAnswer}
                      onChange={(e) => setUserAnswer(e.target.value)}
                      placeholder="Type your answer clearly as you would explain to an interviewer..."
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                    />
                    <div className="flex justify-end">
                      <button
                        onClick={handleSubmitAnswer}
                        disabled={submittingAnswer || !userAnswer.trim()}
                        className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center gap-2 disabled:opacity-50"
                      >
                        {submittingAnswer && <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                        <span>Submit Answer</span>
                      </button>
                    </div>
                  </div>
                ) : (
                  /* Feedback Display with Mana-Style Explanation */
                  <div className="mt-4 space-y-4 border-t border-slate-800 pt-4">
                    <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-emerald-400 flex items-center gap-1">
                          <span>📊</span> Qualitative Feedback Score: {currentFeedback.score || 8}/10
                        </span>
                      </div>

                      {/* What was done well */}
                      {currentFeedback.what_you_did_well && (
                        <div className="p-3 rounded-lg bg-emerald-950/30 border border-emerald-800/40 text-xs">
                          <p className="font-bold text-emerald-300">✅ What you did well:</p>
                          <p className="text-slate-200 mt-1">{currentFeedback.what_you_did_well}</p>
                        </div>
                      )}

                      {/* What was missing */}
                      {currentFeedback.what_you_missed && (
                        <div className="p-3 rounded-lg bg-amber-950/30 border border-amber-800/40 text-xs">
                          <p className="font-bold text-amber-300">💡 What was missing / needs depth:</p>
                          <p className="text-slate-200 mt-1">{currentFeedback.what_you_missed}</p>
                        </div>
                      )}

                      {/* Mana-Style Explanation */}
                      {currentFeedback.mana_explanation && (
                        <div className="p-4 rounded-xl bg-purple-950/40 border border-purple-800/60 text-xs space-y-1">
                          <p className="font-extrabold text-purple-300 flex items-center gap-1 text-sm">
                            <span>✨</span> Mana-Style Explanation:
                          </p>
                          <p className="text-purple-100 leading-relaxed text-xs">
                            {currentFeedback.mana_explanation}
                          </p>
                        </div>
                      )}

                      {/* Follow up question */}
                      {currentFeedback.follow_up_question && (
                        <div className="p-3 rounded-lg bg-indigo-950/40 border border-indigo-800/40 text-xs">
                          <p className="font-bold text-indigo-300">❓ Adaptive Follow-up Question:</p>
                          <p className="text-slate-200 mt-1 italic">{currentFeedback.follow_up_question}</p>
                        </div>
                      )}
                    </div>

                    <div className="flex justify-end pt-2">
                      <button
                        onClick={handleNextQuestion}
                        className="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold text-xs rounded-xl shadow-lg transition-all"
                      >
                        {currentIndex < questions.length - 1 ? 'Next Question →' : 'Complete Viva Session 🎉'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default function VivaPage() {
  return (
    <Suspense fallback={<div className="p-8 text-white">Loading Viva Examination...</div>}>
      <VivaPageContent />
    </Suspense>
  );
}

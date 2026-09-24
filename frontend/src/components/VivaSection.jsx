'use client';

import { useState } from 'react';

export default function VivaSection({ defaultDocumentId }) {
  const [mode, setMode] = useState('resume');
  const [difficulty, setDifficulty] = useState('medium');
  const [session, setSession] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswer, setUserAnswer] = useState('');
  const [evaluating, setEvaluating] = useState(false);
  const [evaluation, setEvaluation] = useState(null);
  const [history, setHistory] = useState([]);

  const handleStartViva = async () => {
    setEvaluating(true);
    setEvaluation(null);
    setHistory([]);
    setCurrentQuestionIndex(0);

    try {
      const res = await fetch('http://127.0.0.1:8000/resume/session/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: defaultDocumentId || 'b8f2cb48',
          mode,
          difficulty
        })
      });
      const data = await res.json();
      setSession(data);
    } catch (err) {
      console.log('Start viva error:', err);
    } finally {
      setEvaluating(false);
    }
  };

  const currentQuestion = session?.questions?.[currentQuestionIndex]?.question || session?.current_question || "Explain your technical project architecture and key design decisions.";

  const handleSubmitAnswer = async (e) => {
    e.preventDefault();
    if (!userAnswer.trim()) return;

    setEvaluating(true);

    try {
      const res = await fetch('http://127.0.0.1:8000/resume/session/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: defaultDocumentId || 'b8f2cb48',
          question: currentQuestion,
          user_answer: userAnswer.trim(),
          mode,
          include_notes_rag: true
        })
      });

      const data = await res.json();
      setEvaluation(data);
      setHistory((prev) => [
        ...prev,
        {
          question: currentQuestion,
          answer: userAnswer.trim(),
          evaluation: data
        }
      ]);
    } catch (err) {
      console.log('Viva evaluation error:', err);
    } finally {
      setEvaluating(false);
    }
  };

  const handleNextQuestion = () => {
    setUserAnswer('');
    setEvaluation(null);

    if (evaluation?.follow_up_question) {
      // Set follow up question as current question
      if (session && session.questions) {
        session.questions[currentQuestionIndex + 1] = {
          id: `f${currentQuestionIndex + 1}`,
          question: evaluation.follow_up_question
        };
      }
    }

    setCurrentQuestionIndex((prev) => prev + 1);
  };

  return (
    <section id="viva-section" className="space-y-6 pt-4">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-800/80">
        <div>
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <span>🎤 Interactive Viva Room</span>
            <span className="text-xs bg-indigo-500/20 text-indigo-400 font-semibold px-2.5 py-0.5 rounded-full border border-indigo-500/30">
              Mana-Style Feedback Active
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Simulate viva examinations with real-time answer evaluation and Mana-style explanations.
          </p>
        </div>

        {/* Mode Selector */}
        <div className="flex flex-wrap items-center gap-2">
          {['resume', 'project', 'technical', 'general'].map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold capitalize transition-all cursor-pointer ${
                mode === m
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {m} Viva
            </button>
          ))}
        </div>
      </div>

      {!session ? (
        /* Start Room Card */
        <div className="glass-card rounded-2xl p-8 text-center space-y-4 max-w-xl mx-auto border border-indigo-500/30 bg-slate-900/90">
          <div className="w-14 h-14 rounded-2xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-3xl mx-auto text-indigo-400 shadow-inner">
            🎙️
          </div>
          <div>
            <h4 className="text-lg font-bold text-white">Ready for your Viva Exam?</h4>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Answer viva questions, receive instant technical critique, and learn with natural <span className="text-indigo-400 font-semibold">Mana-Style explanations ("Simple ga cheppalante...")</span>.
            </p>
          </div>
          <button
            onClick={handleStartViva}
            disabled={evaluating}
            className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition-all cursor-pointer"
          >
            {evaluating ? 'Initializing Session...' : 'Start Viva Examination 🚀'}
          </button>
        </div>
      ) : (
        /* Active Viva Room */
        <div className="space-y-6">
          {/* Question Card */}
          <div className="glass-card rounded-2xl p-6 border border-indigo-500/30 bg-gradient-to-r from-slate-900 via-indigo-950/20 to-slate-900 space-y-3 shadow-xl">
            <div className="flex items-center justify-between text-xs text-indigo-400 font-bold">
              <span>Question {currentQuestionIndex + 1}</span>
              <span className="uppercase text-[10px] bg-indigo-500/20 px-2 py-0.5 rounded-full border border-indigo-500/30">
                {mode} Mode
              </span>
            </div>
            <h3 className="text-base sm:text-lg font-bold text-white leading-snug">
              "{currentQuestion}"
            </h3>
          </div>

          {/* Answer Input Form */}
          {!evaluation && (
            <form onSubmit={handleSubmitAnswer} className="space-y-3">
              <div className="glass-card rounded-2xl p-5 border border-slate-800 space-y-3">
                <label className="text-xs font-bold text-slate-300 block">Your Answer:</label>
                <textarea
                  value={userAnswer}
                  onChange={(e) => setUserAnswer(e.target.value)}
                  rows={4}
                  placeholder="Explain your concept clearly... (e.g., We used FAISS for dense vector similarity search combined with BM25...)"
                  className="w-full bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-500 text-xs rounded-xl p-3.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                />
                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={evaluating || !userAnswer.trim()}
                    className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-xs shadow-md shadow-indigo-600/30 transition-all flex items-center gap-2 cursor-pointer"
                  >
                    {evaluating ? 'Evaluating Answer...' : 'Submit Viva Answer 📤'}
                  </button>
                </div>
              </div>
            </form>
          )}

          {/* Evaluation & Mana-Style Feedback Display */}
          {evaluation && (
            <div className="space-y-5 animate-in fade-in duration-300">
              <div className="glass-card rounded-2xl p-6 border border-emerald-500/30 bg-slate-900/90 space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-bold text-emerald-400 flex items-center gap-2">
                    <span>💡 Examiner Feedback</span>
                  </h4>
                  {evaluation.feedback?.qualitative_status && (
                    <span className="text-xs font-bold px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                      {evaluation.feedback.qualitative_status}
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-1">
                    <p className="font-bold text-emerald-300">✅ What You Did Well:</p>
                    <p className="text-slate-300 leading-relaxed">{evaluation.feedback?.what_you_did_well}</p>
                  </div>
                  <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-500/30 space-y-1">
                    <p className="font-bold text-amber-300">⚠️ Key Details to Add:</p>
                    <p className="text-slate-300 leading-relaxed">{evaluation.feedback?.what_you_missed}</p>
                  </div>
                </div>

                {/* Mana-Style Explanation Box */}
                {evaluation.mana_style_explanation && (
                  <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-500/40 space-y-2">
                    <div className="flex items-center space-x-2 text-indigo-300 font-bold text-xs">
                      <span>🗣️ Mana-Style Explanation (Simple ga cheppalante...):</span>
                    </div>
                    <p className="text-xs text-indigo-100 font-medium leading-relaxed font-sans">
                      {evaluation.mana_style_explanation}
                    </p>
                  </div>
                )}

                {/* Follow-up Question Preview */}
                {evaluation.follow_up_question && (
                  <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">
                      Suggested Follow-Up Question
                    </span>
                    <p className="text-xs font-bold text-white">
                      "{evaluation.follow_up_question}"
                    </p>
                  </div>
                )}

                <div className="pt-2 flex justify-end">
                  <button
                    onClick={handleNextQuestion}
                    className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md shadow-indigo-600/30 transition-all cursor-pointer"
                  >
                    Next Question →
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

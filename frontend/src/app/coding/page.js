'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import DynamicEditor from '@monaco-editor/react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';

function CodingPageContent() {
  const searchParams = useSearchParams();
  const initialDocId = searchParams.get('document_id') || '';

  const [language, setLanguage] = useState('Python');
  const [difficulty, setDifficulty] = useState('medium');
  const [topic, setTopic] = useState('arrays');
  const [targetRole, setTargetRole] = useState('Software Engineer');
  const [includeNotes, setIncludeNotes] = useState(true);

  const [loadingProblem, setLoadingProblem] = useState(false);
  const [problem, setProblem] = useState(null);
  const [code, setCode] = useState('');

  // Execution & Submission state
  const [running, setRunning] = useState(false);
  const [runResult, setRunResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [evalResult, setEvalResult] = useState(null);

  const API_BASE = 'http://127.0.0.1:8000';

  const monacoLangMap = {
    Python: 'python',
    JavaScript: 'javascript',
    Java: 'java',
    SQL: 'sql',
  };

  const handleGenerateProblem = async () => {
    setLoadingProblem(true);
    setProblem(null);
    setRunResult(null);
    setEvalResult(null);

    try {
      const res = await fetch(`${API_BASE}/coding/problem/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          language,
          difficulty,
          topic,
          role: targetRole,
          document_id: initialDocId || null,
          include_notes_rag: includeNotes,
        }),
      });

      const data = await res.json();
      if (res.ok) {
        setProblem(data);
        setCode(data.starter_code || '# Write solution here\n');
      } else {
        alert(data.detail || 'Failed to generate problem');
      }
    } catch (err) {
      alert('Error generating problem: ' + err.message);
    } finally {
      setLoadingProblem(false);
    }
  };

  const handleResetCode = () => {
    if (problem?.starter_code) {
      setCode(problem.starter_code);
    }
  };

  const handleRunCode = async () => {
    if (!code.trim()) return;
    setRunning(true);
    setRunResult(null);

    try {
      const res = await fetch(`${API_BASE}/coding/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          language,
          code,
          setup_sql: problem?.setup_sql || null,
        }),
      });

      const data = await res.json();
      setRunResult(data);
    } catch (err) {
      setRunResult({
        success: False,
        status: 'ERROR',
        stderr: err.message,
      });
    } finally {
      setRunning(false);
    }
  };

  const handleSubmitCode = async () => {
    if (!code.trim() || !problem) return;
    setSubmitting(true);
    setEvalResult(null);

    try {
      const res = await fetch(`${API_BASE}/coding/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          language,
          code,
          problem_statement: problem.statement,
          starter_code: problem.starter_code,
          setup_sql: problem.setup_sql || null,
        }),
      });

      const data = await res.json();
      setEvalResult(data);
    } catch (err) {
      alert('Error evaluating code: ' + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#090d16] text-slate-100 overflow-hidden">
      <Sidebar activeTab="coding" />
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Header activeTab="coding" />
        <main className="p-6 md:p-8 max-w-7xl mx-auto w-full space-y-6">
          <div className="border-b border-slate-800 pb-4">
            <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
              <span>💻</span> Coding Interview Environment
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Solve live code challenges in Python, Java, JavaScript, or SQL with isolated execution and Mana-style algorithmic evaluations.
            </p>
          </div>

          {/* Selector / Configuration Bar */}
          <div className="bg-[#111827]/80 backdrop-blur-md rounded-2xl border border-slate-800 p-5 shadow-xl">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                  Language
                </label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="Python">Python 3</option>
                  <option value="JavaScript">JavaScript (Node.js)</option>
                  <option value="Java">Java</option>
                  <option value="SQL">SQL (SQLite)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                  Difficulty
                </label>
                <select
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                  Topic Area
                </label>
                <select
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="arrays">Arrays & Hashing</option>
                  <option value="strings">Strings & Parsing</option>
                  <option value="trees">Trees & Graphs</option>
                  <option value="dynamic_programming">Dynamic Programming</option>
                  <option value="sql_queries">SQL Joins & Grouping</option>
                </select>
              </div>

              <div className="flex items-center pt-5">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeNotes}
                    onChange={(e) => setIncludeNotes(e.target.checked)}
                    className="w-3.5 h-3.5 rounded text-indigo-600 bg-slate-900 border-slate-700"
                  />
                  <span className="text-xs font-semibold text-slate-300">
                    Use study notes
                  </span>
                </label>
              </div>

              <div className="flex items-center justify-end pt-5">
                <button
                  onClick={handleGenerateProblem}
                  disabled={loadingProblem}
                  className="w-full py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center justify-center gap-1.5"
                >
                  {loadingProblem && <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                  <span>Generate Challenge</span>
                </button>
              </div>
            </div>
          </div>

          {/* Main IDE Workspace */}
          {problem ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Problem Description Panel */}
              <div className="bg-[#111827]/90 backdrop-blur-md rounded-2xl border border-slate-800 p-6 shadow-xl space-y-4 max-h-[750px] overflow-y-auto">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <span>📌</span> {problem.title}
                  </h2>
                  <div className="flex gap-2">
                    <span className="text-xs font-semibold px-2.5 py-0.5 rounded bg-indigo-950/80 border border-indigo-800 text-indigo-300">
                      {problem.language}
                    </span>
                    <span className="text-xs font-semibold px-2.5 py-0.5 rounded bg-purple-950/80 border border-purple-800 text-purple-300 capitalize">
                      {problem.difficulty}
                    </span>
                  </div>
                </div>

                <div className="space-y-3 text-xs text-slate-200">
                  <div>
                    <h3 className="font-bold text-slate-400 uppercase tracking-wider mb-1">Problem Statement</h3>
                    <p className="leading-relaxed text-slate-200 text-sm whitespace-pre-line">{problem.statement}</p>
                  </div>

                  {problem.input_format && (
                    <div>
                      <h3 className="font-bold text-slate-400 uppercase tracking-wider mb-1">Input Format</h3>
                      <p className="bg-slate-900/60 p-2.5 rounded border border-slate-800">{problem.input_format}</p>
                    </div>
                  )}

                  {problem.output_format && (
                    <div>
                      <h3 className="font-bold text-slate-400 uppercase tracking-wider mb-1">Output Format</h3>
                      <p className="bg-slate-900/60 p-2.5 rounded border border-slate-800">{problem.output_format}</p>
                    </div>
                  )}

                  {problem.constraints && problem.constraints.length > 0 && (
                    <div>
                      <h3 className="font-bold text-slate-400 uppercase tracking-wider mb-1">Constraints</h3>
                      <ul className="list-disc list-inside bg-slate-900/60 p-2.5 rounded border border-slate-800 space-y-1">
                        {problem.constraints.map((c, i) => (
                          <li key={i}>{c}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {problem.examples && problem.examples.length > 0 && (
                    <div>
                      <h3 className="font-bold text-slate-400 uppercase tracking-wider mb-2">Examples</h3>
                      <div className="space-y-2">
                        {problem.examples.map((ex, i) => (
                          <div key={i} className="p-3 bg-slate-900 rounded-xl border border-slate-800 space-y-1">
                            <p><strong className="text-indigo-400">Input:</strong> <code>{ex.input}</code></p>
                            <p><strong className="text-emerald-400">Output:</strong> <code>{ex.output}</code></p>
                            {ex.explanation && <p className="text-slate-400 italic">Explanation: {ex.explanation}</p>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Editor & Execution Output Panel */}
              <div className="flex flex-col space-y-4">
                {/* Editor Toolbar */}
                <div className="bg-[#111827] rounded-2xl border border-slate-800 p-3 shadow-xl flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-400">Code Editor</span>
                    <span className="text-[10px] text-emerald-400 px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/40">
                      Subprocess Enabled
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleResetCode}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg border border-slate-700 transition-colors"
                    >
                      ↺ Reset
                    </button>
                    <button
                      onClick={handleRunCode}
                      disabled={running}
                      className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg shadow transition-all flex items-center gap-1.5 disabled:opacity-50"
                    >
                      {running && <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                      <span>▶ Run</span>
                    </button>
                    <button
                      onClick={handleSubmitCode}
                      disabled={submitting}
                      className="px-4 py-1.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold rounded-lg shadow transition-all flex items-center gap-1.5 disabled:opacity-50"
                    >
                      {submitting && <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                      <span>✓ Submit</span>
                    </button>
                  </div>
                </div>

                {/* Monaco Code Editor */}
                <div className="rounded-2xl border border-slate-800 overflow-hidden shadow-2xl h-[380px]">
                  <DynamicEditor
                    height="100%"
                    language={monacoLangMap[language] || 'python'}
                    theme="vs-dark"
                    value={code}
                    onChange={(val) => setCode(val || '')}
                    options={{
                      fontSize: 13,
                      minimap: { enabled: false },
                      scrollBeyondLastLine: false,
                      automaticLayout: true,
                    }}
                  />
                </div>

                {/* Output & Evaluation Cards */}
                {runResult && (
                  <div className="bg-[#111827] rounded-xl border border-slate-800 p-4 space-y-2">
                    <div className="flex items-center justify-between text-xs font-bold">
                      <span className="text-indigo-400">Sample Run Output</span>
                      <span className={runResult.success ? 'text-emerald-400' : 'text-red-400'}>
                        {runResult.status}
                      </span>
                    </div>

                    {runResult.status === 'JAVA_MISSING' && (
                      <div className="p-3 bg-amber-950/40 border border-amber-800/50 rounded-lg text-amber-200 text-xs font-semibold">
                        ⚠️ Java compiler/runtime is not installed on this machine.
                      </div>
                    )}

                    {runResult.stdout && (
                      <pre className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs font-mono text-emerald-300 overflow-x-auto">
                        {runResult.stdout}
                      </pre>
                    )}

                    {runResult.stderr && (
                      <pre className="p-3 bg-slate-950 rounded-lg border border-red-900/50 text-xs font-mono text-red-300 overflow-x-auto">
                        {runResult.stderr}
                      </pre>
                    )}
                  </div>
                )}

                {evalResult && (
                  <div className="bg-[#111827] rounded-xl border border-indigo-900/60 p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                        <span>🏆</span> Submission Results
                      </span>
                      <span className={`text-xs font-bold px-2.5 py-0.5 rounded border ${
                        evalResult.status === 'ACCEPTED'
                          ? 'bg-emerald-950 border-emerald-800 text-emerald-300'
                          : 'bg-red-950 border-red-800 text-red-300'
                      }`}>
                        {evalResult.status} ({evalResult.tests_passed}/{evalResult.total_tests} Tests Passed)
                      </span>
                    </div>

                    {evalResult.status === 'JAVA_MISSING' ? (
                      <div className="p-3 bg-amber-950/40 border border-amber-800/50 rounded-lg text-amber-200 text-xs">
                        {evalResult.message}
                      </div>
                    ) : (
                      <>
                        <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800 text-xs text-slate-200">
                          <p className="font-bold text-indigo-300 mb-1">Feedback:</p>
                          <p>{evalResult.feedback}</p>
                        </div>

                        {/* Mana-Style Explanation */}
                        {evalResult.mana_explanation && (
                          <div className="p-4 bg-purple-950/40 rounded-xl border border-purple-800/60 text-xs">
                            <p className="font-extrabold text-purple-300 mb-1 flex items-center gap-1">
                              <span>✨</span> Mana-Style Explanation:
                            </p>
                            <p className="text-purple-100 leading-relaxed">
                              {evalResult.mana_explanation}
                            </p>
                          </div>
                        )}

                        {evalResult.complexity && (
                          <div className="flex gap-4 text-xs font-mono text-slate-300">
                            <span>Time Complexity: <strong className="text-indigo-400">{evalResult.complexity.time}</strong></span>
                            <span>Space Complexity: <strong className="text-purple-400">{evalResult.complexity.space}</strong></span>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-[#111827]/80 backdrop-blur-md rounded-2xl border border-slate-800 p-12 text-center text-slate-400">
              <span className="text-4xl block mb-2">⚡</span>
              <p className="text-base font-semibold text-white">Select Language & Topic above and click "Generate Challenge"</p>
              <p className="text-xs text-slate-400 mt-1">Practice coding challenges with real execution & instant AI code feedback.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default function CodingPage() {
  return (
    <Suspense fallback={<div className="p-8 text-white">Loading Coding Environment...</div>}>
      <CodingPageContent />
    </Suspense>
  );
}

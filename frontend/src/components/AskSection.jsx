'use client';

import { useState } from 'react';

export default function AskSection() {
  const [query, setQuery] = useState('');
  const [provider, setProvider] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const payload = {
        query: query.trim(),
        top_k: 5,
        provider: provider ? provider : null,
        document_id: 'b8f2cb48',
      };

      const res = await fetch('http://127.0.0.1:8000/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Failed to generate answer from RAG server.');
      }

      setResponse(data);
    } catch (err) {
      setError(err.message || 'An error occurred while calling RAG assistant.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="ask-section" className="space-y-4 pt-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-800/60">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <span>💬 Ask Your Handwritten Notes</span>
            <span className="text-xs bg-indigo-500/20 text-indigo-400 font-semibold px-2.5 py-0.5 rounded-full border border-indigo-500/30">
              Step 11 Live RAG
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Query your 167-page Python notes using hybrid vector retrieval + LLM answer grounding.
          </p>
        </div>
      </div>

      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur-sm space-y-4">
        <form onSubmit={handleAsk} className="space-y-3">
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. What is a lambda function? Or What is the LEGB rule?"
              className="flex-1 bg-slate-950/80 border border-slate-800 text-slate-100 placeholder-slate-500 text-sm rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all"
            />

            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="bg-slate-950/80 border border-slate-800 text-slate-300 text-xs rounded-lg px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all cursor-pointer"
            >
              <option value="">Auto Provider (Default)</option>
              <option value="groq">Groq (qwen3.8-27b)</option>
              <option value="openrouter">OpenRouter (free)</option>
              <option value="nvidia">NVIDIA (llama-3.2-11b)</option>
              <option value="gemini">Gemini (gemma-4-26b)</option>
            </select>

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-xs px-5 py-2.5 rounded-lg shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center gap-2 whitespace-nowrap"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Searching & Generating...</span>
                </>
              ) : (
                <span>Ask Notes AI 🚀</span>
              )}
            </button>
          </div>
        </form>

        {error && (
          <div className="bg-rose-950/40 border border-rose-800/60 rounded-lg p-3 text-xs text-rose-300">
            <strong>Error:</strong> {error}
          </div>
        )}

        {response && (
          <div className="space-y-3 pt-2 border-t border-slate-800/80">
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
              <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                <span>🤖 Response</span>
                <span className="bg-slate-800 text-slate-400 font-mono text-[10px] px-2 py-0.5 rounded border border-slate-700">
                  {response.provider} / {response.model}
                </span>
              </span>
              {response.trace && (
                <span className="text-slate-500 text-[11px] font-mono">
                  Latency: {response.trace.latency_ms}ms | Chunks used: {response.retrieval?.results_used || 5}
                </span>
              )}
            </div>

            <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4 text-sm text-slate-200 leading-relaxed whitespace-pre-wrap font-sans">
              {response.answer}
            </div>

            {response.mana_explanation && (
              <div className="bg-gradient-to-r from-indigo-950/40 via-purple-950/40 to-slate-950/60 border border-indigo-800/60 rounded-xl p-4 space-y-2 shadow-lg">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                    <span>🗣️</span> MANA-STYLE EXPLANATION
                  </h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-900/60 text-indigo-200 border border-indigo-700/50">
                    Powered by Gemini
                  </span>
                </div>
                <div className="text-xs sm:text-sm text-slate-200 leading-relaxed whitespace-pre-wrap font-sans">
                  {response.mana_explanation}
                </div>
              </div>
            )}

            {response.sources && response.sources.length > 0 && (
              <div className="flex flex-wrap items-center gap-2 pt-1">
                <span className="text-xs font-semibold text-slate-400">Cited Pages:</span>
                {response.sources.map((src, i) => (
                  <span
                    key={i}
                    className="bg-indigo-950/60 border border-indigo-800/50 text-indigo-300 font-mono text-[11px] px-2.5 py-0.5 rounded-full"
                  >
                    Page {src.page_start === src.page_end ? src.page_start : `${src.page_start}-${src.page_end}`}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

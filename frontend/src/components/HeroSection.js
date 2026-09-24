'use client';

export default function HeroSection({ onUploadClick, onChatClick }) {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-950/70 via-slate-900/80 to-purple-950/60 border border-indigo-500/20 p-6 md:p-8 shadow-xl shadow-indigo-950/20">
      {/* Subtle Background Glow Accent */}
      <div className="absolute -top-24 -right-24 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 max-w-2xl">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold mb-4">
          <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse"></span>
          <span>OCR & FAISS Retrieval Engine</span>
        </div>

        <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white leading-tight">
          Your notes. Your knowledge. <span className="bg-gradient-to-r from-indigo-300 via-purple-300 to-pink-300 bg-clip-text text-transparent">One AI.</span>
        </h2>

        <p className="text-sm md:text-base text-slate-300 mt-3 leading-relaxed">
          Transform your handwritten AI, Python & SQL notes into an interactive RAG knowledge base. Upload handwritten PDF documents, extract text via PaddleOCR, and get instant answers with exact page references.
        </p>

        {/* Action Buttons */}
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <button
            onClick={onUploadClick}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 transition-all transform hover:-translate-y-0.5 active:translate-y-0 flex items-center space-x-2"
          >
            <span>☁️</span>
            <span>Upload Notes</span>
          </button>

          <button
            onClick={onChatClick}
            className="px-5 py-2.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 text-slate-200 hover:text-white font-semibold text-sm border border-slate-700/80 transition-all flex items-center space-x-2"
          >
            <span>💬</span>
            <span>Start Chat</span>
          </button>
        </div>
      </div>
    </div>
  );
}

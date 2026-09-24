'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

export default function DocumentPreviewModal({ doc, isOpen, onClose, initialPage = 1 }) {
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [zoom, setZoom] = useState(100);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [inputPage, setInputPage] = useState(initialPage.toString());

  const documentId = doc?.id || 'b8f2cb48';
  const totalPages = doc?.pageCount || 167;
  const title = doc?.title || 'Document Preview';

  // Sync internal page state when modal opens or doc changes
  useEffect(() => {
    if (isOpen) {
      const pageToLoad = Math.min(Math.max(1, initialPage), totalPages);
      setCurrentPage(pageToLoad);
      setInputPage(pageToLoad.toString());
      setZoom(100);
      setError(null);
      setLoading(true);
    }
  }, [isOpen, doc, initialPage, totalPages]);

  // Update input text when current page changes
  useEffect(() => {
    setInputPage(currentPage.toString());
  }, [currentPage]);

  const handlePrev = useCallback(() => {
    if (currentPage > 1) {
      setCurrentPage((prev) => prev - 1);
      setLoading(true);
      setError(null);
    }
  }, [currentPage]);

  const handleNext = useCallback(() => {
    if (currentPage < totalPages) {
      setCurrentPage((prev) => prev + 1);
      setLoading(true);
      setError(null);
    }
  }, [currentPage, totalPages]);

  const handleZoomIn = () => setZoom((z) => Math.min(z + 25, 250));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 25, 50));
  const handleResetZoom = () => setZoom(100);

  const handlePageInputChange = (e) => {
    setInputPage(e.target.value);
  };

  const handlePageInputSubmit = (e) => {
    e.preventDefault();
    const parsed = parseInt(inputPage, 10);
    if (!isNaN(parsed) && parsed >= 1 && parsed <= totalPages) {
      setCurrentPage(parsed);
      setLoading(true);
      setError(null);
    } else {
      setInputPage(currentPage.toString());
    }
  };

  // Keyboard navigation support (ArrowLeft, ArrowRight, Escape)
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e) => {
      // Don't intercept keypresses inside input elements
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) {
        if (e.key === 'Escape') {
          onClose();
        }
        return;
      }

      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        handlePrev();
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        handleNext();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, handlePrev, handleNext, onClose]);

  if (!isOpen) return null;

  const imageUrl = `http://127.0.0.1:8000/documents/${documentId}/pages/${currentPage}/image`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      {/* Modal Container */}
      <div className="relative w-full max-w-5xl h-[90vh] bg-[#0c121e] border border-slate-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        
        {/* Header / Control Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-3.5 bg-slate-900/90 border-b border-slate-800">
          
          {/* Document Details & Page Counter */}
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 text-sm font-semibold">
              📄
            </div>
            <div>
              <h3 className="font-bold text-slate-100 text-sm sm:text-base leading-tight">
                {title}
              </h3>
              <div className="flex items-center space-x-2 text-xs text-indigo-400 font-semibold mt-0.5">
                <span>Page {currentPage} of {totalPages}</span>
              </div>
            </div>
          </div>

          {/* Center Navigation & Page Jump */}
          <div className="flex items-center space-x-2 bg-slate-950/80 p-1.5 rounded-xl border border-slate-800">
            <button
              onClick={handlePrev}
              disabled={currentPage <= 1}
              title="Previous Page (ArrowLeft)"
              className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed text-slate-200 text-xs font-bold transition-all border border-slate-800"
            >
              ← Prev
            </button>

            <form onSubmit={handlePageInputSubmit} className="flex items-center space-x-1">
              <span className="text-xs text-slate-400 font-medium pl-1">Page</span>
              <input
                type="text"
                value={inputPage}
                onChange={handlePageInputChange}
                onBlur={handlePageInputSubmit}
                className="w-12 text-center bg-slate-900 border border-slate-700/80 rounded-lg text-xs font-semibold text-white py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
              />
              <span className="text-xs text-slate-400 font-medium pr-1">of {totalPages}</span>
            </form>

            <button
              onClick={handleNext}
              disabled={currentPage >= totalPages}
              title="Next Page (ArrowRight)"
              className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed text-slate-200 text-xs font-bold transition-all border border-slate-800"
            >
              Next →
            </button>
          </div>

          {/* Right Zoom & Close Controls */}
          <div className="flex items-center space-x-2">
            <div className="flex items-center bg-slate-950/80 p-1 rounded-xl border border-slate-800 space-x-1">
              <button
                onClick={handleZoomOut}
                disabled={zoom <= 50}
                title="Zoom Out"
                className="w-7 h-7 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-30 text-slate-300 text-xs font-bold transition-all flex items-center justify-center border border-slate-800"
              >
                −
              </button>

              <button
                onClick={handleResetZoom}
                title="Reset Zoom to 100%"
                className="px-2 py-1 text-[11px] font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
              >
                {zoom}%
              </button>

              <button
                onClick={handleZoomIn}
                disabled={zoom >= 250}
                title="Zoom In"
                className="w-7 h-7 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-30 text-slate-300 text-xs font-bold transition-all flex items-center justify-center border border-slate-800"
              >
                +
              </button>
            </div>

            <button
              onClick={onClose}
              title="Close Preview (Escape)"
              className="w-8 h-8 rounded-xl bg-slate-900 hover:bg-rose-500/20 text-slate-400 hover:text-rose-300 border border-slate-800 hover:border-rose-500/30 font-bold transition-all flex items-center justify-center text-sm"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Modal Main Viewing Area */}
        <div className="flex-1 relative overflow-auto p-4 sm:p-8 flex items-center justify-center bg-[#070b14]/90 custom-scrollbar">
          
          {/* Loading Indicator Overlay */}
          {loading && (
            <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-[#070b14]/75 backdrop-blur-xs text-slate-300 space-y-3">
              <div className="w-10 h-10 border-3 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
              <p className="text-xs font-medium text-slate-300">Rendering page {currentPage} of {totalPages}...</p>
            </div>
          )}

          {/* Error Message Display */}
          {error ? (
            <div className="flex flex-col items-center justify-center max-w-md p-6 bg-slate-900 border border-rose-500/30 rounded-2xl text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 text-xl font-bold">
                ⚠️
              </div>
              <h4 className="text-sm font-bold text-slate-100">Page Load Failed</h4>
              <p className="text-xs text-slate-400 leading-relaxed">{error}</p>
              <button
                onClick={() => {
                  setError(null);
                  setLoading(true);
                }}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all"
              >
                Retry Loading
              </button>
            </div>
          ) : (
            /* Handwritten Document Page Image */
            <div
              className="transition-transform duration-200 ease-out origin-center flex items-center justify-center shadow-2xl rounded-lg overflow-hidden border border-slate-800/80 bg-slate-950"
              style={{
                transform: `scale(${zoom / 100})`,
                maxWidth: '100%',
              }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={imageUrl}
                alt={`Handwritten note page ${currentPage}`}
                onLoad={() => setLoading(false)}
                onError={() => {
                  setLoading(false);
                  setError(`Could not fetch page ${currentPage} from server. Ensure backend is running.`);
                }}
                className="max-h-[72vh] w-auto object-contain rounded-lg shadow-inner select-none"
              />
            </div>
          )}
        </div>

        {/* Modal Footer Bar */}
        <div className="px-5 py-2.5 bg-slate-900/80 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center space-x-2 text-[11px]">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>PyMuPDF On-Demand Renderer</span>
          </div>
          <div className="hidden sm:flex items-center space-x-4 text-[11px] text-slate-500">
            <span>Arrow keys (← / →) to navigate</span>
            <span>Esc to close</span>
          </div>
        </div>

      </div>
    </div>
  );
}

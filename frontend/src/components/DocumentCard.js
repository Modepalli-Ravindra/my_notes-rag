'use client';

export default function DocumentCard({ doc, onPreview }) {
  const { title, pageCount, lastUpdated, status, category, icon, statusDetail, chunkCount } = doc;

  const getStatusBadge = (status) => {
    switch (status) {
      case 'READY':
      case 'Ready':
      case 'indexed_and_chunked':
        return (
          <span className="inline-flex items-center space-x-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>READY</span>
          </span>
        );
      case 'OCR_REQUIRED':
        return (
          <span className="inline-flex items-center space-x-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
            <span>OCR REQUIRED</span>
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center space-x-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
            <span>FAILED</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse"></span>
            <span>{status || 'PROCESSING'}</span>
          </span>
        );
    }
  };

  return (
    <div className="glass-card glass-card-hover rounded-2xl p-5 flex flex-col justify-between group">
      <div>
        {/* Top Header Row */}
        <div className="flex items-start justify-between gap-2.5 min-w-0">
          <div className="flex items-center space-x-3 min-w-0 flex-1">
            <div className="w-10 h-10 rounded-xl bg-slate-900 border border-slate-700/60 flex items-center justify-center text-xl shadow-inner shrink-0">
              {icon || '📄'}
            </div>
            <div className="min-w-0 flex-1">
              <span className="text-[10px] font-bold tracking-wider text-indigo-400 uppercase block truncate">
                {category || 'Notebook'}
              </span>
              <h4 
                title={title}
                className="font-bold text-slate-100 text-sm leading-snug group-hover:text-indigo-300 transition-colors truncate break-all"
              >
                {title}
              </h4>
            </div>
          </div>
          <div className="shrink-0">
            {getStatusBadge(status)}
          </div>
        </div>

        {/* Real Processing Status Banner */}
        <div className="mt-3.5 p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-1 text-xs min-w-0 overflow-hidden">
          <div className="flex items-center space-x-2 text-emerald-400 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0"></span>
            <span className="truncate">OCR text extracted</span>
          </div>
          <div className="flex items-center space-x-2 text-slate-300 min-w-0">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0"></span>
            <span className="truncate">{statusDetail || `${pageCount} pages indexed for chunking`}</span>
          </div>
          {chunkCount !== undefined && (
            <div className="flex items-center space-x-2 text-slate-400 text-[11px] min-w-0">
              <span className="w-1.5 h-1.5 rounded-full bg-slate-500 shrink-0"></span>
              <span className="truncate">{chunkCount} semantic knowledge chunks created</span>
            </div>
          )}
        </div>

        {/* Info Meta Row */}
        <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center space-x-1.5">
            <span>📄</span>
            <span>{pageCount} pages</span>
          </div>
          <div className="flex items-center space-x-1 text-slate-500">
            <span>🕒</span>
            <span>{lastUpdated}</span>
          </div>
        </div>
      </div>

      {/* Card Action Options */}
      <div className="mt-4 flex items-center gap-2">
        <button
          onClick={() => onPreview && onPreview(doc)}
          className="flex-1 py-1.5 rounded-lg bg-slate-900 hover:bg-indigo-600/20 hover:text-indigo-300 text-slate-300 border border-slate-800 text-xs font-medium transition-all text-center cursor-pointer"
        >
          Preview
        </button>
        <button className="py-1.5 px-3 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 text-xs font-medium transition-all">
          •••
        </button>
      </div>
    </div>
  );
}


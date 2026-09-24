'use client';

import { useState, useRef } from 'react';

export default function ResumeUpload({ onUploadSuccess, onSelectAction }) {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle'); // idle | uploading | processing | success | error
  const [errorMessage, setErrorMessage] = useState('');
  const [uploadResult, setUploadResult] = useState(null);
  const fileInputRef = useRef(null);

  const API_BASE = 'http://127.0.0.1:8000';
  const MAX_SIZE_MB = 150;

  const validateAndSetFile = (selectedFile) => {
    if (!selectedFile) return;

    if (!selectedFile.name.toLowerCase().endsWith('.pdf')) {
      setStatus('error');
      setErrorMessage('Invalid file type. Only PDF documents (.pdf) are allowed.');
      return;
    }

    if (selectedFile.size > MAX_SIZE_MB * 1024 * 1024) {
      setStatus('error');
      setErrorMessage(`File size exceeds maximum limit of ${MAX_SIZE_MB} MB.`);
      return;
    }

    setFile(selectedFile);
    setStatus('idle');
    setErrorMessage('');
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setStatus('uploading');
    setErrorMessage('');

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('document_type', 'RESUME');

      setStatus('processing');

      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      setUploadResult(data);
      setStatus('success');
      if (onUploadSuccess) {
        onUploadSuccess(data);
      }
    } catch (err) {
      setStatus('error');
      setErrorMessage(err.message || 'Failed to upload and process resume. Please try again.');
    }
  };

  return (
    <div className="w-full bg-[#111827]/80 backdrop-blur-md rounded-2xl border border-slate-800 p-6 shadow-xl">
      <div className="mb-6">
        <h2 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
          <span>📄</span> Resume Intelligence
        </h2>
        <p className="text-slate-400 text-sm mt-1">
          Upload your resume and practice interview questions based on what you actually wrote.
        </p>
      </div>

      {/* Upload Zone */}
      {status !== 'success' && (
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
            dragActive
              ? 'border-indigo-500 bg-indigo-500/10'
              : 'border-slate-700 hover:border-slate-500 bg-slate-900/40'
          }`}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={handleChange}
          />
          <div className="w-14 h-14 mx-auto rounded-full bg-indigo-600/20 text-indigo-400 flex items-center justify-center text-2xl mb-3 border border-indigo-500/30">
            📄
          </div>
          <p className="text-white font-semibold text-base">
            {file ? file.name : 'Drag & Drop your Resume PDF here'}
          </p>
          <p className="text-slate-400 text-xs mt-1">
            PDF files only up to {MAX_SIZE_MB} MB
          </p>

          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
            className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-colors"
          >
            Choose PDF File
          </button>
        </div>
      )}

      {/* Status Indicators */}
      {status === 'uploading' && (
        <div className="mt-4 p-4 rounded-xl bg-indigo-950/40 border border-indigo-800/50 text-indigo-200 text-sm flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin"></div>
          <span>Uploading resume...</span>
        </div>
      )}

      {status === 'processing' && (
        <div className="mt-4 p-4 rounded-xl bg-purple-950/40 border border-purple-800/50 text-purple-200 text-sm flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-purple-400 border-t-transparent rounded-full animate-spin"></div>
          <span>Parsing resume text & building embeddings...</span>
        </div>
      )}

      {status === 'error' && (
        <div className="mt-4 p-4 rounded-xl bg-red-950/40 border border-red-800/50 text-red-200 text-sm">
          <p className="font-semibold flex items-center gap-1">
            <span>⚠️</span> Upload Error:
          </p>
          <p className="mt-1 text-xs opacity-90">{errorMessage}</p>
        </div>
      )}

      {/* Upload Action Button */}
      {file && status !== 'uploading' && status !== 'processing' && status !== 'success' && (
        <div className="mt-4 flex justify-end">
          <button
            onClick={handleUpload}
            className="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-sm rounded-xl shadow-lg shadow-indigo-500/20 transition-all"
          >
            Upload Resume & Process
          </button>
        </div>
      )}

      {/* Upload Result / Success State */}
      {status === 'success' && uploadResult && (
        <div className="mt-2 space-y-4">
          <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-800/50 text-emerald-200 flex items-center justify-between gap-3 min-w-0">
            <div className="flex items-center gap-3 min-w-0 flex-1">
              <span className="text-2xl shrink-0">✅</span>
              <div className="min-w-0 flex-1">
                <p title={uploadResult.original_filename || uploadResult.filename || file?.name} className="font-bold text-sm text-white truncate break-all">
                  {uploadResult.original_filename || uploadResult.filename || file?.name}
                </p>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400 mt-1">
                  <span>Pages: <strong className="text-slate-200">{uploadResult.page_count}</strong></span>
                  <span>Chunks: <strong className="text-slate-200">{uploadResult.chunk_count || 0}</strong></span>
                  <span>Status: <strong className="text-emerald-400">{uploadResult.processing_status}</strong></span>
                </div>
              </div>
            </div>
            <button
              onClick={() => {
                setStatus('idle');
                setFile(null);
                setUploadResult(null);
              }}
              className="text-xs text-slate-400 hover:text-white underline shrink-0"
            >
              Upload another
            </button>
          </div>

          {/* OCR Warning if applicable */}
          {uploadResult.processing_status === 'OCR_REQUIRED' && (
            <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-800/50 text-amber-200 text-xs">
              ⚠️ Your resume is an image-only PDF and needs OCR before interview features can use it.
            </div>
          )}

          {/* Next Steps / Quick Actions */}
          <div className="pt-2">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
              Available Resume Actions
            </p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2.5">
              <button
                onClick={() => onSelectAction && onSelectAction('analyze', uploadResult.document_id)}
                className="p-3 bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 rounded-xl text-left transition-all group"
              >
                <span className="text-lg block mb-1">🔍</span>
                <span className="text-xs font-bold text-white group-hover:text-indigo-400">Analyze Resume</span>
              </button>

              <button
                onClick={() => onSelectAction && onSelectAction('viva', uploadResult.document_id)}
                className="p-3 bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 rounded-xl text-left transition-all group"
              >
                <span className="text-lg block mb-1">🎤</span>
                <span className="text-xs font-bold text-white group-hover:text-purple-400">Start Viva</span>
              </button>

              <button
                onClick={() => onSelectAction && onSelectAction('hr', uploadResult.document_id)}
                className="p-3 bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 rounded-xl text-left transition-all group"
              >
                <span className="text-lg block mb-1">💼</span>
                <span className="text-xs font-bold text-white group-hover:text-blue-400">HR Interview</span>
              </button>

              <button
                onClick={() => onSelectAction && onSelectAction('technical', uploadResult.document_id)}
                className="p-3 bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 rounded-xl text-left transition-all group"
              >
                <span className="text-lg block mb-1">⚡</span>
                <span className="text-xs font-bold text-white group-hover:text-amber-400">Technical Interview</span>
              </button>

              <button
                onClick={() => onSelectAction && onSelectAction('project', uploadResult.document_id)}
                className="p-3 bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 rounded-xl text-left transition-all group"
              >
                <span className="text-lg block mb-1">🛡️</span>
                <span className="text-xs font-bold text-white group-hover:text-pink-400">Project Defense</span>
              </button>

              <button
                onClick={() => onSelectAction && onSelectAction('coding', uploadResult.document_id)}
                className="p-3 bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 rounded-xl text-left transition-all group"
              >
                <span className="text-lg block mb-1">💻</span>
                <span className="text-xs font-bold text-white group-hover:text-emerald-400">Coding Interview</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

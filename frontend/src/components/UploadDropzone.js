'use client';

import { useState, useRef } from 'react';

export default function UploadDropzone({ onUploadSuccess, fileInputRef: externalRef }) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [status, setStatus] = useState('idle'); // 'idle' | 'selected' | 'uploading' | 'success' | 'error'
  const [docType, setDocType] = useState('NOTES'); // 'NOTES' | 'RESUME' | 'GENERAL_PDF'
  const [errorMessage, setErrorMessage] = useState('');
  const [uploadResult, setUploadResult] = useState(null);

  const internalRef = useRef(null);
  const fileInputRef = externalRef || internalRef;

  const MAX_SIZE_BYTES = 150 * 1024 * 1024; // 150MB

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const validateFile = (file) => {
    if (!file) return 'No file selected.';
    const isPdfExt = file.name.toLowerCase().endsWith('.pdf');
    if (!isPdfExt) {
      return 'Invalid file type. Please select a PDF file (.pdf).';
    }
    if (file.size > MAX_SIZE_BYTES) {
      return `File size (${formatBytes(file.size)}) exceeds the maximum limit of 150 MB.`;
    }
    return null;
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const error = validateFile(file);
    if (error) {
      setStatus('error');
      setErrorMessage(error);
      setSelectedFile(null);
    } else {
      setSelectedFile(file);
      setStatus('selected');
      setErrorMessage('');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    if (status !== 'uploading') setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (status === 'uploading') return;

    const file = e.dataTransfer.files?.[0];
    if (!file) return;

    const error = validateFile(file);
    if (error) {
      setStatus('error');
      setErrorMessage(error);
      setSelectedFile(null);
    } else {
      setSelectedFile(file);
      setStatus('selected');
      setErrorMessage('');
    }
  };

  const triggerFilePicker = () => {
    if (status === 'uploading') return;
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
      fileInputRef.current.click();
    }
  };

  const executeUpload = async () => {
    if (!selectedFile) return;

    setStatus('uploading');
    setErrorMessage('');

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('document_type', docType);

    try {
      const response = await fetch('http://127.0.0.1:8000/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `Upload failed with status code ${response.status}`);
      }

      setUploadResult(data);
      setStatus('success');

      if (onUploadSuccess) {
        onUploadSuccess(data);
      }
    } catch (err) {
      setStatus('error');
      if (err.message.includes('Failed to fetch') || err.name === 'TypeError') {
        setErrorMessage('Cannot connect to backend server at http://127.0.0.1:8000. Ensure FastAPI is running.');
      } else {
        setErrorMessage(err.message || 'An unexpected error occurred during upload.');
      }
    }
  };

  const resetUploadState = () => {
    setSelectedFile(null);
    setStatus('idle');
    setErrorMessage('');
    setUploadResult(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="space-y-4">
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        accept=".pdf,application/pdf"
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Main Container */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={status === 'idle' ? triggerFilePicker : undefined}
        className={`relative overflow-hidden rounded-2xl border-2 transition-all ${
          isDragging
            ? 'border-indigo-500 bg-indigo-500/10 shadow-lg shadow-indigo-500/20 scale-[1.01]'
            : status === 'success'
            ? 'border-emerald-500/40 bg-emerald-950/20'
            : status === 'error'
            ? 'border-rose-500/40 bg-rose-950/20'
            : status === 'selected' || status === 'uploading'
            ? 'border-indigo-500/50 bg-slate-900/90'
            : 'border-slate-800 hover:border-slate-700 bg-slate-900/50 hover:bg-slate-900/80 cursor-pointer'
        } p-6 md:p-8 text-center`}
      >
        <div className="relative z-10 flex flex-col items-center justify-center space-y-4">
          {/* IDLE STATE */}
          {status === 'idle' && (
            <>
              <div className="w-14 h-14 rounded-2xl bg-indigo-600/10 border border-indigo-500/30 flex items-center justify-center text-2xl text-indigo-400 shadow-md">
                ☁️
              </div>
              <div>
                <p className="text-base font-bold text-white">Drop your PDF here</p>
                <p className="text-xs text-slate-400 mt-1">
                  or <span className="text-indigo-400 font-semibold underline underline-offset-2">choose a file</span> from your computer
                </p>
              </div>
              <div className="flex items-center space-x-3 text-[11px] text-slate-500 pt-1">
                <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700/60 font-mono">
                  PDF format
                </span>
                <span>•</span>
                <span>Max 150MB</span>
                <span>•</span>
                <span className="text-indigo-400/90 font-medium">FastAPI Endpoint Connected</span>
              </div>
            </>
          )}

          {/* SELECTED STATE */}
          {status === 'selected' && selectedFile && (
            <div className="w-full max-w-md space-y-4">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-xl text-indigo-400 mx-auto">
                📄
              </div>
              <div>
                <p className="text-sm font-bold text-white truncate px-2">{selectedFile.name}</p>
                <p className="text-xs text-slate-400 mt-0.5">{formatBytes(selectedFile.size)}</p>
              </div>

              {/* Document Type Selector */}
              <div className="flex flex-col items-center space-y-1.5 pt-1">
                <span className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider">Select Document Type:</span>
                <div className="flex items-center gap-2 bg-slate-950 p-1 rounded-xl border border-slate-800">
                  {[
                    { id: 'NOTES', label: '📘 Notes' },
                    { id: 'RESUME', label: '📄 Resume' },
                    { id: 'GENERAL_PDF', label: '📂 General PDF' },
                  ].map((t) => (
                    <button
                      key={t.id}
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setDocType(t.id);
                      }}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                        docType === t.id
                          ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                          : 'text-slate-400 hover:text-slate-200 bg-slate-900'
                      }`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex items-center justify-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    executeUpload();
                  }}
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-md shadow-indigo-600/30 transition-all"
                >
                  Upload Now 🚀
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    resetUploadState();
                  }}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs transition-all"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* UPLOADING STATE */}
          {status === 'uploading' && selectedFile && (
            <div className="w-full max-w-md space-y-4 py-2">
              <div className="w-10 h-10 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <div>
                <p className="text-sm font-bold text-white">Uploading PDF to FastAPI Backend...</p>
                <p className="text-xs text-slate-400 mt-1 truncate">{selectedFile.name}</p>
              </div>
              {/* Progress bar visual */}
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden border border-slate-700/50">
                <div className="bg-gradient-to-r from-indigo-500 to-purple-500 h-2 rounded-full animate-pulse w-3/4" />
              </div>
            </div>
          )}

          {/* SUCCESS STATE */}
          {status === 'success' && uploadResult && (
            <div className="w-full max-w-md space-y-3 py-2">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center text-xl mx-auto ${
                uploadResult.processing_status === 'OCR_REQUIRED'
                  ? 'bg-amber-500/20 border border-amber-500/40 text-amber-400'
                  : 'bg-emerald-500/20 border border-emerald-500/40 text-emerald-400'
              }`}>
                {uploadResult.processing_status === 'OCR_REQUIRED' ? '⚠️' : '✓'}
              </div>
              <div>
                <span className={`inline-block text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border mb-1 ${
                  uploadResult.processing_status === 'OCR_REQUIRED'
                    ? 'text-amber-400 bg-amber-500/10 border-amber-500/30'
                    : 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
                }`}>
                  {uploadResult.processing_status === 'OCR_REQUIRED' ? 'OCR Required' : 'Ingestion Ready'}
                </span>
                <p className="text-base font-bold text-white">{uploadResult.original_filename}</p>
                
                {uploadResult.processing_status === 'OCR_REQUIRED' ? (
                  <div className="mt-2.5 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-300 text-left space-y-1">
                    <p className="font-semibold">⚠️ No Usable Text Layer Found</p>
                    <p className="text-[11px] text-amber-400/90 leading-relaxed">
                      This PDF does not contain a usable text layer and requires OCR before it can be indexed in RAG search.
                    </p>
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 mt-1">
                    Stored as: <span className="font-mono text-slate-300">{uploadResult.stored_filename}</span> ({formatBytes(uploadResult.file_size)})
                  </p>
                )}

                {uploadResult.page_count !== undefined && (
                  <div className="mt-2 p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300 space-y-1 font-mono">
                    <p>Doc ID: <span className="text-indigo-300">{uploadResult.document_id}</span></p>
                    <p>Pages: <span className="text-emerald-400 font-bold">{uploadResult.page_count}</span> | Chunks: <span className="text-indigo-400 font-bold">{uploadResult.chunk_count || 0}</span> | Text Layer: <span className={uploadResult.has_text_layer ? "text-emerald-400 font-bold" : "text-amber-400 font-bold"}>{uploadResult.has_text_layer ? "Yes" : "No"}</span></p>
                  </div>
                )}
              </div>
              <div className="pt-2">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    resetUploadState();
                  }}
                  className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-xs border border-slate-700 transition-all"
                >
                  Upload Another Note ➕
                </button>
              </div>
            </div>
          )}

          {/* ERROR STATE */}
          {status === 'error' && (
            <div className="w-full max-w-md space-y-3 py-2">
              <div className="w-12 h-12 rounded-full bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-xl text-rose-400 mx-auto">
                ⚠️
              </div>
              <div>
                <span className="inline-block text-[10px] font-bold uppercase tracking-wider text-rose-400 bg-rose-500/10 px-2.5 py-0.5 rounded-full border border-rose-500/30 mb-1">
                  Upload Failed
                </span>
                <p className="text-sm font-semibold text-rose-200 mt-1">{errorMessage}</p>
              </div>
              <div className="pt-2 flex justify-center gap-3">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    triggerFilePicker();
                  }}
                  className="px-4 py-2 rounded-xl bg-rose-600/80 hover:bg-rose-500 text-white font-medium text-xs transition-all"
                >
                  Try Again
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    resetUploadState();
                  }}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs transition-all"
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

'use client';

import { useState, useRef, useEffect, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import HeroSection from '../components/HeroSection';
import StatCard from '../components/StatCard';
import DocumentCard from '../components/DocumentCard';
import UploadDropzone from '../components/UploadDropzone';
import AskSection from '../components/AskSection';
import DocumentPreviewModal from '../components/DocumentPreviewModal';
import ResumeSection from '../components/ResumeSection';
import VivaSection from '../components/VivaSection';
import InterviewSection from '../components/InterviewSection';

function DashboardContent() {
  const searchParams = useSearchParams();
  const tabParam = searchParams.get('tab');

  const [activeTab, setActiveTab] = useState(tabParam || 'dashboard');
  const [activeCategory, setActiveCategory] = useState('all');
  const [documents, setDocuments] = useState([]);
  const [previewDoc, setPreviewDoc] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (tabParam) {
      setActiveTab(tabParam);
    }
  }, [tabParam]);

  const loadDocuments = useCallback(() => {
    fetch('http://127.0.0.1:8000/documents')
      .then((res) => res.json())
      .then((data) => {
        if (data && data.documents && data.documents.length > 0) {
          const formatted = data.documents.map((d) => ({
            id: d.document_id,
            title: d.original_filename || d.filename || d.stored_filename || 'PDF Document',
            originalFilename: d.original_filename || d.filename,
            pageCount: d.page_count || 0,
            chunkCount: d.chunk_count || 0,
            lastUpdated: d.updated_at ? new Date(d.updated_at).toLocaleTimeString() : 'READY',
            status: d.processing_status || 'READY',
            statusDetail: d.processing_error || `${d.page_count || 0} pages indexed`,
            category: d.document_id === 'b8f2cb48' ? 'Handwritten Notes' : 'Uploaded PDF',
            icon: d.document_id === 'b8f2cb48' ? '🧠' : '📄',
          }));
          setDocuments(formatted);
        }
      })
      .catch((err) => {
        console.log('Backend sync warning:', err);
      });
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const defaultDoc = {
    id: 'b8f2cb48',
    title: 'AI & Python Notes',
    pageCount: 167,
    chunkCount: 106,
    lastUpdated: 'READY',
    status: 'READY',
    statusDetail: '167 pages indexed for chunking',
    category: 'Handwritten Notes',
    icon: '🧠',
  };

  const displayDocs = documents.length > 0 ? documents : [defaultDoc];

  const totalPages = displayDocs.reduce((acc, d) => acc + (d.pageCount || 0), 0);
  const totalChunks = displayDocs.reduce((acc, d) => acc + (d.chunkCount || 0), 0);
  const totalDocs = displayDocs.length;

  const stats = [
    { label: 'Documents', value: totalDocs.toString(), icon: '📚', badge: 'Multi-Doc Corpus' },
    { label: 'Pages', value: totalPages.toString(), icon: '📄', badge: 'Total Indexed' },
    { label: 'Knowledge Chunks', value: totalChunks.toString(), icon: '🧩', badge: `${totalChunks} Chunks` },
    { label: 'RAG Mode', value: 'Step 13', icon: '💬', badge: 'Generic Ingestion' },
  ];

  const handleUploadSuccess = () => {
    loadDocuments();
  };

  const allDocuments = displayDocs;

  return (
    <div className="flex flex-col lg:flex-row min-h-screen bg-[#080c14] text-slate-100">
      {/* Sidebar Navigation */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <main className="flex-1 p-4 sm:p-6 md:p-8 space-y-8 max-w-7xl mx-auto w-full overflow-hidden">
        {/* Top Greeting & Search Header */}
        <Header />

        {/* Tab-based View Switching */}
        {activeTab === 'dashboard' && (
          <>
            <HeroSection
              onUploadClick={() => {
                const uploadEl = document.getElementById('upload-section');
                if (uploadEl) uploadEl.scrollIntoView({ behavior: 'smooth' });
                if (fileInputRef.current) {
                  fileInputRef.current.value = '';
                  fileInputRef.current.click();
                }
              }}
              onChatClick={() => {
                const askEl = document.getElementById('ask-section');
                if (askEl) askEl.scrollIntoView({ behavior: 'smooth' });
              }}
            />

            <AskSection />

            <section className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
                  <span>Overview Metrics</span>
                  {documents.length <= 1 && (
                    <span className="text-[10px] bg-slate-800 text-slate-400 font-semibold px-2 py-0.5 rounded-full border border-slate-700/60">
                      Live Corpus
                    </span>
                  )}
                </h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {stats.map((stat, idx) => (
                  <StatCard
                    key={idx}
                    label={stat.label}
                    value={stat.value}
                    icon={stat.icon}
                    badge={stat.badge}
                  />
                ))}
              </div>
            </section>

            <section id="upload-section" className="space-y-4 pt-2">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                  <span>Upload Handwritten Notes or Resumes</span>
                  <span className="text-xs text-indigo-400 font-normal">PDF Supported</span>
                </h3>
              </div>
              <UploadDropzone
                fileInputRef={fileInputRef}
                onUploadSuccess={handleUploadSuccess}
              />
            </section>

            <section className="space-y-4 pt-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-800/60">
                <div>
                  <h3 className="text-lg font-bold text-white">Recent Documents</h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {documents.length > 0
                      ? `${documents.length} PDF document(s) registered in repository`
                      : 'Sample preview cards for your AI knowledge repository'}
                  </p>
                </div>

                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
                  {['all', 'ready', 'pending'].map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setActiveCategory(cat)}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold capitalize transition-all whitespace-nowrap ${
                        activeCategory === cat
                          ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                          : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
                      }`}
                    >
                      {cat === 'all' ? 'All Notes' : cat}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {allDocuments
                  .filter((doc) => {
                    if (activeCategory === 'ready') return doc.status === 'READY' || doc.status === 'Ready' || doc.status === 'indexed_and_chunked';
                    if (activeCategory === 'pending') return doc.status === 'OCR_REQUIRED' || doc.status === 'FAILED';
                    return true;
                  })
                  .map((doc) => (
                    <DocumentCard key={doc.id} doc={doc} onPreview={(d) => setPreviewDoc(d)} />
                  ))}
              </div>
            </section>
          </>
        )}

        {activeTab === 'documents' && (
          <div className="space-y-6">
            <section id="upload-section" className="space-y-4 pt-2">
              <h3 className="text-lg font-bold text-white">Upload New PDF Document</h3>
              <UploadDropzone
                fileInputRef={fileInputRef}
                onUploadSuccess={handleUploadSuccess}
              />
            </section>

            <section className="space-y-4 pt-4">
              <h3 className="text-lg font-bold text-white">All Repository Documents ({allDocuments.length})</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {allDocuments.map((doc) => (
                  <DocumentCard key={doc.id} doc={doc} onPreview={(d) => setPreviewDoc(d)} />
                ))}
              </div>
            </section>
          </div>
        )}

        {activeTab === 'ask' && (
          <div className="space-y-6">
            <AskSection />
          </div>
        )}

        {activeTab === 'resume' && (
          <ResumeSection
            onStartViva={() => setActiveTab('viva')}
            onStartInterview={() => setActiveTab('interview')}
          />
        )}

        {activeTab === 'viva' && (
          <VivaSection defaultDocumentId={displayDocs[0]?.id} />
        )}

        {activeTab === 'interview' && (
          <InterviewSection defaultDocumentId={displayDocs[0]?.id} />
        )}

        {activeTab === 'settings' && (
          <div className="bg-[#111827]/80 backdrop-blur-md rounded-2xl border border-slate-800 p-6 shadow-xl space-y-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span>⚙️</span> System & Provider Settings
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                <p className="font-bold text-indigo-300">LLM Provider Chain Configuration</p>
                <p className="text-slate-300">Primary Provider: <strong>Groq (qwen3.8-27b)</strong></p>
                <p className="text-slate-400">Fallbacks: OpenRouter → NVIDIA → Gemini</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                <p className="font-bold text-emerald-300">Vector Search & Storage</p>
                <p className="text-slate-300">FAISS Index: <strong>sentence-transformers/all-MiniLM-L6-v2</strong></p>
                <p className="text-slate-400">Lexical Search: BM25 Okapi Hybrid Retrieval</p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Document Preview Modal */}
      <DocumentPreviewModal
        doc={previewDoc}
        isOpen={!!previewDoc}
        onClose={() => setPreviewDoc(null)}
      />
    </div>
  );
}

export default function Dashboard() {
  return (
    <Suspense fallback={<div className="p-8 text-white">Loading Dashboard...</div>}>
      <DashboardContent />
    </Suspense>
  );
}

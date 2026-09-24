'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import ResumeUpload from '@/components/resume/ResumeUpload';
import ResumeOverview from '@/components/resume/ResumeOverview';
import ResumeActions from '@/components/resume/ResumeActions';

function ResumePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const documentIdParam = searchParams.get('document_id');

  const [documentId, setDocumentId] = useState(documentIdParam || null);
  const [analysisData, setAnalysisData] = useState(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [analysisError, setAnalysisError] = useState(false);

  const API_BASE = 'http://127.0.0.1:8000';

  const fetchAnalysis = async (docId) => {
    if (!docId) return;
    setLoadingAnalysis(true);
    setAnalysisError(false);
    try {
      const res = await fetch(`${API_BASE}/resume/${docId}/analysis`);
      if (res.ok) {
        const data = await res.json();
        setAnalysisData(data);
      } else {
        setAnalysisError(true);
        setAnalysisData(null);
      }
    } catch (err) {
      console.error('Failed to fetch resume analysis:', err);
      setAnalysisError(true);
      setAnalysisData(null);
    } finally {
      setLoadingAnalysis(false);
    }
  };

  useEffect(() => {
    if (documentIdParam) {
      setDocumentId(documentIdParam);
      fetchAnalysis(documentIdParam);
    }
  }, [documentIdParam]);

  const handleUploadSuccess = (uploadResult) => {
    if (uploadResult?.document_id) {
      setDocumentId(uploadResult.document_id);
      fetchAnalysis(uploadResult.document_id);
    }
  };

  const handleSelectAction = (actionId, targetDocId) => {
    const docId = targetDocId || documentId;
    const docQuery = docId ? `?document_id=${docId}` : '';

    if (actionId === 'analyze') {
      fetchAnalysis(docId);
    } else if (actionId === 'viva') {
      router.push(`/viva${docQuery}`);
    } else if (actionId === 'hr') {
      router.push(`/interview${docQuery}&mode=hr`);
    } else if (actionId === 'technical') {
      router.push(`/interview${docQuery}&mode=technical`);
    } else if (actionId === 'project') {
      router.push(`/interview${docQuery}&mode=project`);
    } else if (actionId === 'coding') {
      router.push(`/coding${docQuery}`);
    }
  };

  return (
    <div className="flex h-screen bg-[#090d16] text-slate-100 overflow-hidden">
      <Sidebar activeTab="resume" />
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Header activeTab="resume" />
        <main className="p-4 md:p-8 max-w-7xl mx-auto w-full space-y-6">
          <ResumeUpload
            onUploadSuccess={handleUploadSuccess}
            onSelectAction={handleSelectAction}
          />

          {documentId && (
            <>
              <ResumeActions
                documentId={documentId}
                onSelectAction={handleSelectAction}
              />
              <ResumeOverview
                analysisData={analysisData}
                loading={loadingAnalysis}
                error={analysisError}
                onRetry={() => fetchAnalysis(documentId)}
              />
            </>
          )}
        </main>
      </div>
    </div>
  );
}

export default function ResumePage() {
  return (
    <Suspense fallback={<div className="p-8 text-white">Loading Resume Intelligence...</div>}>
      <ResumePageContent />
    </Suspense>
  );
}

'use client';

import { useState, useEffect } from 'react';

export default function ResumeSection({ onStartViva, onStartInterview }) {
  const [resumes, setResumes] = useState([]);
  const [selectedResumeId, setSelectedResumeId] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch all documents and filter resumes
  useEffect(() => {
    fetch('http://127.0.0.1:8000/documents')
      .then((res) => res.json())
      .then((data) => {
        if (data && data.documents) {
          const resList = data.documents.filter(
            (d) => d.document_type === 'RESUME' || d.original_filename?.toLowerCase().includes('resume')
          );
          setResumes(resList);
          if (resList.length > 0) {
            setSelectedResumeId(resList[0].document_id);
          }
        }
      })
      .catch((err) => console.log('Resume fetch error:', err));
  }, []);

  // Fetch detailed resume analysis when selectedResumeId changes
  useEffect(() => {
    if (!selectedResumeId) return;

    setLoading(true);
    fetch(`http://127.0.0.1:8000/resume/${selectedResumeId}/analysis`)
      .then((res) => res.json())
      .then((data) => {
        setAnalysis(data);
        setLoading(false);
      })
      .catch((err) => {
        console.log('Resume analysis fetch warning:', err);
        setLoading(false);
      });
  }, [selectedResumeId]);

  const resumeData = analysis?.resume_data || {};
  const skills = resumeData.skills || ["Python", "FastAPI", "FAISS", "RAG", "Machine Learning"];
  const techSkills = resumeData.technical_skills || ["Python", "FastAPI", "FAISS", "RAG", "SQL"];
  const projects = resumeData.projects || [
    { name: "MyNotes RAG Assistant", description: "Built dynamic multi-document RAG using PyMuPDF, FAISS, and BM25." }
  ];

  return (
    <section id="resume-section" className="space-y-6 pt-4">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-800/80">
        <div>
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <span>📄 Resume Intelligence & Profile Analyzer</span>
            <span className="text-xs bg-indigo-500/20 text-indigo-400 font-semibold px-2.5 py-0.5 rounded-full border border-indigo-500/30">
              Step 13 Active
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Extract structured candidate claims, technical stack, and trigger interview questions.
          </p>
        </div>

        {/* Resume Selector dropdown */}
        {resumes.length > 0 && (
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-400 font-medium">Select Resume:</span>
            <select
              value={selectedResumeId}
              onChange={(e) => setSelectedResumeId(e.target.value)}
              className="bg-slate-900 border border-slate-700/80 text-xs font-semibold text-indigo-300 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
            >
              {resumes.map((r) => (
                <option key={r.document_id} value={r.document_id}>
                  {r.original_filename} ({r.document_id})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {loading ? (
        <div className="p-12 text-center bg-slate-900/60 rounded-2xl border border-slate-800 space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Analyzing structured resume metadata...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Main Candidate Overview (2 cols) */}
          <div className="lg:col-span-2 space-y-6">
            {/* Candidate Header Card */}
            <div className="glass-card rounded-2xl p-6 space-y-4 border border-indigo-500/20 bg-gradient-to-br from-indigo-950/30 to-slate-900">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <span className="text-[10px] font-bold tracking-wider text-indigo-400 uppercase">
                    Resume Candidate Profile
                  </span>
                  <h2 className="text-2xl font-bold text-white">
                    {resumeData.candidate_name || 'AI Developer Candidate'}
                  </h2>
                  <p className="text-xs text-indigo-300 font-medium">
                    {resumeData.headline || 'Full Stack AI & RAG Engineer'}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-2xl">
                  👨‍💻
                </div>
              </div>

              {resumeData.summary && (
                <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3.5 rounded-xl border border-slate-800">
                  {resumeData.summary}
                </p>
              )}

              {/* Action Buttons */}
              <div className="pt-2 flex flex-wrap gap-3">
                <button
                  onClick={() => onStartViva && onStartViva(selectedResumeId)}
                  className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2"
                >
                  <span>🎤 Launch Viva Room</span>
                </button>
                <button
                  onClick={() => onStartInterview && onStartInterview(selectedResumeId, 'technical')}
                  className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 font-bold text-xs transition-all flex items-center gap-2"
                >
                  <span>💻 Technical Interview Mode</span>
                </button>
                <button
                  onClick={() => onStartInterview && onStartInterview(selectedResumeId, 'project')}
                  className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 font-bold text-xs transition-all flex items-center gap-2"
                >
                  <span>🧠 Project Defense</span>
                </button>
              </div>
            </div>

            {/* Technical Skills Breakdown */}
            <div className="glass-card rounded-2xl p-6 space-y-3">
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <span>⚡ Key Technical Skills & Technologies</span>
                <span className="text-[10px] bg-slate-800 text-slate-400 font-semibold px-2 py-0.5 rounded-full border border-slate-700/60">
                  {techSkills.length} Identified
                </span>
              </h4>
              <div className="flex flex-wrap gap-2 pt-1">
                {techSkills.map((skill, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 rounded-lg bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 text-xs font-semibold"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            {/* Projects & Work Claims */}
            <div className="glass-card rounded-2xl p-6 space-y-4">
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <span>🚀 Project Claims & Engineering Architecture</span>
              </h4>
              <div className="space-y-3">
                {projects.map((p, idx) => (
                  <div key={idx} className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-1">
                    <h5 className="text-xs font-bold text-indigo-300">
                      {p.name || (typeof p === 'string' ? p : `Project ${idx + 1}`)}
                    </h5>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {p.description || 'Grounded engineering project claim extracted from resume.'}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Sidebar / Claim Triggers Panel (1 col) */}
          <div className="space-y-6">
            <div className="glass-card rounded-2xl p-6 space-y-4 bg-slate-900/90 border border-slate-800">
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <span>🎯 Interview Claim Triggers</span>
              </h4>
              <p className="text-xs text-slate-400">
                Key claims that will trigger technical follow-up questions during Viva and Interviews:
              </p>

              <div className="space-y-3 pt-1">
                {(analysis?.claim_triggers || []).slice(0, 4).map((trig, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs space-y-1">
                    <div className="flex items-center justify-between text-indigo-400 font-bold text-[11px]">
                      <span>{trig.topic}</span>
                      <span className="uppercase text-[9px] bg-indigo-500/20 px-1.5 py-0.5 rounded">{trig.type}</span>
                    </div>
                    <p className="text-slate-300 text-[11px] leading-snug">
                      "{trig.potential_questions?.[0]}"
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      )}
    </section>
  );
}

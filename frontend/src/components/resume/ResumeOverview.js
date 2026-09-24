'use client';

export default function ResumeOverview({ analysisData, loading, error, onRetry }) {
  if (loading) {
    return (
      <div className="w-full bg-[#111827]/80 backdrop-blur-md rounded-2xl border border-slate-800 p-6 shadow-xl space-y-6 animate-pulse">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
          <div className="space-y-2">
            <div className="h-6 w-56 bg-slate-800 rounded-lg"></div>
            <div className="h-4 w-40 bg-slate-800/60 rounded-lg"></div>
          </div>
          <div className="h-8 w-28 bg-slate-800 rounded-full"></div>
        </div>
        <div className="space-y-2">
          <div className="h-4 w-32 bg-slate-800 rounded"></div>
          <div className="h-16 w-full bg-slate-800/40 rounded-xl"></div>
        </div>
        <div className="space-y-2">
          <div className="h-4 w-36 bg-slate-800 rounded"></div>
          <div className="flex flex-wrap gap-2">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
              <div key={i} className="h-7 w-20 bg-slate-800/60 rounded-lg"></div>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-slate-800/40 rounded-xl p-4 space-y-2">
              <div className="h-4 w-28 bg-slate-800 rounded"></div>
              <div className="h-3 w-3/4 bg-slate-800/60 rounded"></div>
              <div className="h-3 w-1/2 bg-slate-800/60 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full bg-[#111827]/80 backdrop-blur-md rounded-2xl border border-red-900/50 p-8 text-center text-red-300 shadow-xl">
        <div className="w-12 h-12 mx-auto rounded-full bg-red-950/60 border border-red-800 flex items-center justify-center text-xl mb-3">
          ⚠️
        </div>
        <h3 className="text-lg font-bold text-white mb-1">Resume analysis could not be completed.</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto mb-5">
          We encountered an issue retrieving the structured resume details from the backend.
        </p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-5 py-2.5 bg-gradient-to-r from-red-600 to-indigo-600 hover:from-red-500 hover:to-indigo-500 text-white font-bold text-xs rounded-xl shadow-lg transition-all"
          >
            Retry Analysis
          </button>
        )}
      </div>
    );
  }

  if (!analysisData) {
    return null;
  }

  const data = analysisData.resume_data || analysisData || {};

  const renderSkills = (skills) => {
    if (!skills) {
      return <span className="text-slate-500 italic text-xs">Not found in resume</span>;
    }

    if (typeof skills === 'object' && !Array.isArray(skills)) {
      const categoryLabels = {
        programming: 'Languages',
        ai_ml: 'AI & Machine Learning',
        generative_ai: 'Generative AI & LLMs',
        libraries: 'Frameworks & Libraries',
        frontend: 'Frontend',
        backend: 'Backend',
        tools: 'Tools & Cloud',
      };

      const categoriesWithSkills = Object.entries(skills).filter(
        ([_, items]) => Array.isArray(items) && items.length > 0
      );

      if (categoriesWithSkills.length === 0) {
        return <span className="text-slate-500 italic text-xs">Not found in resume</span>;
      }

      return (
        <div className="space-y-3">
          {categoriesWithSkills.map(([catKey, items]) => (
            <div key={catKey}>
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                {categoryLabels[catKey] || catKey.replace('_', ' ')}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {items.map((skill, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 bg-indigo-950/60 border border-indigo-800/60 text-indigo-300 rounded-lg text-xs font-medium shadow-sm transition-all hover:bg-indigo-900/60"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      );
    }

    if (Array.isArray(skills)) {
      if (skills.length === 0) {
        return <span className="text-slate-500 italic text-xs">Not found in resume</span>;
      }
      return (
        <div className="flex flex-wrap gap-1.5">
          {skills.map((skill, idx) => (
            <span
              key={idx}
              className="px-2.5 py-1 bg-indigo-950/60 border border-indigo-800/60 text-indigo-300 rounded-lg text-xs font-medium shadow-sm"
            >
              {typeof skill === 'object' ? JSON.stringify(skill) : skill}
            </span>
          ))}
        </div>
      );
    }

    if (typeof skills === 'string') {
      const items = skills.split(/[,•|]/).map((s) => s.trim()).filter(Boolean);
      if (items.length === 0) {
        return <span className="text-slate-500 italic text-xs">Not found in resume</span>;
      }
      return (
        <div className="flex flex-wrap gap-1.5">
          {items.map((skill, idx) => (
            <span
              key={idx}
              className="px-2.5 py-1 bg-indigo-950/60 border border-indigo-800/60 text-indigo-300 rounded-lg text-xs font-medium shadow-sm"
            >
              {skill}
            </span>
          ))}
        </div>
      );
    }

    return <span className="text-slate-500 italic text-xs">Not found in resume</span>;
  };

  const renderSimpleList = (items, title, icon) => {
    if (!items || !Array.isArray(items) || items.length === 0) {
      return (
        <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800/80">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <span>{icon}</span> {title}
          </h4>
          <span className="text-slate-500 italic text-xs">Not found in resume</span>
        </div>
      );
    }

    return (
      <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800/80">
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
          <span>{icon}</span> {title}
        </h4>
        <ul className="space-y-2">
          {items.map((item, idx) => (
            <li key={idx} className="text-xs text-slate-200 flex items-start gap-2">
              <span className="text-indigo-400 mt-0.5">•</span>
              <span>{typeof item === 'string' ? item : item.title || item.name || JSON.stringify(item)}</span>
            </li>
          ))}
        </ul>
      </div>
    );
  };

  const renderExperienceList = (items) => {
    if (!items || !Array.isArray(items) || items.length === 0) {
      return (
        <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800/80">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <span>💼</span> Experience
          </h4>
          <span className="text-slate-500 italic text-xs">Not found in resume</span>
        </div>
      );
    }

    return (
      <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800/80">
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
          <span>💼</span> Experience
        </h4>
        <div className="space-y-4">
          {items.map((exp, idx) => (
            <div key={idx} className="border-b border-slate-800/80 pb-3 last:border-0 last:pb-0 space-y-1">
              <div className="flex flex-wrap justify-between items-start gap-1">
                <div>
                  <p className="text-sm font-bold text-white">
                    {exp.company || exp.role || 'Experience'}
                  </p>
                  {exp.company && exp.role && (
                    <p className="text-xs font-medium text-indigo-400">{exp.role}</p>
                  )}
                </div>
                {exp.duration && (
                  <span className="px-2 py-0.5 bg-slate-800/80 text-slate-300 rounded text-[10px] font-mono border border-slate-700/50">
                    {exp.duration}
                  </span>
                )}
              </div>
              {exp.project && (
                <p className="text-xs text-purple-300 font-medium">
                  <span className="text-slate-400">Project:</span> {exp.project}
                </p>
              )}
              {exp.highlights && Array.isArray(exp.highlights) && exp.highlights.length > 0 && (
                <ul className="mt-1.5 space-y-1">
                  {exp.highlights.map((h, hIdx) => (
                    <li key={hIdx} className="text-xs text-slate-300 flex items-start gap-1.5">
                      <span className="text-indigo-400 text-[10px] mt-0.5">•</span>
                      <span>{h}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderEducationList = (items) => {
    if (!items || !Array.isArray(items) || items.length === 0) {
      return (
        <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800/80">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <span>🎓</span> Education
          </h4>
          <span className="text-slate-500 italic text-xs">Not found in resume</span>
        </div>
      );
    }

    return (
      <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800/80">
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
          <span>🎓</span> Education
        </h4>
        <div className="space-y-3">
          {items.map((edu, idx) => (
            <div key={idx} className="border-b border-slate-800/80 pb-2.5 last:border-0 last:pb-0 space-y-1">
              <div className="flex flex-wrap justify-between items-start gap-1">
                <p className="text-sm font-bold text-white">
                  {edu.institution || edu.degree || 'Institution'}
                </p>
                {edu.year && (
                  <span className="text-[10px] font-mono text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700/40">
                    {edu.year}
                  </span>
                )}
              </div>
              {edu.degree && edu.institution && (
                <p className="text-xs text-indigo-300">{edu.degree}</p>
              )}
              {edu.gpa && (
                <span className="inline-block px-2 py-0.5 bg-emerald-950/60 text-emerald-300 border border-emerald-800/50 rounded text-[11px] font-medium mt-1">
                  {edu.gpa.includes('CGPA') || edu.gpa.includes('GPA') ? edu.gpa : `CGPA: ${edu.gpa}`}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderProjectsList = (items) => {
    if (!items || !Array.isArray(items) || items.length === 0) {
      return (
        <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800/80">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <span>🚀</span> Key Projects
          </h4>
          <span className="text-slate-500 italic text-xs">Not found in resume</span>
        </div>
      );
    }

    return (
      <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800/80">
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
          <span>🚀</span> Key Projects
        </h4>
        <div className="space-y-4">
          {items.map((proj, idx) => (
            <div key={idx} className="border-b border-slate-800/80 pb-3 last:border-0 last:pb-0 space-y-1.5">
              <p className="text-sm font-bold text-white">
                {typeof proj === 'string' ? proj : proj.title || proj.name || 'Project'}
              </p>
              {typeof proj === 'object' && proj.description && (
                <p className="text-xs text-slate-300 leading-relaxed">{proj.description}</p>
              )}
              {typeof proj === 'object' && proj.highlights && Array.isArray(proj.highlights) && proj.highlights.length > 0 && (
                <ul className="space-y-1 mt-1">
                  {proj.highlights.map((h, hIdx) => (
                    <li key={hIdx} className="text-xs text-slate-300 flex items-start gap-1.5">
                      <span className="text-purple-400 text-[10px] mt-0.5">•</span>
                      <span>{h}</span>
                    </li>
                  ))}
                </ul>
              )}
              {typeof proj === 'object' && proj.technologies && Array.isArray(proj.technologies) && proj.technologies.length > 0 && (
                <div className="flex flex-wrap gap-1 pt-1">
                  {proj.technologies.map((tech, tIdx) => (
                    <span key={tIdx} className="text-[10px] px-2 py-0.5 bg-indigo-950/60 text-indigo-300 rounded border border-indigo-800/40">
                      {tech}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="w-full bg-[#111827]/80 backdrop-blur-md rounded-2xl border border-slate-800 p-4 md:p-6 shadow-xl space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-xl md:text-2xl font-extrabold text-white flex items-center gap-2 tracking-tight">
            <span>👤</span> {data.candidate_name || 'Candidate Profile'}
          </h3>
          {data.location && (
            <div className="flex items-center gap-1.5 text-xs text-indigo-400 font-semibold mt-1">
              <span>📍</span>
              <span>{data.location}</span>
            </div>
          )}
        </div>
      </div>

      {/* Professional Summary */}
      <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800/80">
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <span>📝</span> Professional Summary
        </h4>
        {data.summary ? (
          <p className="text-xs md:text-sm text-slate-200 leading-relaxed">{data.summary}</p>
        ) : (
          <span className="text-slate-500 italic text-xs">Not found in resume</span>
        )}
      </div>

      {/* Skills */}
      <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800/80">
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
          <span>⚡</span> Technical & Core Skills
        </h4>
        {renderSkills(data.skills)}
      </div>

      {/* Grid for Experience, Education, Projects */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {renderExperienceList(data.experience)}
        {renderEducationList(data.education)}
        {renderProjectsList(data.projects)}
        {renderSimpleList(data.certifications, 'Certifications', '📜')}
      </div>

      {/* Achievements */}
      {renderSimpleList(data.achievements, 'Achievements & Awards', '🏆')}
    </div>
  );
}


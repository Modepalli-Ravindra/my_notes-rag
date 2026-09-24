from backend.services.ingestion.document_indexer import DocumentMetadataStore
from backend.services.resume.resume_parser import parse_and_store_resume


class ResumeAnalyzer:
    """
    Analyzes resume data and identifies technical skills, project claims,
    architecture choices, and technical follow-up triggers.
    """

    @classmethod
    def get_or_analyze_resume(cls, document_id: str) -> dict:
        meta = DocumentMetadataStore.load_metadata(document_id)
        if not meta:
            raise FileNotFoundError(f"Resume document '{document_id}' not found.")

        # Always delegate to parse_and_store_resume which handles caching, hashing, and versioning
        resume_data = parse_and_store_resume(document_id)

        # Generate claim triggers for technical interview questions
        triggers = []
        tech_skills = resume_data.get("technical_skills") or resume_data.get("all_skills") or []
        for tech in tech_skills:
            triggers.append({
                "type": "technical_skill",
                "topic": tech,
                "claim": f"Listed proficiency in {tech}",
                "potential_questions": [
                    f"What problem did you solve using {tech}?",
                    f"Can you explain the key concepts and internal mechanics of {tech}?"
                ]
            })

        projects = resume_data.get("projects", [])
        for proj in projects:
          proj_name = proj.get("title") or proj.get("name") if isinstance(proj, dict) else str(proj)
          if not proj_name:
            proj_name = "Project"
          triggers.append({
              "type": "project",
              "topic": proj_name,
              "claim": f"Project: {proj_name}",
              "potential_questions": [
                  f"Explain the architecture and technical design of {proj_name}.",
                  f"What were the biggest challenges you faced while building {proj_name}?"
              ]
          })

        skills_dict = resume_data.get("skills") if isinstance(resume_data.get("skills"), dict) else {}
        total_skills_count = len(tech_skills)

        analysis = {
            "document_id": document_id,
            "document_type": "RESUME",
            "candidate_name": resume_data.get("candidate_name"),
            "location": resume_data.get("location"),
            "summary": resume_data.get("summary"),
            "skills": skills_dict,
            "all_skills": tech_skills,
            "technical_skills": tech_skills,
            "education": resume_data.get("education", []),
            "experience": resume_data.get("experience", []),
            "projects": projects,
            "certifications": resume_data.get("certifications", []),
            "achievements": resume_data.get("achievements", []),
            "resume_data": resume_data,
            "claim_triggers": triggers,
            "total_skills": total_skills_count,
            "total_projects": len(projects),
            "total_experience": len(resume_data.get("experience", []))
        }

        return analysis

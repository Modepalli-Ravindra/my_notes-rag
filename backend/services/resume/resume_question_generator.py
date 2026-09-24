import json
import re
from backend.services.resume.resume_analyzer import ResumeAnalyzer
from backend.services.llm.provider_manager import LLMProviderManager


class ResumeQuestionGenerator:
    """
    Generates structured, resume-grounded interview questions for technical, HR, project defense, and viva modes.
    """

    @classmethod
    def generate_questions(
        cls,
        document_id: str,
        mode: str = "technical",
        role: str = None,
        difficulty: str = "medium",
        count: int = 5
    ) -> dict:
        analysis = ResumeAnalyzer.get_or_analyze_resume(document_id)
        resume_data = analysis["resume_data"]

        mode_clean = mode.lower() if mode else "technical"
        diff_clean = difficulty.lower() if difficulty else "medium"

        # Prepare context summary from actual resume data
        context_str = f"""Candidate Name: {resume_data.get('candidate_name')}
Headline: {resume_data.get('headline')}
Technical Skills: {', '.join(resume_data.get('technical_skills', []))}
Soft Skills: {', '.join(resume_data.get('soft_skills', []))}
Projects: {json.dumps(resume_data.get('projects', []), ensure_ascii=False)}
Experience: {json.dumps(resume_data.get('experience', []), ensure_ascii=False)}
Education: {json.dumps(resume_data.get('education', []), ensure_ascii=False)}
Certifications: {json.dumps(resume_data.get('certifications', []), ensure_ascii=False)}
"""

        role_str = f"Target Role: {role}\n" if role else ""

        prompt = f"""You are an expert technical interviewer and viva examiner.
Generate exactly {count} interview questions based strictly on the candidate's resume below.
Do NOT invent claims or technologies not present in the resume.

Interview Mode: {mode_clean}
{role_str}Difficulty: {diff_clean}

Return a valid JSON array of question objects matching this schema:
[
  {{
    "id": "q1",
    "question": "Clear interview question string",
    "source": "resume",
    "related_section": "projects|skills|experience|education",
    "topic": "Target Technology or Concept"
  }}
]

Resume Context:
{context_str}"""

        questions = []
        try:
            manager = LLMProviderManager()
            chain = manager.get_configured_chain()
            if chain:
                prov = manager.providers[chain[0]]
                llm_res = prov.generate_answer(query="Generate resume interview questions JSON", formatted_context=prompt)
                ans = llm_res.get("answer", "")
                json_match = re.search(r'\[.*\]', ans, re.DOTALL)
                if json_match:
                    questions = json.loads(json_match.group(0))
        except Exception as e:
            print(f"LLM question generation fallback: {e}")

        # Fallback question generator if LLM response not formatted
        if not questions or not isinstance(questions, list):
            questions = cls._fallback_questions(resume_data, mode_clean, count)

        # Normalize ids
        for idx, q in enumerate(questions):
            q["id"] = f"q{idx + 1}"

        return {
            "document_id": document_id,
            "mode": mode_clean,
            "difficulty": diff_clean,
            "role": role,
            "count": len(questions),
            "questions": questions[:count]
        }

    @classmethod
    def _fallback_questions(cls, resume_data: dict, mode: str, count: int) -> list[dict]:
        tech_skills = resume_data.get("technical_skills", ["Python", "RAG", "FAISS"])
        projects = resume_data.get("projects", [])

        questions = []
        if mode in ["project", "defense"]:
            for p in projects:
                p_name = p.get("name") if isinstance(p, dict) else str(p)
                questions.append({
                    "question": f"Can you explain the architecture and key challenges of project '{p_name}'?",
                    "source": "resume",
                    "related_section": "projects",
                    "topic": p_name
                })
        elif mode == "hr":
            questions.append({
                "question": "Walk me through your background and why you are interested in this role.",
                "source": "resume",
                "related_section": "experience",
                "topic": "Background & Introduction"
            })
            questions.append({
                "question": "What has been your most challenging project so far, and how did you overcome roadblocks?",
                "source": "resume",
                "related_section": "projects",
                "topic": "Problem Solving"
            })

        # Add technical questions for remaining slots
        for tech in tech_skills:
            if len(questions) >= count:
                break
            questions.append({
                "question": f"Why did you choose {tech} in your work, and how does it function under the hood?",
                "source": "resume",
                "related_section": "skills",
                "topic": tech
            })

        while len(questions) < count:
            idx = len(questions) + 1
            questions.append({
                "question": f"Explain the core technical concepts behind your projects and how you evaluated performance.",
                "source": "resume",
                "related_section": "projects",
                "topic": "Engineering Design"
            })

        return questions

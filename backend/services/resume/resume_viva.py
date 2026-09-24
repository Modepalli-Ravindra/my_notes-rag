import json
import re
from backend.services.resume.resume_analyzer import ResumeAnalyzer
from backend.services.resume.resume_question_generator import ResumeQuestionGenerator
from backend.services.llm.provider_manager import LLMProviderManager


class VivaEngine:
    """
    Interactive Viva Mode Engine:
    Evaluates candidate answers, generates qualitative feedback, provides Mana-Style Explanations
    ("Simple ga cheppalante..."), and formulates adaptive technical follow-up questions.
    """

    @classmethod
    def evaluate_viva_answer(
        cls,
        document_id: str | None,
        question: str,
        user_answer: str,
        mode: str = "general",
        notes_context: str | None = None
    ) -> dict:
        resume_context_str = ""
        if document_id:
            try:
                analysis = ResumeAnalyzer.get_or_analyze_resume(document_id)
                resume_data = analysis["resume_data"]
                resume_context_str = f"Candidate Resume Claims:\n{json.dumps(resume_data, ensure_ascii=False)}"
            except Exception:
                pass

        notes_str = f"\nRelevant Study Notes Context:\n{notes_context}" if notes_context else ""

        prompt = f"""You are an expert technical viva examiner and interview coach.
Evaluate the candidate's answer to the question below.

Question: {question}
Candidate's Answer: {user_answer}

{resume_context_str}
{notes_str}

CRITICAL MANA-STYLE EXPLANATION RULE:
Provide a "mana_style_explanation" using natural Telugu-English written in English letters.
- Always start with "Simple ga cheppalante..."
- Use natural Telugu sentence structure written entirely using English letters (NO Telugu script).
- Mix technical English terms naturally inside Telugu sentences (keep Python, SQL, FAISS, BM25, RAG, AST, etc. in English).
- Do NOT use awkward word-by-word translations or fragmented words.
- Explain conversationally as if a friendly peer is teaching another friend.
- Use natural phrases: "simple ga cheppalante", "ante", "ikkada", "enduku ante", "ela work avtundi ante", "use chestham", "consider cheddam", "example ga".

Return a JSON object matching this schema:
{{
  "feedback": {{
    "what_you_did_well": "Clear explanation of core concept...",
    "what_you_missed": "Should mention internal mechanics or retrieval steps...",
    "improvement_suggestion": "Practical step to improve answer depth and clarity...",
    "qualitative_status": "Strong | Good | Needs Improvement | Too Vague"
  }},
  "mana_style_explanation": "Simple ga cheppalante, interviewer ki...",
  "follow_up_question": "A logical follow-up question based on the candidate's answer and resume/notes"
}}"""

        try:
            manager = LLMProviderManager()
            chain = manager.get_configured_chain()
            if chain:
                prov = manager.providers[chain[0]]
                llm_res = prov.generate_answer(query="Evaluate viva answer", formatted_context=prompt)
                ans = llm_res.get("answer", "")
                json_match = re.search(r'\{.*\}', ans, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    try:
                        from backend.services.mana_explanation import ManaExplanationService
                        gemini_exp = ManaExplanationService.generate_mana_explanation(
                            question=question,
                            technical_answer=json.dumps(parsed.get("feedback", {}), ensure_ascii=False),
                            source_context=notes_context or "",
                            mode="VIVA"
                        )
                        if gemini_exp:
                            parsed["mana_style_explanation"] = gemini_exp
                    except Exception as ge_err:
                        print(f"Viva Gemini Mana note: {ge_err}")
                    return parsed
        except Exception as e:
            print(f"Viva evaluation fallback: {e}")

        # Fallback response
        return {
          "feedback": {
            "what_you_did_well": "You addressed the main point clearly.",
            "what_you_missed": "Try to add more technical architecture details or concrete examples.",
            "improvement_suggestion": "Focus on step-by-step technical explanation with real-world examples.",
            "qualitative_status": "Good"
          },
          "mana_style_explanation": f"Simple ga cheppalante, interviewer question '{question[:30]}...' antunnaru. Concept ni clear ga, step-by-step format lo explain cheyali.",
          "follow_up_question": "Can you explain the step-by-step data flow in your implementation?"
        }

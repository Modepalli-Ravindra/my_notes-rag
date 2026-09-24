import json
import re
from backend.services.llm.provider_manager import LLMProviderManager


class InterviewCoachingEngine:
    """
    Generates structured interview coaching packages:
    1. Interview-ready answer
    2. Mana-style explanation ("Simple ga cheppalante...")
    3. Key points to remember
    4. Possible follow-up question
    """

    @classmethod
    def generate_coaching(
        cls,
        question: str,
        resume_context: str | None = None,
        notes_context: str | None = None
    ) -> dict:
        resume_str = f"Resume Details:\n{resume_context}\n" if resume_context else ""
        notes_str = f"Study Notes Context:\n{notes_context}\n" if notes_context else ""

        prompt = f"""You are an expert technical interview coach.
Provide a complete interview coaching breakdown for the following question:

Question: {question}

{resume_str}{notes_str}

CRITICAL MANA-STYLE EXPLANATION RULE:
Provide a "mana_style_explanation" using natural Telugu-English written in English letters.
- Always start with "Simple ga cheppalante..."
- Use natural Telugu sentence structure written entirely using English letters (NO Telugu script).
- Mix technical English terms naturally inside Telugu sentences (keep Python, SQL, FAISS, BM25, RAG, AST, etc. in English).
- Do NOT use awkward word-by-word translations or fragmented words.
- Explain conversationally as if a friendly peer is teaching another friend.
- Use natural phrases: "simple ga cheppalante", "ante", "ikkada", "enduku ante", "ela work avtundi ante", "use chestham", "consider cheddam", "example ga".

Return a valid JSON object matching this schema:
{{
  "question": "{question}",
  "interview_ready_answer": "Clear, professional, interview-ready answer...",
  "mana_style_explanation": "Simple ga cheppalante...",
  "key_points": [
    "Key concept 1",
    "Key concept 2",
    "Key concept 3"
  ],
  "follow_up_question": "Logical follow-up question that an interviewer might ask next"
}}"""

        try:
            manager = LLMProviderManager()
            chain = manager.get_configured_chain()
            if chain:
                prov = manager.providers[chain[0]]
                llm_res = prov.generate_answer(query="Generate interview coaching JSON", formatted_context=prompt)
                ans = llm_res.get("answer", "")
                json_match = re.search(r'\{.*\}', ans, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    try:
                        from backend.services.mana_explanation import ManaExplanationService
                        gemini_exp = ManaExplanationService.generate_mana_explanation(
                            question=question,
                            technical_answer=parsed.get("interview_ready_answer", ""),
                            source_context=notes_context or resume_context or "",
                            mode="INTERVIEW"
                        )
                        if gemini_exp:
                            parsed["mana_style_explanation"] = gemini_exp
                    except Exception as ge_err:
                        print(f"Coaching Gemini Mana note: {ge_err}")
                    return parsed
        except Exception as e:
            print(f"Interview coaching fallback: {e}")

        return {
            "question": question,
            "interview_ready_answer": f"To answer '{question}', explain the core concepts clearly, highlight technical trade-offs, and describe how you implemented the solution.",
            "mana_style_explanation": f"Simple ga cheppalante, interviewer inni sarlu '{question}' adigithe, direct ga main concept cheppi enduku use cheshamo explain cheyali.",
            "key_points": [
                "State core definition",
                "Explain architectural trade-offs",
                "Mention practical usage example"
            ],
            "follow_up_question": "What alternative approach would you consider if requirements scaled by 10x?"
        }

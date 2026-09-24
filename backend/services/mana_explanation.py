import os
import re
from typing import Optional
from backend.services.llm.gemini_provider import GeminiProvider


GEMINI_MANA_PROMPT = """You are the Mana-style explanation teacher for a Telugu-speaking learner.

Your job is NOT to change the technical meaning.
Your job is to explain the supplied technical answer in natural conversational Telugu written entirely using English letters, while keeping technical terms in English.

Do not use Telugu script.

Do not translate technical terms such as:
Python, List, Tuple, mutable, immutable, API, RAG, FAISS, BM25, embeddings, vector, SQL, FastAPI, React, recursion, complexity, AST, CodeBERT, etc.

Use natural Telugu sentence structure.
The explanation should sound like a knowledgeable friend teaching another friend.

Use natural Telugu constructions such as:
'ante'
'ikkada'
'simple ga cheppalante'
'enduku ante'
'ela work avtundi ante'
'manam'
'chestham'
'cheyyachu'
'cheyyalem'
'avutundi'
'vastundi'
'use chestham'
'consider cheddam'
'example ga'

Avoid awkward constructions such as:
'List ekada mutable object'
'creation pakkaina'
'nenu ani change cheyochu'

Instead write naturally:
'List anedi mutable object.'
'List ni create chesina tarvata existing object lone changes cheyyachu.'
'Ante manam values ni add, remove, modify cheyyachu.'

Do not translate English technical terminology into unnatural Telugu.
Do not write formal textbook Telugu.
Do not produce a word-by-word translation of the technical answer.
Do not add unsupported facts.
Use only the supplied technical answer and source context.

If the technical answer contains code, explain the code in simple Telugu-English and preserve the code exactly.

The explanation should normally have:
1. Simple ga cheppalante...
2. Enduku ante...
3. Ela work avtundi ante...
4. Example...
5. Simple takeaway...

Keep it concise but clear.
The output must contain ONLY the explanation text.
Do not include headings such as 'Technical Answer'.
Do not mention this instruction.

STYLE REFERENCE EXAMPLES:

BAD: "List ekada mutable object. Meaning creation pakkaina nenu ani change cheyochu."
GOOD: "Simple ga cheppalante, List anedi mutable object. Ante manam List ni create chesina tarvata kuda, existing List lo values ni add cheyyachu, remove cheyyachu, modify cheyyachu."

BAD: "Tuple ekada immutable object."
GOOD: "Simple ga cheppalante, Tuple anedi immutable object. Ante Tuple ni create chesina tarvata, danilo unna values ni direct ga change cheyyalem."

BAD: "FAISS similarity search kosam vector use chestundi."
GOOD: "Simple ga cheppalante, mana documents lo unna chunks ni vector format lo store chestham. User question ki meaning-wise close ga unna chunks ni fast ga find cheyyadaniki FAISS use chestham."

BAD: "RAG gives context to LLM."
GOOD: "Simple ga cheppalante, LLM ki complete document motham ivvakunda, user question ki relevant ga unna chunks matrame retrieve chesi LLM ki pampistham. Daanivalla answer ki correct context dorukutundi."
"""

MODE_GUIDELINES = {
    "CODING": "Focus on explaining algorithm logic, time/space complexity, and code execution flow in natural Telugu-English.",
    "INTERVIEW": "Focus on explaining why the interviewer is asking this, what technical depth they look for, and how to explain real project experience.",
    "RESUME": "Focus on explaining how candidate resume claims relate to technical concepts and real-world project usage.",
    "VIVA": "Focus on step-by-step oral presentation, key technical mechanics, and immediate follow-up preparation.",
    "EXAM": "Focus on high-scoring core concepts, key definitions, and exam takeaways.",
    "STUDY": "Focus on intuitive conceptual foundation, friend-to-friend teaching, and simple memory hooks.",
    "REVISION": "Focus on quick bullet-point summary of key technical takeaways.",
    "QUIZ": "Focus on explaining the correct choice and why distractor options are incorrect."
}

TELUGU_MARKERS = [
    "ante", "cheppalante", "ikkada", "enduku", "work", "manam",
    "chestham", "cheyyachu", "cheyyalem", "avutundi", "vastundi",
    "use", "consider", "example", "dini", "valla", "lo"
]


class ManaExplanationService:
    """
    Dedicated Mana-Style Explanation Engine powered exclusively by Google Gemini.
    """

    @classmethod
    def is_enabled(cls) -> bool:
        val = os.environ.get("ENABLE_MANA_EXPLANATION", "true").strip().lower()
        return val in ("true", "1", "yes")

    @classmethod
    def clean_explanation_text(cls, text: str) -> str:
        if not text:
            return ""

        # Remove markdown fences if any
        clean_text = text.strip()
        if clean_text.startswith("```"):
            clean_text = clean_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        # If thinking/scratchpad process precedes the explanation, isolate the final explanation block
        if "Simple ga cheppalante" in clean_text:
            parts = clean_text.split("Simple ga cheppalante")
            clean_text = "Simple ga cheppalante" + parts[-1]

        # Strip inline meta step tags like *Step 1: Explaining...*
        clean_text = re.sub(r'\*Step \d+:.*?\*\n?', '', clean_text)

        # Strip remaining bullet markers and model self-checklists
        clean_lines = []
        for line in clean_text.split("\n"):
            line_str = line.strip()
            if re.match(r'^(No Telugu script\?|Technical terms preserved\?|Natural Telugu\?|No headings|Structure followed\?|Concise\?|\*Final Polish:\*).*', line_str, re.IGNORECASE):
                continue
            if line_str.startswith("* ") or line_str.startswith("- "):
                line_str = line_str[2:].strip()
            clean_lines.append(line_str)

        return "\n".join(clean_lines).strip()

    @classmethod
    def validate_explanation(cls, text: str) -> bool:
        if not text or not isinstance(text, str):
            return False

        # 1. Reject if Telugu script is present
        if re.search(r'[\u0C00-\u0C7F]', text):
            return False

        # 2. Reject obvious awkward phrases
        awkward_patterns = [
            r'ekada mutable', r'creation pakkaina', r'nenu ani change',
            r'list ekada', r'tuple ekada', r'meaning creation'
        ]
        for pattern in awkward_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False

        # 3. Check for natural Telugu-English markers
        text_lower = text.lower()
        has_marker = any(m in text_lower for m in TELUGU_MARKERS)
        if not has_marker:
            return False

        return True

    @classmethod
    def generate_mana_explanation(
        cls,
        question: str,
        technical_answer: str,
        source_context: str = "",
        mode: str = "NORMAL_RAG"
    ) -> Optional[str]:
        if not cls.is_enabled():
            return None

        provider_name = os.environ.get("MANA_EXPLANATION_PROVIDER", "gemini").strip().lower()
        target_model = os.environ.get("MANA_EXPLANATION_MODEL", "gemma-4-26b-a4b-it").strip()

        mode_upper = mode.upper().strip()
        mode_instruction = MODE_GUIDELINES.get(mode_upper, "")

        context_str = f"\nRELEVANT SOURCE CONTEXT:\n{source_context[:4000]}\n" if source_context else ""

        prompt = f"""Mode: {mode_upper}
{mode_instruction}

User Question:
{question}

Grounded Technical Answer:
{technical_answer}
{context_str}
Explain the technical answer above strictly in natural Mana-style Telugu-English using English letters only."""

        try:
            gemini = GeminiProvider()
            raw_res = gemini.generate_answer(
                query=prompt,
                formatted_context="",
                model_name=target_model,
                system_prompt=GEMINI_MANA_PROMPT
            )
            raw_text = raw_res.get("answer", "").strip()
            explanation = cls.clean_explanation_text(raw_text)

            # Quality Validation Step 1
            if cls.validate_explanation(explanation):
                return explanation

            # Retry once with explicit refinement prompt if validation failed
            retry_prompt = f"{prompt}\n\nREWRITE INSTRUCTION: Rewrite naturally. Use conversational Telugu sentence structure in English letters. Preserve technical terms. Do not change meaning."
            retry_res = gemini.generate_answer(
                query=retry_prompt,
                formatted_context="",
                model_name=target_model,
                system_prompt=GEMINI_MANA_PROMPT
            )
            retry_raw = retry_res.get("answer", "").strip()
            retry_explanation = cls.clean_explanation_text(retry_raw)

            if cls.validate_explanation(retry_explanation):
                return retry_explanation

            # If retry still validly fails, return cleaned attempt if non-empty
            if retry_explanation and not re.search(r'[\u0C00-\u0C7F]', retry_explanation):
                return retry_explanation

            return explanation if explanation and not re.search(r'[\u0C00-\u0C7F]', explanation) else None

        except Exception as e:
            print(f"Gemini Mana Explanation note: {e}")
            return f"Simple ga cheppalante, {question} ki technical answer ni simple ga explain cheyochu. Core concept ni evaluate chesi step-by-step implement chestham."

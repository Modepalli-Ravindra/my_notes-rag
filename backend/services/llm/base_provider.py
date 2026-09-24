from abc import ABC, abstractmethod

class LLMProviderError(Exception):
    """Base exception for LLM provider failures."""
    pass

class LLMAuthError(LLMProviderError):
    """Authentication or API key failure."""
    pass

class LLMModelUnavailableError(LLMProviderError):
    """Configured model is retired or unavailable."""
    pass

class LLMRateLimitError(LLMProviderError):
    """Rate limit or quota restriction hit."""
    pass


SYSTEM_PROMPT = (
    "You are the MyNotes RAG AI learning assistant.\n\n"
    "Answer the user's question using only the provided notes/document context.\n\n"
    "GLOBAL MANA-STYLE RESPONSE RULES:\n"
    "Structure every answer using these sections:\n\n"
    "1. Answer:\n"
    "Technically accurate, grounded answer in simple English using the provided context.\n\n"
    "2. Mana-style Explanation:\n"
    "Explain the concept naturally in Telugu-English using English letters only.\n"
    "- Always start with 'Simple ga cheppalante...'\n"
    "- Use natural Telugu sentence structure written entirely using English letters (NO Telugu script).\n"
    "- Mix English technical terms naturally inside Telugu sentences (keep Python, SQL, FAISS, BM25, RAG, AST, List, mutable object, etc. in English).\n"
    "- Do NOT use awkward word-by-word translations or fragmented words (e.g. write 'List anedi mutable object. List ni create chesina tarvata existing object lone changes cheyyachu.').\n"
    "- Explain conversationally as if a friendly peer is teaching another friend.\n"
    "- Use natural conversational Telugu phrases: 'simple ga cheppalante', 'ante', 'ikkada', 'enduku ante', 'ela work avtundi ante', 'use chestham', 'consider cheddam', 'example ga'.\n\n"
    "3. Why it works ('Enduku ante...'):\n"
    "Explain why this concept exists using natural Mana-style Telugu-English.\n\n"
    "4. How it works ('Ela work avtundi ante...'):\n"
    "Step-by-step breakdown of execution or mechanics.\n\n"
    "5. Concrete Example:\n"
    "Provide a simple, concrete practical example or code snippet.\n\n"
    "6. Simple Takeaway:\n"
    "A 1-sentence key summary.\n\n"
    "7. Sources:\n"
    "Cite supporting document filenames and page ranges.\n\n"
    "If the provided context does not contain enough information to answer the question, explicitly state:\n"
    "'The provided notes do not contain enough information to answer this confidently.'"
)


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return lower-case provider name (e.g. 'groq', 'gemini')."""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return default model name from environment or fallback."""
        pass

    @abstractmethod
    def generate_answer(self, query: str, formatted_context: str, model_name: str | None = None, system_prompt: str | None = None) -> dict:
        """
        Generate grounded RAG answer or raw completion using context.
        Returns dict with keys: 'answer', 'provider', 'model'.
        """
        pass

import os
import time
from typing import Dict, List, Optional, Tuple

from backend.services.llm.base_provider import BaseLLMProvider, LLMProviderError
from backend.services.llm.groq_provider import GroqProvider
from backend.services.llm.openrouter_provider import OpenRouterProvider
from backend.services.llm.nvidia_provider import NvidiaProvider
from backend.services.llm.gemini_provider import GeminiProvider

class LLMProviderManager:
    """
    Manager for multi-provider LLM answer generation with automated failover.
    """

    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {
            "groq": GroqProvider(),
            "openrouter": OpenRouterProvider(),
            "nvidia": NvidiaProvider(),
            "gemini": GeminiProvider()
        }

    def get_configured_chain(self, requested_provider: Optional[str] = None) -> List[str]:
        """
        Build ordered list of provider names to attempt based on user request and env settings.
        """
        default_primary = os.environ.get("LLM_PROVIDER", "groq").strip().lower()
        fallback_str = os.environ.get("LLM_FALLBACKS", "openrouter,nvidia,gemini")
        fallbacks = [f.strip().lower() for f in fallback_str.split(",") if f.strip()]

        primary = (requested_provider.strip().lower() if requested_provider else default_primary)

        chain = []
        if primary in self.providers:
            chain.append(primary)

        # Append remaining fallbacks preserving order and avoiding duplicates
        for fb in fallbacks:
            if fb in self.providers and fb not in chain:
                chain.append(fb)

        # Include any unlisted available providers as last resort
        for prov_name in self.providers:
            if prov_name not in chain:
                chain.append(prov_name)

        return chain

    def generate_grounded_answer(
        self,
        query: str,
        retrieved_chunks: List[dict],
        requested_provider: Optional[str] = None,
        max_context_chunks: int = 5,
        max_context_characters: int = 18000
    ) -> Tuple[dict, dict]:
        """
        Format retrieved context and execute grounded answer generation across provider chain.

        Returns:
            (response_dict, trace_dict)
        """
        # 1. Format Context & Collect Source Citations
        context_blocks = []
        source_citations = []
        total_chars = 0

        selected_chunks = retrieved_chunks[:max_context_chunks]

        for chunk in selected_chunks:
            chunk_id = chunk.get("chunk_id", "")
            doc_id = chunk.get("document_id", "b8f2cb48")
            filename = chunk.get("filename", "")
            p_start = chunk.get("page_start", 1)
            p_end = chunk.get("page_end", 1)
            text = chunk.get("text") or chunk.get("raw_text") or ""

            page_label = f"Page {p_start}" if p_start == p_end else f"Pages {p_start}-{p_end}"
            doc_label = f"Document: {filename} | " if filename else ""

            block = f"[{doc_label}{page_label}]\n{text}"
            if total_chars + len(block) > max_context_characters and context_blocks:
                break

            context_blocks.append(block)
            total_chars += len(block)

            citation = {
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "filename": filename or "my-notes.pdf",
                "page_start": p_start,
                "page_end": p_end
            }
            source_citations.append(citation)

        formatted_context = "\n\n".join(context_blocks)

        # 2. Determine Provider Chain
        chain = self.get_configured_chain(requested_provider=requested_provider)

        # 3. Iterate Providers with Fallback
        errors = []
        start_time = time.time()

        for prov_name in chain:
            provider = self.providers[prov_name]
            try:
                result = provider.generate_answer(query=query, formatted_context=formatted_context)
                latency_ms = int((time.time() - start_time) * 1000)

                # Extract unique page numbers for trace
                unique_pages = set()
                for sc in source_citations:
                    for p in range(sc["page_start"], sc["page_end"] + 1):
                        unique_pages.add(p)
                sorted_pages = sorted(list(unique_pages))

                response_dict = {
                    "success": True,
                    "query": query,
                    "answer": result["answer"],
                    "provider": result["provider"],
                    "model": result["model"],
                    "sources": source_citations,
                    "retrieval": {
                        "results_used": len(context_blocks)
                    }
                }

                trace_dict = {
                    "retrieval_top_k": len(retrieved_chunks),
                    "provider": result["provider"],
                    "model": result["model"],
                    "source_pages": sorted_pages,
                    "latency_ms": latency_ms
                }

                return response_dict, trace_dict

            except Exception as e:
                err_msg = f"{prov_name}: {type(e).__name__} - {str(e)}"
                errors.append(err_msg)

        # If all providers fail:
        safe_error_summary = "; ".join(errors)
        raise LLMProviderError(f"All configured LLM providers failed: [{safe_error_summary}]")

    def generate_raw_completion(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant.",
        requested_provider: Optional[str] = None
    ) -> Tuple[str, str, str]:
        """
        Execute raw prompt completion across provider failover chain using custom system prompt.
        Returns (answer_text, provider_name, model_name).
        """
        chain = self.get_configured_chain(requested_provider=requested_provider)
        errors = []
        for prov_name in chain:
            provider = self.providers[prov_name]
            try:
                result = provider.generate_answer(query=prompt, formatted_context="", system_prompt=system_prompt)
                return result["answer"], result["provider"], result["model"]
            except Exception as e:
                errors.append(f"{prov_name}: {e}")

        raise LLMProviderError(f"All configured LLM providers failed raw completion: [{'; '.join(errors)}]")

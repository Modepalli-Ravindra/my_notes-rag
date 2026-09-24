import os
import httpx
from backend.services.llm.base_provider import (
    BaseLLMProvider,
    SYSTEM_PROMPT,
    LLMProviderError,
    LLMAuthError,
    LLMModelUnavailableError,
    LLMRateLimitError
)

class GeminiProvider(BaseLLMProvider):
    """Google Gemini API Provider."""

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return os.environ.get("GEMINI_MODEL", "gemma-4-26b-a4b-it")

    def _get_api_key(self) -> str:
        key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise LLMAuthError("Gemini API key missing in server environment.")
        return key

    def generate_answer(self, query: str, formatted_context: str, model_name: str | None = None, system_prompt: str | None = None) -> dict:
        api_key = self._get_api_key()
        target_model = model_name or self.default_model
        sys_p = system_prompt if system_prompt is not None else SYSTEM_PROMPT

        if not target_model.startswith("models/"):
            model_path = f"models/{target_model}"
        else:
            model_path = target_model

        url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:generateContent?key={api_key}"

        prompt_text = f"{sys_p}\n\nCONTEXT:\n{formatted_context}\n\nQUESTION:\n{query}" if formatted_context else f"{sys_p}\n\nPROMPT:\n{query}"

        payload = {
            "contents": [{
                "parts": [{"text": prompt_text}]
            }]
        }

        try:
            with httpx.Client(timeout=90.0) as client:
                response = client.post(url, json=payload, headers={"Content-Type": "application/json"})

            if response.status_code == 200:
                data = response.json()
                try:
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise LLMProviderError("Gemini returned empty candidates list.")
                    part_text = candidates[0]["content"]["parts"][0]["text"].strip()
                    return {
                        "answer": part_text,
                        "provider": self.provider_name,
                        "model": target_model
                    }
                except (KeyError, IndexError) as e:
                    raise LLMProviderError(f"Failed to parse Gemini response payload: {e}")
            elif response.status_code in (500, 502, 503, 504):
                if target_model != "gemini-2.5-flash":
                    return self.generate_answer(query=query, formatted_context=formatted_context, model_name="gemini-2.5-flash", system_prompt=system_prompt)
                raise LLMProviderError(f"Gemini API returned HTTP {response.status_code}: {response.text[:200]}")
            elif response.status_code == 404:
                # If target model 404s, attempt fallback to gemini-2.5-flash
                if target_model != "gemini-2.5-flash":
                    return self.generate_answer(query=query, formatted_context=formatted_context, model_name="gemini-2.5-flash", system_prompt=system_prompt)
                raise LLMModelUnavailableError(f"Gemini model '{target_model}' is unavailable or retired.")
            elif response.status_code == 401 or response.status_code == 403:
                raise LLMAuthError("Gemini authentication failed / unauthorized key.")
            elif response.status_code == 429:
                raise LLMRateLimitError("Gemini rate limit or quota exceeded.")
            else:
                err_msg = response.text[:200]
                raise LLMProviderError(f"Gemini API returned HTTP {response.status_code}: {err_msg}")

        except httpx.RequestError as e:
            if target_model != "gemini-2.5-flash":
                try:
                    return self.generate_answer(query=query, formatted_context=formatted_context, model_name="gemini-2.5-flash", system_prompt=system_prompt)
                except Exception:
                    pass
            raise LLMProviderError(f"Gemini network request failed: {type(e).__name__}")

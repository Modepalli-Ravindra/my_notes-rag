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

class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter API Provider."""

    @property
    def provider_name(self) -> str:
        return "openrouter"

    @property
    def default_model(self) -> str:
        return os.environ.get("OPENROUTER_MODEL", "nex-agi/nex-n2.5-mini:free")

    def _get_api_key(self) -> str:
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise LLMAuthError("OpenRouter API key missing in server environment.")
        return key

    def generate_answer(self, query: str, formatted_context: str, model_name: str | None = None, system_prompt: str | None = None) -> dict:
        api_key = self._get_api_key()
        target_model = model_name or self.default_model
        sys_p = system_prompt if system_prompt is not None else SYSTEM_PROMPT

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        user_content = f"CONTEXT:\n{formatted_context}\n\nQUESTION:\n{query}" if formatted_context else query

        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": sys_p},
                {"role": "user", "content": user_content}
            ],
            "max_tokens": 1024,
            "temperature": 0.2
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                data = response.json()
                try:
                    content = data["choices"][0]["message"]["content"].strip()
                    return {
                        "answer": content,
                        "provider": self.provider_name,
                        "model": target_model
                    }
                except (KeyError, IndexError) as e:
                    raise LLMProviderError(f"Failed to parse OpenRouter response payload: {e}")
            elif response.status_code == 401 or response.status_code == 403:
                raise LLMAuthError("OpenRouter authentication failed or unauthorized key.")
            elif response.status_code == 404:
                raise LLMModelUnavailableError(f"OpenRouter model '{target_model}' is unavailable.")
            elif response.status_code == 429:
                raise LLMRateLimitError("OpenRouter rate limit exceeded.")
            else:
                err_msg = response.text[:200]
                raise LLMProviderError(f"OpenRouter API returned HTTP {response.status_code}: {err_msg}")

        except httpx.RequestError as e:
            raise LLMProviderError(f"OpenRouter network request failed: {type(e).__name__}")

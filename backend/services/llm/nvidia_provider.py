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

class NvidiaProvider(BaseLLMProvider):
    """NVIDIA NIM API Provider."""

    @property
    def provider_name(self) -> str:
        return "nvidia"

    @property
    def default_model(self) -> str:
        return os.environ.get("NVIDIA_MODEL", "meta/llama-3.2-11b-vision-instruct")

    def _get_api_key(self) -> str:
        key = os.environ.get("NVIDIA_API_KEY") or os.environ.get("NVIDIA_NIM_API_KEY")
        if not key:
            raise LLMAuthError("NVIDIA API key missing in server environment.")
        return key

    def generate_answer(self, query: str, formatted_context: str, model_name: str | None = None, system_prompt: str | None = None) -> dict:
        api_key = self._get_api_key()
        target_model = model_name or self.default_model
        sys_p = system_prompt if system_prompt is not None else SYSTEM_PROMPT

        url = "https://integrate.api.nvidia.com/v1/chat/completions"
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
                    raise LLMProviderError(f"Failed to parse NVIDIA response payload: {e}")
            elif response.status_code == 401 or response.status_code == 403:
                raise LLMAuthError("NVIDIA authentication failed or unauthorized key.")
            elif response.status_code in (404, 410):
                raise LLMModelUnavailableError(f"NVIDIA model '{target_model}' is unavailable or retired.")
            elif response.status_code == 429:
                raise LLMRateLimitError("NVIDIA rate limit exceeded.")
            else:
                err_msg = response.text[:200]
                raise LLMProviderError(f"NVIDIA API returned HTTP {response.status_code}: {err_msg}")

        except httpx.RequestError as e:
            raise LLMProviderError(f"NVIDIA network request failed: {type(e).__name__}")

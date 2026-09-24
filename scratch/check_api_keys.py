import os
import sys
import json
import urllib.request
import urllib.error

PROJECT_ROOT = r"c:\Users\user\OneDrive\Desktop\mynotes-rag"

def mask_key(val: str) -> str:
    if not val:
        return "MISSING"
    val = val.strip()
    if len(val) <= 4:
        return "****"
    return f"...{val[-4:]}"

def safe_log(msg: str):
    print(msg, flush=True)

def parse_env_file(filepath: str) -> dict:
    env_vars = {}
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'").strip('"')
                    env_vars[k] = v
    return env_vars

def main():
    env_file = os.path.join(PROJECT_ROOT, "backend", ".env")
    env_vars = parse_env_file(env_file)

    gemini_key = env_vars.get("GEMINI_API_KEY") or env_vars.get("GOOGLE_API_KEY")
    groq_key = env_vars.get("GROQ_API_KEY")
    openrouter_key = env_vars.get("OPENROUTER_API_KEY")
    nvidia_key = env_vars.get("NVIDIA_API_KEY") or env_vars.get("NVIDIA_NIM_API_KEY")

    safe_log("=== DETAILED DIAGNOSTIC FOR OPENROUTER & NVIDIA ===")

    # 3. OPENROUTER TEST
    safe_log("\n--- OPENROUTER TEST ---")
    if openrouter_key:
        url = "https://openrouter.ai/api/v1/models"
        try:
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {openrouter_key}"})
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                all_models = [m["id"] for m in data.get("data", [])]
                free_models = [m for m in all_models if ":free" in m]
                safe_log(f"OpenRouter Total Models: {len(all_models)}, Free Models: {len(free_models)}")

                # Select a reliable text model
                text_free_models = [m for m in free_models if "gemma" in m or "llama" in m or "qwen" in m or "mistral" in m]
                target_model = text_free_models[0] if text_free_models else (free_models[0] if free_models else "meta-llama/llama-3.2-1b-instruct:free")
                safe_log(f"Testing model: {target_model}")

                chat_url = "https://openrouter.ai/api/v1/chat/completions"
                payload = json.dumps({
                    "model": target_model,
                    "messages": [{"role": "user", "content": "Reply with exactly: MyNotes RAG connection successful."}],
                    "max_tokens": 30,
                    "temperature": 0.0
                }).encode()

                c_req = urllib.request.Request(chat_url, data=payload, headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openrouter_key}",
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "MyNotes RAG"
                })
                with urllib.request.urlopen(c_req) as c_resp:
                    c_data = json.loads(c_resp.read().decode())
                    choice = c_data["choices"][0]
                    content = choice.get("message", {}).get("content", "")
                    safe_log(f"OpenRouter Response Status: 200 OK")
                    safe_log(f"OpenRouter Model Tested: {target_model}")
                    safe_log(f"OpenRouter Test Output: \"{content}\"")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            safe_log(f"OpenRouter Error (HTTP {e.code}): {err_body}")

    # 4. NVIDIA TEST
    safe_log("\n--- NVIDIA TEST ---")
    if nvidia_key:
        url = "https://integrate.api.nvidia.com/v1/models"
        try:
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {nvidia_key}"})
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                models = [m["id"] for m in data.get("data", [])]
                safe_log(f"NVIDIA Total Models: {len(models)}")
                if models:
                    target_model = models[0]
                    safe_log(f"Testing NVIDIA model: {target_model}")

                    chat_url = "https://integrate.api.nvidia.com/v1/chat/completions"
                    payload = json.dumps({
                        "model": target_model,
                        "messages": [{"role": "user", "content": "Reply with exactly: MyNotes RAG connection successful."}],
                        "max_tokens": 30,
                        "temperature": 0.0
                    }).encode()
                    c_req = urllib.request.Request(chat_url, data=payload, headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {nvidia_key}"
                    })
                    with urllib.request.urlopen(c_req) as c_resp:
                        c_data = json.loads(c_resp.read().decode())
                        content = c_data["choices"][0]["message"]["content"]
                        safe_log(f"NVIDIA Response Status: 200 OK")
                        safe_log(f"NVIDIA Model Tested: {target_model}")
                        safe_log(f"NVIDIA Test Output: \"{content}\"")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            safe_log(f"NVIDIA Error (HTTP {e.code}): {err_body}")

if __name__ == "__main__":
    main()

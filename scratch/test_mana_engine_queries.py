import urllib.request
import json
import time

API_BASE = "http://127.0.0.1:8000"

test_queries = [
    "Explain mutable and immutable objects.",
    "What is RAG?",
    "What is FAISS?",
    "What is BM25?",
    "What is a lambda function?",
    "Explain exception handling.",
    "Why did you use FastAPI in your project?",
    "Explain your AI Code Complexity Analyzer project.",
    "Why did you use hybrid retrieval?",
    "Explain the coding error in a simple way."
]

print("================ TESTING DEDICATED GEMINI MANA-STYLE EXPLANATION ENGINE ================\n", flush=True)

for i, query in enumerate(test_queries, 1):
    print(f"[{i}/10] Query: {query}", flush=True)
    t0 = time.time()
    req = urllib.request.Request(
        f"{API_BASE}/ask",
        data=json.dumps({"query": query, "top_k": 3}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            latency = int((time.time() - t0) * 1000)
            data = json.loads(resp.read().decode('utf-8'))
            tech_ans = data.get("answer", "")
            mana_exp = data.get("mana_explanation", "")
            
            print(f"Latency: {latency}ms | Provider: {data.get('provider')} / {data.get('model')}", flush=True)
            print(f"Technical Answer snippet: {tech_ans[:90]}...", flush=True)
            if mana_exp:
                print(f"[OK] Gemini Mana Explanation:\n{mana_exp}\n", flush=True)
            else:
                print("⚠️ Mana explanation missing\n", flush=True)
    except Exception as e:
        print(f"FAILED: {e}\n", flush=True)

print("================ ALL TEST QUERIES COMPLETED ================", flush=True)

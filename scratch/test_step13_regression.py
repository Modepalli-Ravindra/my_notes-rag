import urllib.request
import json

API_BASE = "http://127.0.0.1:8000"

def test_endpoint(name, method, url, data=None):
    print(f"\n--- Testing {name} ---")
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8') if data else None,
        headers={'Content-Type': 'application/json'} if data else {}
    )
    req.get_method = lambda: method
    try:
        with urllib.request.urlopen(req) as resp:
            status_code = resp.getcode()
            body = json.loads(resp.read().decode('utf-8'))
            print(f"Status: {status_code}")
            return True, body
    except Exception as e:
        print(f"FAILED: {e}")
        return False, str(e)

results = {}

# 1. /search
ok, res = test_endpoint("Multi-Doc Search", "POST", f"{API_BASE}/search", {"query": "transformer attention", "top_k": 2})
results["search"] = ok

# 2. /ask
ok, res = test_endpoint("RAG Ask", "POST", f"{API_BASE}/ask", {"query": "What is self-attention in transformers?", "top_k": 2})
results["ask"] = ok
if ok:
    print("Answer snippet:", res.get("answer", "")[:120])
    if "Simple ga cheppalante" in res.get("answer", "") or "mana" in res.get("answer", "").lower():
        print("[OK] Mana-style explanation detected in RAG response")

# 3. /resume/cf15cd49/analysis
ok, res = test_endpoint("Resume Analysis", "GET", f"{API_BASE}/resume/cf15cd49/analysis")
results["resume_analysis"] = ok
if ok:
    print("Candidate:", res.get("candidate_name"))
    print("Education:", res.get("education"))
    exps = res.get("experience", [])
    print("Experience:", exps)
    print("Projects:", [p.get("title") for p in res.get("projects", [])])
    
    # Precision Regression Assertion: PowerUrBiz -> AI Engineer Intern
    powerurbiz_exp = next((e for e in exps if e.get("company") == "PowerUrBiz"), None)
    assert powerurbiz_exp is not None, "PowerUrBiz experience entry not found!"
    assert powerurbiz_exp.get("role") == "AI Engineer Intern", f"Role mismatch! Expected 'AI Engineer Intern', got '{powerurbiz_exp.get('role')}'"
    print("[OK] PRECISION ASSERTION PASSED: PowerUrBiz -> AI Engineer Intern")

# 4. Viva Session
ok, res = test_endpoint("Viva Session Start", "POST", f"{API_BASE}/resume/session/start", {"document_id": "cf15cd49", "mode": "technical"})
results["viva_start"] = ok

ok, res = test_endpoint("Viva Answer Submission", "POST", f"{API_BASE}/resume/session/answer", {
    "document_id": "cf15cd49",
    "question": "Explain RAG architecture and why you used vector similarity search.",
    "user_answer": "RAG retrieves relevant chunks from FAISS vector store using cosine similarity and passes them to LLM prompt context to ground generation.",
    "mode": "technical"
})
results["viva_answer"] = ok
if ok:
    print("Feedback score:", res.get("score"))
    print("Mana explanation:", res.get("mana_explanation", "")[:100])

# 5. Coding Problem
ok, res = test_endpoint("Coding Problem Generate", "POST", f"{API_BASE}/coding/problem/generate", {
    "language": "Python",
    "difficulty": "medium",
    "topic": "arrays",
    "document_id": "cf15cd49"
})
results["coding_generate"] = ok

# 6. Coding Execute
ok, res = test_endpoint("Coding Execute", "POST", f"{API_BASE}/coding/execute", {
    "language": "Python",
    "code": "def two_sum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target - n], i]\n        seen[n] = i\n    return []\nprint(two_sum([2, 7, 11, 15], 9))"
})
results["coding_execute"] = ok
if ok:
    print("Code stdout:", res.get("stdout", "").strip())

# 7. Coding Evaluate
ok, res = test_endpoint("Coding Evaluate", "POST", f"{API_BASE}/coding/evaluate", {
    "language": "Python",
    "code": "def two_sum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target - n], i]\n        seen[n] = i\n    return []",
    "problem_statement": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target."
})
results["coding_evaluate"] = ok
if ok:
    print("Evaluation Verdict:", res.get("verdict"))
    print("Mana summary:", res.get("mana_explanation", "")[:100])

print("\n================ SUMMARY ================")
for test_name, status in results.items():
    print(f"{test_name:25s}: {'PASSED' if status else 'FAILED'}")

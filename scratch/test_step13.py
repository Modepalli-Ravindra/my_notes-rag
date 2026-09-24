import os
import sys
import json

# Add backend directory to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_all_systems():
    print("--- 1. Testing Root Endpoint ---")
    res = client.get("/")
    assert res.status_code == 200
    print("Root status:", res.json())

    print("\n--- 2. Testing Existing Documents ---")
    res = client.get("/documents")
    assert res.status_code == 200
    docs = res.json().get("documents", [])
    print(f"Total documents registered: {len(docs)}")
    assert len(docs) > 0

    print("\n--- 3. Testing Existing RAG Search & Ask ---")
    search_res = client.post("/search", json={"query": "lambda functions in python", "top_k": 3})
    assert search_res.status_code == 200
    print("Search results count:", search_res.json().get("count"))

    ask_res = client.post("/ask", json={"query": "What is a lambda function?", "top_k": 3})
    assert ask_res.status_code == 200
    ask_json = ask_res.json()
    print("Ask response provider:", ask_json.get("provider"))
    print("Ask response preview:", ask_json.get("answer", "")[:150])

    print("\n--- 4. Testing Resume Analysis Endpoint ---")
    doc_id = "b8f2cb48"
    analysis_res = client.get(f"/resume/{doc_id}/analysis")
    assert analysis_res.status_code == 200
    ana_data = analysis_res.json()
    print("Resume analysis candidate name:", ana_data.get("resume_data", {}).get("candidate_name"))

    print("\n--- 5. Testing Viva Session Endpoints ---")
    viva_start = client.post("/resume/session/start", json={
        "document_id": doc_id,
        "mode": "technical",
        "difficulty": "medium",
        "count": 3
    })
    assert viva_start.status_code == 200
    viva_json = viva_start.json()
    print("Viva questions count:", viva_json.get("total_questions"))
    first_q = viva_json.get("current_question")
    print("Viva Question 1:", first_q)

    viva_ans = client.post("/resume/session/answer", json={
        "document_id": doc_id,
        "question": first_q,
        "user_answer": "Lambda functions are anonymous, single-expression functions in Python defined using the lambda keyword.",
        "mode": "technical",
        "include_notes_rag": True
    })
    assert viva_ans.status_code == 200
    viva_eval = viva_ans.json()
    print("Viva Mana Explanation present:", "mana_style_explanation" in viva_eval or "mana_explanation" in viva_eval)
    print("Viva Feedback:", viva_eval.get("feedback"))

    print("\n--- 6. Testing Interview Coaching Endpoint ---")
    coach_res = client.post("/resume/coaching", json={
        "question": "How do vector embeddings work in RAG?",
        "document_id": doc_id,
        "include_notes_rag": True
    })
    assert coach_res.status_code == 200
    coach_json = coach_res.json()
    print("Coaching response present:", bool(coach_json.get("mana_style_explanation")))

    print("\n--- 7. Testing Coding Problem Generation ---")
    prob_res = client.post("/coding/problem/generate", json={
        "language": "Python",
        "difficulty": "medium",
        "topic": "arrays",
        "role": "Backend Engineer",
        "document_id": doc_id,
        "include_notes_rag": True
    })
    assert prob_res.status_code == 200
    prob_data = prob_res.json()
    print("Generated Coding Problem Title:", prob_data.get("title"))

    print("\n--- 8. Testing Code Execution (Python, JS, Java, SQL) ---")
    py_exec = client.post("/coding/execute", json={
        "language": "Python",
        "code": "print('Hello Python Subprocess')"
    })
    assert py_exec.status_code == 200
    print("Python stdout:", py_exec.json().get("stdout").strip())

    js_exec = client.post("/coding/execute", json={
        "language": "JavaScript",
        "code": "console.log('Hello Node.js Subprocess');"
    })
    assert js_exec.status_code == 200
    print("JS status & stdout:", js_exec.json().get("status"), js_exec.json().get("stdout").strip())

    java_exec = client.post("/coding/execute", json={
        "language": "Java",
        "code": "public class Solution { public static void main(String[] args) { System.out.println(\"Hello Java\"); } }"
    })
    assert java_exec.status_code == 200
    print("Java status:", java_exec.json().get("status"), "| Stderr:", java_exec.json().get("stderr"))

    sql_exec = client.post("/coding/execute", json={
        "language": "SQL",
        "setup_sql": "CREATE TABLE test (id INT, name TEXT); INSERT INTO test VALUES (1, 'Alice');",
        "code": "SELECT * FROM test;"
    })
    assert sql_exec.status_code == 200
    print("SQL stdout:", sql_exec.json().get("stdout").strip())

    print("\n--- 9. Testing Coding Submission Evaluation ---")
    eval_res = client.post("/coding/evaluate", json={
        "language": "Python",
        "code": "def two_sum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        if target - num in seen:\n            return [seen[target - num], i]\n        seen[num] = i\n    return []\nprint(two_sum([2, 7, 11, 15], 9))",
        "problem_statement": "Given nums array and target, return indices of 2 numbers summing to target."
    })
    assert eval_res.status_code == 200
    eval_json = eval_res.json()
    print("Coding evaluation status:", eval_json.get("status"))
    print("Tests passed:", eval_json.get("tests_passed"), "Failed:", eval_json.get("tests_failed"))
    print("Mana explanation:", eval_json.get("mana_explanation"))

    print("\n=== ALL BACKEND TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_all_systems()

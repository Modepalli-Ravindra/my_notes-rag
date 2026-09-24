import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error

API_BASE = "http://127.0.0.1:8000"

def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    
    body = None
    if data is not None:
        if isinstance(data, dict):
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif isinstance(data, bytes):
            body = data

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode("utf-8")
            return resp.status, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(resp_body)
        except Exception:
            err_json = {"detail": resp_body}
        return e.code, err_json

def encode_multipart(fields, files):
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = []
    for k, v in fields.items():
        body.append(f"--{boundary}".encode("utf-8"))
        body.append(f'Content-Disposition: form-data; name="{k}"'.encode("utf-8"))
        body.append(b"")
        body.append(str(v).encode("utf-8"))
    
    for k, (filename, content, content_type) in files.items():
        body.append(f"--{boundary}".encode("utf-8"))
        body.append(f'Content-Disposition: form-data; name="{k}"; filename="{filename}"'.encode("utf-8"))
        body.append(f"Content-Type: {content_type}".encode("utf-8"))
        body.append(b"")
        body.append(content)
        
    body.append(f"--{boundary}--".encode("utf-8"))
    body.append(b"")
    
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    return b"\r\n".join(body), headers

def run_tests():
    print("=== STARTING STEP 13 CODING & RESUME AUTOMATED VERIFICATION ===")

    # 1. Test Health Root
    status, res = make_request(f"{API_BASE}/")
    assert status == 200, f"Root endpoint failed: {res}"
    print("[OK] Health check passed.")

    # 2. Test Resume Upload with document_type = RESUME
    sample_pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "pdfs", "my-notes.pdf"))
    if not os.path.exists(sample_pdf_path):
        sample_pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "pdfs", "test_sql_guide.pdf"))

    print(f"Testing resume upload with PDF: {sample_pdf_path}")
    with open(sample_pdf_path, "rb") as f:
        pdf_bytes = f.read()

    body_bytes, headers = encode_multipart(
        fields={"document_type": "RESUME"},
        files={"file": ("my_resume.pdf", pdf_bytes, "application/pdf")}
    )

    status, res_data = make_request(f"{API_BASE}/upload", method="POST", data=body_bytes, headers=headers)
    assert status == 200, f"Resume upload failed: {res_data}"
    doc_id = res_data.get("document_id")
    print(f"[OK] Resume Upload Successful. document_id={doc_id}, processing_status={res_data.get('processing_status')}")

    # 3. Test Resume Analysis endpoint
    status, analysis = make_request(f"{API_BASE}/resume/{doc_id}/analysis")
    assert status == 200, f"Resume analysis failed: {analysis}"
    assert "resume_data" in analysis, "Analysis missing resume_data"
    print("[OK] Resume Analysis endpoint passed.")

    # 4. Test Coding Problem Generation
    print("Testing Coding Problem Generation...")
    status, prob = make_request(f"{API_BASE}/coding/problem/generate", method="POST", data={
        "language": "Python",
        "difficulty": "easy",
        "topic": "arrays",
        "role": "Backend Engineer",
        "document_id": doc_id,
        "include_notes_rag": True
    })
    assert status == 200, f"Problem generation failed: {prob}"
    assert "title" in prob and "statement" in prob, "Problem response missing title/statement"
    print(f"[OK] Generated Problem: '{prob.get('title')}'")

    # 5. Test Python Execution (Subprocess)
    print("Testing Python Code Execution...")
    python_code = "print('Hello from Python Execution!')"
    status, exec_res = make_request(f"{API_BASE}/coding/execute", method="POST", data={
        "language": "Python",
        "code": python_code
    })
    assert status == 200, f"Python execution failed: {exec_res}"
    assert exec_res.get("success") is True, f"Python execution returned unsuccessful: {exec_res}"
    assert "Hello from Python Execution!" in exec_res.get("stdout"), "Python stdout mismatch"
    print("[OK] Python Code Execution passed.")

    # 6. Test SQL Execution (Subprocess isolated SQLite)
    print("Testing SQL Execution...")
    sql_code = "SELECT 1 + 1 AS result;"
    status, sql_res = make_request(f"{API_BASE}/coding/execute", method="POST", data={
        "language": "SQL",
        "code": sql_code
    })
    assert status == 200, f"SQL execution failed: {sql_res}"
    assert sql_res.get("success") is True, f"SQL execution unsuccessful: {sql_res}"
    print("[OK] SQL Execution passed.")

    # 7. Test JavaScript Node.js Execution
    print("Testing JS Execution...")
    js_code = "console.log('JS execution test');"
    status, js_res = make_request(f"{API_BASE}/coding/execute", method="POST", data={
        "language": "JavaScript",
        "code": js_code
    })
    assert status == 200, f"JS execution endpoint failed: {js_res}"
    if js_res.get("status") == "NODE_MISSING":
        print("[OK] Node.js missing notice handled gracefully.")
    else:
        assert js_res.get("success") is True, f"JS execution unsuccessful: {js_res}"
        print("[OK] JS Node.js Execution passed.")

    # 8. Test Java Execution / Graceful JDK missing check
    print("Testing Java Execution...")
    java_code = "public class Solution { public static void main(String[] args) { System.out.println(\"Java Test\"); } }"
    status, java_res = make_request(f"{API_BASE}/coding/execute", method="POST", data={
        "language": "Java",
        "code": java_code
    })
    assert status == 200, f"Java execution endpoint failed: {java_res}"
    if java_res.get("status") == "JAVA_MISSING":
        assert "Java compiler/runtime is not installed on this machine." in java_res.get("stderr"), "Java missing message mismatch"
        print("[OK] Java JDK missing handled gracefully with friendly notice (not system error).")
    else:
        print("[OK] Java Execution passed.")

    # 9. Test Coding Evaluation & Mana-Style Explanation
    print("Testing Coding Evaluation & Mana-Style Explanation...")
    status, eval_res = make_request(f"{API_BASE}/coding/evaluate", method="POST", data={
        "language": "Python",
        "code": "def solution(arr):\n    return sum(arr)\n\nprint(solution([1, 2, 3]))",
        "problem_statement": "Sum all elements in an integer array."
    })
    assert status == 200, f"Evaluation failed: {eval_res}"
    assert "mana_explanation" in eval_res, "Evaluation missing mana_explanation"
    assert "Simple ga cheppalante" in eval_res.get("mana_explanation"), "Mana explanation missing Telugu-English phrase"
    print(f"[OK] Coding Evaluation passed. Mana Explanation: {eval_res.get('mana_explanation')}")

    # 10. RAG Regression Verification
    print("Testing RAG /ask regression...")
    status, ask_res = make_request(f"{API_BASE}/ask", method="POST", data={"query": "What is FAISS?", "top_k": 2})
    assert status == 200, f"RAG ask failed: {ask_res}"
    assert "answer" in ask_res, "RAG answer missing"
    print("[OK] RAG /ask regression test passed.")

    print("\nALL STEP 13 BACKEND VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()

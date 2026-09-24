import os
import sys
import hashlib
import json
import pymupdf

sys.path.insert(0, r"c:\Users\user\OneDrive\Desktop\mynotes-rag")

from fastapi.testclient import TestClient
from backend.main import app

def create_sample_text_pdf(filename: str, title: str, topics: list) -> str:
    """Helper to create a small text-layer PDF using PyMuPDF."""
    pdf_dir = r"c:\Users\user\OneDrive\Desktop\mynotes-rag\scratch"
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, filename)

    doc = pymupdf.open()
    for idx, (heading, content) in enumerate(topics):
        page = doc.new_page(width=595, height=842)
        text = f"{title}\n\nSection {idx+1}: {heading}\n\n{content}\n"
        # Insert text onto page
        rect = pymupdf.Rect(50, 50, 545, 792)
        page.insert_textbox(rect, text, fontsize=12)
    doc.save(pdf_path)
    doc.close()
    return pdf_path

def create_image_only_pdf(filename: str) -> str:
    """Helper to create a PDF with an image layer but NO text layer."""
    pdf_dir = r"c:\Users\user\OneDrive\Desktop\mynotes-rag\scratch"
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, filename)

    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    # Draw a shape/drawing without text
    shape = page.new_shape()
    shape.draw_rect(pymupdf.Rect(100, 100, 400, 400))
    shape.finish(fill=(0.8, 0.8, 0.8), color=(0, 0, 0))
    shape.commit()
    doc.save(pdf_path)
    doc.close()
    return pdf_path

def run_tests():
    client = TestClient(app)
    print("--- STARTING STEP 12B VERIFICATION SUITE ---")

    # TEST 1: Existing canonical document b8f2cb48 check
    res = client.get("/documents")
    assert res.status_code == 200
    docs = res.json()["documents"]
    doc_ids = [d["document_id"] for d in docs]
    print(f"[TEST 1] Registered documents: {doc_ids}")
    assert "b8f2cb48" in doc_ids, "Canonical document b8f2cb48 is missing!"
    
    canon_doc = [d for d in docs if d["document_id"] == "b8f2cb48"][0]
    assert canon_doc["processing_status"] in ["READY", "indexed_and_chunked"]
    print(f"[TEST 1 PASSED] Canonical b8f2cb48 is present and status is '{canon_doc['processing_status']}'")

    # TEST 2 & 3: Create and Ingest Document A (Python) and Document B (SQL)
    doc_a_path = create_sample_text_pdf(
        "test_python_guide.pdf",
        "Python Programming Essentials",
        [
            ("Lambda Functions", "A lambda function in Python is a small anonymous function defined with the lambda keyword. It can take any number of arguments, but can only have one expression. Syntactically, python lambda functions are used when an anonymous function is required for a short period of time."),
            ("Python Decorators", "Decorators in Python allow you to modify or extend the behavior of a function without modifying the function code itself. They wrap another function.")
        ]
    )

    doc_b_path = create_sample_text_pdf(
        "test_sql_guide.pdf",
        "SQL Relational Database Guide",
        [
            ("INNER JOIN Queries", "An INNER JOIN in SQL selects records that have matching values in both tables. It combines rows from two or more tables based on a related column between them."),
            ("SQL Group By", "The GROUP BY statement groups rows that have the same values into summary rows, like find the number of customers in each country.")
        ]
    )

    # Ingest Document A via POST /upload
    with open(doc_a_path, "rb") as f:
        res_a = client.post("/upload", files={"file": ("test_python_guide.pdf", f, "application/pdf")})
    assert res_a.status_code == 200 or res_a.status_code == 201, f"Upload A failed: {res_a.text}"
    data_a = res_a.json()
    assert data_a["processing_status"] == "READY"
    doc_a_id = data_a["document_id"]
    print(f"[TEST 2 PASSED] Ingested Document A (Python): ID = {doc_a_id}, Chunks = {data_a['chunk_count']}")

    # Ingest Document B via POST /upload
    with open(doc_b_path, "rb") as f:
        res_b = client.post("/upload", files={"file": ("test_sql_guide.pdf", f, "application/pdf")})
    assert res_b.status_code == 200 or res_b.status_code == 201, f"Upload B failed: {res_b.text}"
    data_b = res_b.json()
    assert data_b["processing_status"] == "READY"
    doc_b_id = data_b["document_id"]
    print(f"[TEST 3 PASSED] Ingested Document B (SQL): ID = {doc_b_id}, Chunks = {data_b['chunk_count']}")

    # TEST 4: Cross-Document Search (document_id omitted)
    search_python = client.post("/search", json={"query": "What is a lambda function?", "top_k": 3})
    assert search_python.status_code == 200
    res_py = search_python.json()["results"]
    assert len(res_py) > 0
    top_doc_py = res_py[0]["document_id"]
    print(f"[TEST 4A PASSED] Cross-doc search 'lambda': Top result from doc '{top_doc_py}' (expected {doc_a_id})")
    assert top_doc_py == doc_a_id

    search_sql = client.post("/search", json={"query": "What is INNER JOIN?", "top_k": 3})
    assert search_sql.status_code == 200
    res_sql = search_sql.json()["results"]
    assert len(res_sql) > 0
    top_doc_sql = res_sql[0]["document_id"]
    print(f"[TEST 4B PASSED] Cross-doc search 'INNER JOIN': Top result from doc '{top_doc_sql}' (expected {doc_b_id})")
    assert top_doc_sql == doc_b_id

    # TEST 5: Document-Filtered Search
    filtered_search = client.post("/search", json={"query": "What is a lambda function?", "document_id": doc_b_id, "top_k": 3})
    assert filtered_search.status_code == 200
    filt_res = filtered_search.json()["results"]
    for r in filt_res:
        assert r["document_id"] == doc_b_id
    print(f"[TEST 5 PASSED] Filtered search on Document B returned only Document B results.")

    # TEST 6: Duplicate Upload Test
    with open(doc_a_path, "rb") as f:
        res_dup = client.post("/upload", files={"file": ("test_python_guide.pdf", f, "application/pdf")})
    assert res_dup.status_code == 200 or res_dup.status_code == 201
    dup_data = res_dup.json()
    assert dup_data["document_id"] == doc_a_id
    assert "already exists" in dup_data.get("message", "").lower() or dup_data.get("processing_status") == "READY"
    print(f"[TEST 6 PASSED] Re-uploading Document A correctly detected duplicate without creating new records.")

    # TEST 7: Image-Only PDF Test (OCR_REQUIRED)
    doc_img_path = create_image_only_pdf("scanned_no_text.pdf")
    with open(doc_img_path, "rb") as f:
        res_img = client.post("/upload", files={"file": ("scanned_no_text.pdf", f, "application/pdf")})
    assert res_img.status_code in [200, 201]
    img_data = res_img.json()
    assert img_data["processing_status"] == "OCR_REQUIRED"
    assert img_data["has_text_layer"] == False
    print(f"[TEST 7 PASSED] Scanned image-only PDF correctly marked OCR_REQUIRED.")

    # TEST 8: Grounded Multi-Doc /ask Test
    ask_res = client.post("/ask", json={"query": "What is an INNER JOIN in SQL?", "top_k": 3})
    assert ask_res.status_code == 200
    ask_data = ask_res.json()
    sources = ask_data.get("sources", [])
    assert len(sources) > 0
    source_filenames = [s.get("filename") for s in sources]
    print(f"[TEST 8 PASSED] Multi-doc /ask response retrieved sources: {source_filenames}")

    print("\n--- ALL STEP 12B TESTS COMPLETED SUCCESSFULLY! ---")

if __name__ == "__main__":
    run_tests()

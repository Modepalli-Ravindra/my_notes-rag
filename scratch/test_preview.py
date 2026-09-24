import os
import hashlib
import sys

# Add project root to python path
sys.path.insert(0, r"c:\Users\user\OneDrive\Desktop\mynotes-rag")

from fastapi.testclient import TestClient
from backend.main import app

def get_pdf_sha256(pdf_path):
    h = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def test_preview_feature():
    pdf_path = r"c:\Users\user\OneDrive\Desktop\mynotes-rag\data\pdfs\my-notes.pdf"
    
    # 1. Initial SHA-256 check
    initial_sha = get_pdf_sha256(pdf_path)
    print(f"[TEST 1] Initial SHA-256: {initial_sha}")
    
    client = TestClient(app)
    
    # 2. Test valid page renderings: 1, 2, 10, 50, 167
    test_pages = [1, 2, 10, 50, 167]
    for page in test_pages:
        res = client.get(f"/documents/b8f2cb48/pages/{page}/image")
        assert res.status_code == 200, f"Failed on page {page}: {res.status_code}"
        assert res.headers["content-type"] == "image/png", f"Invalid media type: {res.headers['content-type']}"
        assert res.headers["x-document-id"] == "b8f2cb48"
        assert res.headers["x-page-number"] == str(page)
        assert res.headers["x-total-pages"] == "167"
        assert len(res.content) > 1000, f"Image bytes too small for page {page}"
        print(f"[TEST 2] Page {page} rendered successfully! Size: {len(res.content)} bytes")
        
    # 3. Test out of bounds pages: 0 and 168
    res_low = client.get("/documents/b8f2cb48/pages/0/image")
    assert res_low.status_code == 400, f"Expected 400 for page 0, got {res_low.status_code}"
    print(f"[TEST 3A] Page 0 correctly returned 400 Bad Request: {res_low.json()}")
    
    res_high = client.get("/documents/b8f2cb48/pages/168/image")
    assert res_high.status_code == 400, f"Expected 400 for page 168, got {res_high.status_code}"
    print(f"[TEST 3B] Page 168 correctly returned 400 Bad Request: {res_high.json()}")

    # 4. Test invalid document ID
    res_invalid = client.get("/documents/invalid_doc_id/pages/1/image")
    assert res_invalid.status_code == 404, f"Expected 404 for invalid doc ID, got {res_invalid.status_code}"
    print(f"[TEST 4] Invalid doc ID correctly returned 404 Not Found: {res_invalid.json()}")

    # 5. Check SHA-256 after rendering to verify PDF is unmodified
    final_sha = get_pdf_sha256(pdf_path)
    assert initial_sha == final_sha, "PDF SHA-256 hash changed!"
    print(f"[TEST 5] PDF SHA-256 hash verified unchanged!")

    # 6. Check for any leak of .png files in project directory
    root_dir = r"c:\Users\user\OneDrive\Desktop\mynotes-rag"
    png_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        if "venv" in dirpath or "node_modules" in dirpath or ".next" in dirpath:
            continue
        for f in filenames:
            if f.lower().endswith(".png"):
                png_files.append(os.path.join(dirpath, f))
    assert len(png_files) == 0, f"Found permanent PNG files on disk: {png_files}"
    print(f"[TEST 6] Confirmed 0 permanent PNG files on disk!")

    print("\n--- ALL BACKEND PREVIEW TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    test_preview_feature()

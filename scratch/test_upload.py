import time
import os
import sys
from fastapi.testclient import TestClient

# Add workspace to path
sys.path.insert(0, os.path.abspath('.'))

from backend.main import app

def test_real_pdf_upload():
    client = TestClient(app)
    pdf_path = "data/pdfs/my-notes.pdf"
    
    print(f"File size: {os.path.getsize(pdf_path) / (1024*1024):.2f} MB")
    start = time.time()
    
    with open(pdf_path, "rb") as f:
        response = client.post("/upload", files={"file": ("DocScanner_2026.pdf", f, "application/pdf")})
        
    elapsed = time.time() - start
    print(f"Elapsed time: {elapsed:.2f} seconds")
    print(f"Status code: {response.status_code}")
    data = response.json()
    print("Response JSON:")
    for k, v in data.items():
        print(f"  {k}: {v}")
        
    assert response.status_code == 201
    assert data["success"] is True
    assert data["page_count"] == 167
    assert data["pages_with_text"] == 167
    assert data["pages_with_images"] == 167
    assert data["has_text_layer"] is True
    print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_real_pdf_upload()

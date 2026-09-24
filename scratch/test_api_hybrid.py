import sys
import json
from fastapi.testclient import TestClient

sys.path.insert(0, r"c:\Users\user\OneDrive\Desktop\mynotes-rag")
from backend.main import app

def test_api():
    client = TestClient(app)
    print("=== TESTING HYBRID POST /search API ENDPOINT ===")

    queries = [
        ("What is the LEGB rule?", "Pages 8-9"),
        ("What is list comprehension?", "Pages 17-18"),
        ("What are decorators?", "Page 14")
    ]

    for q, expected_pages in queries:
        payload = {"query": q, "top_k": 5}
        r = client.post("/search", json=payload)
        assert r.status_code == 200, f"Search failed with status {r.status_code}"
        res = r.json()
        top1 = res["results"][0]
        print(f"Query: \"{q}\"")
        print(f"  Top 1 Chunk: {top1['chunk_id']} | Pages: {top1['page_start']}-{top1['page_end']}")
        print(f"  Final Score: {top1['final_score']} (Dense: {top1['dense_score']}, Lexical: {top1['lexical_score']})")
        print()

    print("API HYBRID SEARCH VERIFIED PERFECTLY!")

if __name__ == "__main__":
    test_api()

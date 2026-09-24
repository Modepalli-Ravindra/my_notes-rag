import os
import sys
import json

sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, r"c:\Users\user\OneDrive\Desktop\mynotes-rag")
from backend.services.vector_store import VectorStore

def main():
    print("=== 1. Building / Loading FAISS Index ===", flush=True)
    vs = VectorStore(document_id="b8f2cb48")
    vs.load_or_build_index()

    manifest = vs.manifest
    print("Manifest Info:", flush=True)
    print(json.dumps(manifest, indent=2), flush=True)

    print(f"\nTotal Chunks Embedded: {len(vs.chunk_metadata)}", flush=True)
    print(f"FAISS Vector Count: {vs.index.ntotal}", flush=True)
    print(f"Embedding Dimension: {vs.index.d}", flush=True)

    test_queries = [
        "What is a variable in Python?",
        "Explain mutable and immutable objects.",
        "What is the LEGB rule?",
        "What is a lambda function?",
        "What are decorators?",
        "What is exception handling?",
        "What are iterators and generators?",
        "What is list comprehension?"
    ]

    print("\n" + "=" * 65, flush=True)
    print("=== RETRIEVAL QUALITY EVALUATION REPORT (8 TEST QUERIES) ===", flush=True)
    print("=" * 65 + "\n", flush=True)

    for idx, q in enumerate(test_queries, 1):
        results = vs.search(q, top_k=5)
        print(f"Query {idx}: \"{q}\"", flush=True)
        print("-" * 55, flush=True)
        for res in results:
            p_str = f"Page {res['page_start']}" if res['page_start'] == res['page_end'] else f"Pages {res['page_start']}-{res['page_end']}"
            snippet = res['text'].replace('\n', ' ')[:130]
            print(f"  Rank {res['rank']}: Score {res['score']:.4f} | {p_str} | Chunk {res['chunk_id']}", flush=True)
            print(f"          Snippet: {snippet}...", flush=True)
        print(flush=True)

    print("=" * 65, flush=True)
    print("=== 2. Testing Persistence / Reload without Re-embedding ===", flush=True)
    print("=" * 65, flush=True)
    vs2 = VectorStore(document_id="b8f2cb48")
    vs2.load_or_build_index()
    assert vs2.loaded_from_cache is True, "Expected index to load from disk cache"
    print("SUCCESS: Persistent FAISS index reloaded directly from disk without re-embedding!", flush=True)

if __name__ == "__main__":
    main()

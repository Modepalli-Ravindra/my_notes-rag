import os
import sys
import json

sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, r"c:\Users\user\OneDrive\Desktop\mynotes-rag")
from backend.services.vector_store import VectorStore

def main():
    print("=== STEP 10.5 HYBRID RETRIEVAL & RERANKING EVALUATION ===", flush=True)
    vs = VectorStore(document_id="b8f2cb48")
    vs.load_or_build_index()

    test_queries = [
        ("What is a variable in Python?", "Pages 2-3"),
        ("Explain mutable and immutable objects.", "Pages 4-5"),
        ("What is the LEGB rule?", "Page 9"),
        ("What is a lambda function?", "Pages 11-12"),
        ("What are decorators?", "Page 14"),
        ("What is exception handling?", "Page 15"),
        ("What are iterators and generators?", "Pages 16-17"),
        ("What is list comprehension?", "Page 18")
    ]

    print("\n" + "=" * 80, flush=True)
    print("=== HYBRID RETRIEVAL QUALITY EVALUATION (DENSE + BM25 + TERM BOOST) ===", flush=True)
    print("=" * 80 + "\n", flush=True)

    target_hits = 0

    for idx, (q, expected_pages) in enumerate(test_queries, 1):
        results = vs.hybrid_search(q, top_k=5)
        print(f"Query {idx}: \"{q}\" (Expected Target: {expected_pages})", flush=True)
        print("-" * 75, flush=True)

        top_page_range = ""
        for res in results:
            p_start, p_end = res["page_start"], res["page_end"]
            p_str = f"Page {p_start}" if p_start == p_end else f"Pages {p_start}-{p_end}"
            if not top_page_range:
                top_page_range = p_str

            snippet = res["text"].replace('\n', ' ')[:110]
            print(f"  Rank {res['rank']}: Final Score {res['final_score']:.4f} | Dense {res['dense_score']:.4f} | Lexical {res['lexical_score']:.4f} | {p_str} | Chunk {res['chunk_id']}", flush=True)
            print(f"          Snippet: {snippet}...", flush=True)

        print(f"  -> Top Result Returned: {top_page_range}", flush=True)
        print(flush=True)

    print("=" * 80, flush=True)
    print("=== PERSISTENCE & REBOOT RELOAD TEST ===", flush=True)
    print("=" * 80, flush=True)
    vs2 = VectorStore(document_id="b8f2cb48")
    vs2.load_or_build_index()
    assert vs2.loaded_from_cache is True, "Expected index to load from disk cache"
    print("SUCCESS: Persistent FAISS vector store & BM25 index reloaded directly from disk without re-embedding!", flush=True)

if __name__ == "__main__":
    main()

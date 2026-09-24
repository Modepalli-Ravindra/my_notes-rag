import os
import hashlib
import json
import pymupdf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(BASE_DIR, "data", "pdfs")
INDEX_DIR = os.path.join(BASE_DIR, "data", "extracted_text")

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(INDEX_DIR, exist_ok=True)

def compute_sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def inspect_and_extract_pdf(pdf_path: str, document_id: str, sha256_hash: str, stored_filename: str, original_filename: str):
    doc = pymupdf.open(pdf_path)
    page_count = len(doc)
    pages_with_text = 0
    pages_with_images = 0
    extracted_pages = []

    for i in range(page_count):
        page = doc[i]
        text = page.get_text() or ""
        has_text = bool(text.strip())
        images = page.get_images()
        has_image = bool(images and len(images) > 0)

        if has_text:
            pages_with_text += 1
        if has_image:
            pages_with_images += 1

        extracted_pages.append({
            "page_num": i + 1,
            "text": text,
            "has_text": has_text,
            "has_image": has_image
        })

    doc.close()

    has_text_layer = (pages_with_text > 0)
    file_size = os.path.getsize(pdf_path)
    rel_file_path = os.path.relpath(pdf_path, BASE_DIR).replace("\\", "/")

    doc_index = {
        "document_id": document_id,
        "sha256": sha256_hash,
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "pdf_path": pdf_path,
        "file_path": rel_file_path,
        "file_size": file_size,
        "page_count": page_count,
        "has_text_layer": has_text_layer,
        "pages_with_text": pages_with_text,
        "pages_with_images": pages_with_images,
        "pages": extracted_pages
    }

    index_path = os.path.join(INDEX_DIR, f"{document_id}.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(doc_index, f, ensure_ascii=False, indent=2)

    return doc_index

def sync_and_deduplicate():
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf") and not f.startswith("temp_")]
    print(f"Initial PDF files in {PDF_DIR}: {pdf_files}")

    # Group files by SHA256 hash
    hash_to_files = {}
    for filename in pdf_files:
        path = os.path.join(PDF_DIR, filename)
        h = compute_sha256_file(path)
        hash_to_files.setdefault(h, []).append(filename)

    for h, files in hash_to_files.items():
        print(f"\nHash: {h[:12]}... -> Files: {files}")
        # Prefer 'my-notes.pdf' as canonical
        canonical_filename = files[0]
        for f in files:
            if f.lower() == "my-notes.pdf":
                canonical_filename = f
                break

        canonical_path = os.path.join(PDF_DIR, canonical_filename)
        doc_id = h[:8]

        # Remove duplicate files
        for f in files:
            if f != canonical_filename:
                dup_path = os.path.join(PDF_DIR, f)
                os.remove(dup_path)
                print(f"Removed duplicate PDF: {dup_path}")

        # Extract and save metadata for canonical file
        meta = inspect_and_extract_pdf(
            pdf_path=canonical_path,
            document_id=doc_id,
            sha256_hash=h,
            stored_filename=canonical_filename,
            original_filename=canonical_filename
        )
        print(f"Canonical PDF registered: {canonical_filename} (Doc ID: {doc_id}, Pages: {meta['page_count']})")

    # Clean up obsolete index json files
    valid_ids = {h[:8] for h in hash_to_files.keys()}
    for index_name in os.listdir(INDEX_DIR):
        if index_name.endswith(".json"):
            idx_id = os.path.splitext(index_name)[0]
            if idx_id not in valid_ids:
                obsolete_path = os.path.join(INDEX_DIR, index_name)
                os.remove(obsolete_path)
                print(f"Removed obsolete index JSON: {obsolete_path}")

if __name__ == "__main__":
    sync_and_deduplicate()

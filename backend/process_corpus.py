import os
import re
import json
import pymupdf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(BASE_DIR, "data", "pdfs")
INDEX_DIR = os.path.join(BASE_DIR, "data", "extracted_text")
CHUNKS_DIR = os.path.join(BASE_DIR, "data", "chunks")
os.makedirs(CHUNKS_DIR, exist_ok=True)


def normalize_text_conservative(text: str) -> str:
    """
    Conservative text normalization:
    - Removes non-printable control characters
    - Normalizes line endings (\r\n -> \n)
    - Normalizes horizontal whitespace (spaces/tabs to single space per line)
    - Preserves paragraph boundaries, punctuation, numbers, Python/SQL code, math, and OCR errors
    """
    if not text:
        return ""

    # Remove unprintable control characters except \n and \t
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

    # Standardize line breaks
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Normalize horizontal spaces/tabs on each line
    lines = text.split('\n')
    cleaned_lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in lines]
    text = '\n'.join(cleaned_lines)

    # Reduce 3+ consecutive newlines to 2 newlines (preserving paragraph boundaries)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def calculate_quality_metrics(raw_text: str, norm_text: str):
    """
    Calculate simple heuristic quality indicators per page.
    Stored only as heuristic flags (NOT true OCR confidence scores).
    """
    word_count = len(norm_text.split())
    char_count = len(norm_text)

    empty_text = (word_count == 0)
    very_short_text = (word_count < 10)

    # Calculate unusual symbol ratio (non-alphanumeric, non-space, non-standard punctuation)
    if char_count > 0:
        standard_chars = re.compile(r'[a-zA-Z0-9\s.,!?;:\'"\-\(\)\[\]\{\}\/\*\+\=\<\>\#\$\@\%\&\_\\]')
        non_std_count = sum(1 for c in norm_text if not standard_chars.match(c))
        unusual_symbol_ratio = round(non_std_count / char_count, 4)
    else:
        unusual_symbol_ratio = 0.0

    # Calculate repeated character ratio (e.g. "aaa", "---", "...")
    if char_count > 0:
        repeated_count = sum(len(m.group(0)) for m in re.finditer(r'(.)\1{2,}', norm_text))
        repeated_character_ratio = round(repeated_count / char_count, 4)
    else:
        repeated_character_ratio = 0.0

    return {
        "empty_text": empty_text,
        "very_short_text": very_short_text,
        "unusual_symbol_ratio": unusual_symbol_ratio,
        "repeated_character_ratio": repeated_character_ratio
    }


def chunk_pages(document_id: str, pages_data: list):
    """
    Create semantic/page-aware chunks:
    - Target ~300-600 words per chunk
    - Modest overlap (~50-100 words) when appropriate
    - Maintain page boundaries (page_start, page_end)
    - Short pages remain as single chunks or grouped naturally across adjacent pages
    - Long pages split into multiple chunks along paragraph boundaries
    """
    chunks = []
    current_page_start = None
    current_page_end = None
    accumulated_raw_paragraphs = []
    accumulated_norm_paragraphs = []
    accumulated_words = 0

    def finalize_chunk(p_start, p_end, raw_paras, norm_paras, chunk_index):
        if not norm_paras:
            return None

        raw_chunk_text = "\n\n".join(raw_paras)
        norm_chunk_text = "\n\n".join(norm_paras)
        word_cnt = len(norm_chunk_text.split())

        if p_start == p_end:
            cid = f"{document_id}_p{p_start}_c{chunk_index}"
        else:
            cid = f"{document_id}_p{p_start}_p{p_end}_c{chunk_index}"

        return {
            "chunk_id": cid,
            "document_id": document_id,
            "page_start": p_start,
            "page_end": p_end,
            "raw_text": raw_chunk_text,
            "normalized_text": norm_chunk_text,
            "word_count": word_cnt,
            "character_count": len(norm_chunk_text)
        }

    page_chunk_counts = {}

    for page in pages_data:
        p_num = page["page_number"]
        p_raw = page["raw_text"]
        p_norm = page["normalized_text"]
        p_words = page["word_count"]

        if not p_norm:
            # Handle empty page as a standalone small chunk if needed or skip
            c_idx = page_chunk_counts.get(p_num, 0) + 1
            page_chunk_counts[p_num] = c_idx
            empty_chunk = {
                "chunk_id": f"{document_id}_p{p_num}_c{c_idx}",
                "document_id": document_id,
                "page_start": p_num,
                "page_end": p_num,
                "raw_text": p_raw,
                "normalized_text": p_norm,
                "word_count": 0,
                "character_count": 0
            }
            chunks.append(empty_chunk)
            continue

        # Split long page into paragraphs
        paragraphs_raw = [p for p in p_raw.split('\n\n') if p.strip()] or [p_raw]
        paragraphs_norm = [p for p in p_norm.split('\n\n') if p.strip()] or [p_norm]

        # If a single page is very long (>600 words), chunk it internally
        if p_words > 650:
            # Flush any accumulated prior buffer
            if accumulated_norm_paragraphs:
                c_idx = page_chunk_counts.get(current_page_start, 0) + 1
                page_chunk_counts[current_page_start] = c_idx
                chk = finalize_chunk(current_page_start, current_page_end, accumulated_raw_paragraphs, accumulated_norm_paragraphs, c_idx)
                if chk:
                    chunks.append(chk)
                accumulated_raw_paragraphs = []
                accumulated_norm_paragraphs = []
                accumulated_words = 0
                current_page_start = None

            # Split paragraphs of this long page into chunks of ~300-500 words
            sub_raw = []
            sub_norm = []
            sub_words = 0

            for raw_p, norm_p in zip(paragraphs_raw, paragraphs_norm):
                w_len = len(norm_p.split())
                if sub_words + w_len > 500 and sub_words >= 250:
                    c_idx = page_chunk_counts.get(p_num, 0) + 1
                    page_chunk_counts[p_num] = c_idx
                    chk = finalize_chunk(p_num, p_num, sub_raw, sub_norm, c_idx)
                    if chk:
                        chunks.append(chk)

                    # Modest overlap: keep last paragraph if helpful
                    if len(sub_norm) > 1 and len(sub_norm[-1].split()) <= 100:
                        sub_raw = [sub_raw[-1], raw_p]
                        sub_norm = [sub_norm[-1], norm_p]
                        sub_words = len(sub_norm[0].split()) + w_len
                    else:
                        sub_raw = [raw_p]
                        sub_norm = [norm_p]
                        sub_words = w_len
                else:
                    sub_raw.append(raw_p)
                    sub_norm.append(norm_p)
                    sub_words += w_len

            if sub_norm:
                c_idx = page_chunk_counts.get(p_num, 0) + 1
                page_chunk_counts[p_num] = c_idx
                chk = finalize_chunk(p_num, p_num, sub_raw, sub_norm, c_idx)
                if chk:
                    chunks.append(chk)

            continue

        # Normal/short page: accumulate until target ~300-500 words or flush if buffer gets large
        if accumulated_words + p_words > 550:
            c_idx = page_chunk_counts.get(current_page_start, 0) + 1
            page_chunk_counts[current_page_start] = c_idx
            chk = finalize_chunk(current_page_start, current_page_end, accumulated_raw_paragraphs, accumulated_norm_paragraphs, c_idx)
            if chk:
                chunks.append(chk)

            current_page_start = p_num
            current_page_end = p_num
            accumulated_raw_paragraphs = [p_raw]
            accumulated_norm_paragraphs = [p_norm]
            accumulated_words = p_words
        else:
            if not current_page_start:
                current_page_start = p_num
            current_page_end = p_num
            accumulated_raw_paragraphs.append(p_raw)
            accumulated_norm_paragraphs.append(p_norm)
            accumulated_words += p_words

    # Final flush
    if accumulated_norm_paragraphs:
        c_idx = page_chunk_counts.get(current_page_start, 0) + 1
        page_chunk_counts[current_page_start] = c_idx
        chk = finalize_chunk(current_page_start, current_page_end, accumulated_raw_paragraphs, accumulated_norm_paragraphs, c_idx)
        if chk:
            chunks.append(chk)

    return chunks


def process_document(document_id: str = "b8f2cb48"):
    pdf_path = os.path.join(PDF_DIR, "my-notes.pdf")
    index_json_path = os.path.join(INDEX_DIR, f"{document_id}.json")

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Canonical PDF not found at {pdf_path}")

    # Extract text from PDF using PyMuPDF
    doc = pymupdf.open(pdf_path)
    page_count = len(doc)
    pages_processed = []
    total_words = 0

    for i in range(page_count):
        page = doc[i]
        page_num = i + 1
        raw_text = page.get_text() or ""
        norm_text = normalize_text_conservative(raw_text)

        has_text = bool(norm_text.strip())
        char_cnt = len(norm_text)
        word_cnt = len(norm_text.split())
        total_words += word_cnt

        q_metrics = calculate_quality_metrics(raw_text, norm_text)

        pages_processed.append({
            "document_id": document_id,
            "page_number": page_num,
            "raw_text": raw_text,
            "normalized_text": norm_text,
            "has_text": has_text,
            "character_count": char_cnt,
            "word_count": word_cnt,
            "has_image": bool(page.get_images() and len(page.get_images()) > 0),
            "quality_metrics": q_metrics
        })

    doc.close()

    # Generate page-aware semantic chunks
    chunks = chunk_pages(document_id, pages_processed)

    # Save chunks to JSONL file
    jsonl_path = os.path.join(CHUNKS_DIR, f"{document_id}.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    # Update index metadata JSON
    pages_with_text_count = sum(1 for p in pages_processed if p["has_text"])
    pages_with_images_count = sum(1 for p in pages_processed if p["has_image"])

    meta_doc = {
        "document_id": document_id,
        "sha256": "b8f2cb48087ae8ca195d25c08499cadbf2a99de72535afacc34b92ac0de8af61",
        "original_filename": "my-notes.pdf",
        "stored_filename": "my-notes.pdf",
        "pdf_path": pdf_path,
        "file_size": os.path.getsize(pdf_path),
        "page_count": page_count,
        "pages_with_text": pages_with_text_count,
        "pages_with_images": pages_with_images_count,
        "has_text_layer": (pages_with_text_count > 0),
        "chunk_count": len(chunks),
        "total_words": total_words,
        "processing_status": "indexed_and_chunked",
        "pages": pages_processed
    }

    with open(index_json_path, "w", encoding="utf-8") as f:
        json.dump(meta_doc, f, ensure_ascii=False, indent=2)

    print(f"Successfully processed {page_count} pages and created {len(chunks)} chunks for document '{document_id}'.")
    print(f"Chunks saved to: {jsonl_path}")
    print(f"Metadata index updated: {index_json_path}")
    return meta_doc, chunks


if __name__ == "__main__":
    process_document("b8f2cb48")

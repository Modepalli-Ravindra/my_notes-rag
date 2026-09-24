import os
import json

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CHUNKS_DIR = os.path.join(ROOT_DIR, "data", "chunks")
os.makedirs(CHUNKS_DIR, exist_ok=True)


def chunk_pages(document_id: str, pages_data: list) -> list[dict]:
    """
    Create semantic/page-aware chunks:
    - Target ~300-600 words per chunk
    - Modest overlap (~50-100 words)
    - Preserve page boundaries (page_start, page_end)
    - Preserve document_id and unique chunk_id
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
            continue

        paragraphs_raw = [p for p in p_raw.split('\n\n') if p.strip()] or [p_raw]
        paragraphs_norm = [p for p in p_norm.split('\n\n') if p.strip()] or [p_norm]

        if p_words > 650:
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

    if accumulated_norm_paragraphs:
        c_idx = page_chunk_counts.get(current_page_start, 0) + 1
        page_chunk_counts[current_page_start] = c_idx
        chk = finalize_chunk(current_page_start, current_page_end, accumulated_raw_paragraphs, accumulated_norm_paragraphs, c_idx)
        if chk:
            chunks.append(chk)

    return chunks


def save_chunks_to_jsonl(document_id: str, chunks: list[dict]) -> str:
    """Save chunk list to data/chunks/<document_id>.jsonl."""
    jsonl_path = os.path.join(CHUNKS_DIR, f"{document_id}.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    return jsonl_path

import re
import pymupdf


def normalize_text_conservative(text: str) -> str:
    """
    Conservative text normalization:
    - Removes non-printable control characters
    - Normalizes line endings (\r\n -> \n)
    - Normalizes horizontal whitespace (spaces/tabs to single space per line)
    - Preserves paragraph boundaries, punctuation, numbers, Python/SQL code, math, and technical terminology
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


def calculate_quality_metrics(raw_text: str, norm_text: str) -> dict:
    """
    Calculate heuristic quality indicators per page.
    """
    word_count = len(norm_text.split())
    char_count = len(norm_text)

    empty_text = (word_count == 0)
    very_short_text = (word_count < 10)

    if char_count > 0:
        standard_chars = re.compile(r'[a-zA-Z0-9\s.,!?;:\'"\-\(\)\[\]\{\}\/\*\+\=\<\>\#\$\@\%\&\_\\]')
        non_std_count = sum(1 for c in norm_text if not standard_chars.match(c))
        unusual_symbol_ratio = round(non_std_count / char_count, 4)
    else:
        unusual_symbol_ratio = 0.0

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


def extract_text_from_pdf(pdf_path: str, document_id: str) -> tuple[list[dict], dict]:
    """
    Open PDF using PyMuPDF, extract page-level text, normalize text,
    calculate metrics, and evaluate text layer presence.
    """
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        raise ValueError(f"Failed to open PDF file: {str(e)}")

    page_count = len(doc)
    pages_data = []
    total_words = 0
    pages_with_text_count = 0
    pages_with_images_count = 0

    for i in range(page_count):
        page = doc[i]
        page_num = i + 1
        raw_text = page.get_text() or ""
        norm_text = normalize_text_conservative(raw_text)

        has_text = bool(norm_text.strip())
        char_cnt = len(norm_text)
        word_cnt = len(norm_text.split())
        total_words += word_cnt

        if has_text:
            pages_with_text_count += 1

        images = page.get_images()
        has_image = bool(images and len(images) > 0)
        if has_image:
            pages_with_images_count += 1

        q_metrics = calculate_quality_metrics(raw_text, norm_text)

        pages_data.append({
            "document_id": document_id,
            "page_number": page_num,
            "raw_text": raw_text,
            "normalized_text": norm_text,
            "has_text": has_text,
            "character_count": char_cnt,
            "word_count": word_cnt,
            "has_image": has_image,
            "quality_metrics": q_metrics
        })

    doc.close()

    summary = {
        "page_count": page_count,
        "pages_with_text": pages_with_text_count,
        "pages_with_images": pages_with_images_count,
        "has_text_layer": (pages_with_text_count > 0),
        "total_words": total_words
    }

    return pages_data, summary

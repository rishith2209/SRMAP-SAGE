import re
from typing import List, Dict, Any


def split_into_chunks(
    text: str,
    page_number: int,
    document_title: str,
    extraction_method: str = "digital",
    max_chunk_chars: int = 1500,
    overlap_chars: int = 200
) -> List[Dict[str, Any]]:
    """
    Splits page text into semantically cohesive chunks while preserving
    structural metadata (section headers, page numbers, extraction method).
    """
    if not text.strip():
        return []

    # Detect possible section headers (e.g., '1. Objective', 'Article 3', 'Scope:', 'Eligibility Criteria')
    header_pattern = re.compile(r"^([0-9]+(\.[0-9]+)*\s+[A-Z][^\n]+|[A-Z\s]{4,}:|Article\s+[0-9]+)", re.MULTILINE)
    headers = [m.group(0).strip() for m in header_pattern.finditer(text)]
    current_header = headers[0] if headers else None

    # Split by paragraphs or double newlines first
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    chunks = []
    current_chunk = []
    current_len = 0

    for para in paragraphs:
        # Check if paragraph contains a new heading
        match = header_pattern.search(para)
        if match:
            current_header = match.group(0).strip()

        para_len = len(para)
        if current_len + para_len > max_chunk_chars and current_chunk:
            chunk_content = "\n\n".join(current_chunk)
            chunks.append({
                "page_number": page_number,
                "section_heading": current_header,
                "content": chunk_content,
                "token_count": len(chunk_content.split()),
                "extraction_method": extraction_method
            })
            # Overlap: keep last paragraph if short enough
            if len(current_chunk[-1]) < overlap_chars:
                current_chunk = [current_chunk[-1], para]
                current_len = len(current_chunk[0]) + para_len
            else:
                current_chunk = [para]
                current_len = para_len
        else:
            current_chunk.append(para)
            current_len += para_len

    if current_chunk:
        chunk_content = "\n\n".join(current_chunk)
        chunks.append({
            "page_number": page_number,
            "section_heading": current_header,
            "content": chunk_content,
            "token_count": len(chunk_content.split()),
            "extraction_method": extraction_method
        })

    return chunks

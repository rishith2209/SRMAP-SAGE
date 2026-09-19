import logging
import re
from typing import List, Dict, Any, Optional
import pymupdf
from rapidocr_onnxruntime import RapidOCR

logger = logging.getLogger(__name__)

# Lazy singleton for OCR engine
_ocr_engine = None


def get_ocr():
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = RapidOCR()
    return _ocr_engine


class DocumentExtractor:
    """
    Extracts text from digital and scanned PDFs with automatic OCR fallback.
    Preserves page boundaries, extraction methods, and attempts regex metadata extraction.
    """

    POLICY_NUM_PATTERN = re.compile(
        r"(SRMAP\s*/\s*[A-Za-z0-9\.\s_/-]+Policies\s*/\s*[0-9\s/-]+|Policy\s+No\.?:?\s*[A-Za-z0-9/-]+)",
        re.IGNORECASE
    )
    DATE_PATTERN = re.compile(
        r"(\b\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s+\d{4}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b)",
        re.IGNORECASE
    )

    @classmethod
    def extract_pdf(cls, file_path: str) -> Dict[str, Any]:
        doc = pymupdf.open(file_path)
        pages_data = []
        requires_ocr_count = 0
        total_pages = len(doc)
        full_text_list = []

        for page_idx, page in enumerate(doc, start=1):
            text = page.get_text().strip()
            extraction_method = "digital"

            # Check if text is insufficient (scanned image page)
            if len(text) < 40:
                extraction_method = "ocr"
                requires_ocr_count += 1
                ocr = get_ocr()
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                ocr_result, _ = ocr(img_bytes)
                if ocr_result:
                    text = " ".join([line[1] for line in ocr_result])
                else:
                    text = ""

            pages_data.append({
                "page_number": page_idx,
                "text": text,
                "extraction_method": extraction_method,
                "char_count": len(text)
            })
            full_text_list.append(text)

        combined_first_pages = " ".join(full_text_list[:2])

        # Extract Policy Number & Date if present
        policy_number_match = cls.POLICY_NUM_PATTERN.search(combined_first_pages)
        policy_number = policy_number_match.group(0).strip() if policy_number_match else None

        date_match = cls.DATE_PATTERN.search(combined_first_pages)
        policy_date = date_match.group(0).strip() if date_match else None

        return {
            "file_path": file_path,
            "total_pages": total_pages,
            "requires_ocr": requires_ocr_count > 0,
            "scanned_pages_count": requires_ocr_count,
            "policy_number": policy_number,
            "policy_date": policy_date,
            "pages": pages_data,
            "full_text": "\n\n".join(full_text_list)
        }

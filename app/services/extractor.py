import io
import logging
from typing import Optional

import fitz
import pdfplumber
from fastapi import UploadFile

from app.services.ocr import extract_text_from_image
from app.utils.helpers import clean_text

logger = logging.getLogger(__name__)


async def extract_text(file: UploadFile) -> str:
    raw_bytes = await file.read()
    if not raw_bytes:
        return ""

    filename = file.filename.lower()
    content_type = (file.content_type or "").lower()

    if filename.endswith(".pdf") or content_type == "application/pdf":
        return await extract_text_from_pdf(raw_bytes)

    if any(filename.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"]) or content_type.startswith("image/"):
        return await extract_text_from_image(raw_bytes)

    raise ValueError("Unsupported file type. Please upload a PDF or image file.")


async def extract_text_from_pdf(raw_bytes: bytes) -> str:
    extracted = []
    try:
        with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
            for page in pdf.pages:
                extracted.append(page.extract_text() or "")
    except Exception as exc:
        logger.warning("pdfplumber extraction failed, falling back to PyMuPDF: %s", exc)

    if not any(text.strip() for text in extracted):
        try:
            document = fitz.open(stream=raw_bytes, filetype="pdf")
            for page in document:
                extracted.append(page.get_text())
        except Exception as exc:
            logger.error("PyMuPDF fallback failed: %s", exc)

    raw_text = "\n".join(extracted)
    cleaned_text = clean_text(raw_text)

    # If no text extracted (non-searchable PDF), fall back to OCR
    if not cleaned_text.strip():
        logger.info("No text extracted from PDF, falling back to OCR")
        try:
            document = fitz.open(stream=raw_bytes, filetype="pdf")
            ocr_texts = []
            for page_num in range(len(document)):
                page = document.load_page(page_num)
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                page_text = await extract_text_from_image(img_bytes)
                ocr_texts.append(page_text)
            cleaned_text = clean_text("\n".join(ocr_texts))
        except Exception as exc:
            logger.error("OCR fallback failed: %s", exc)
            raise ValueError("Failed to extract text from PDF using OCR")

    return cleaned_text

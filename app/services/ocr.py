import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import easyocr
from PIL import Image

logger = logging.getLogger(__name__)
_thread_pool = ThreadPoolExecutor(max_workers=2)
_reader = None


def get_ocr_reader() -> easyocr.Reader:
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


def preprocess_image(raw_bytes: bytes) -> Image.Image:
    return Image.open(BytesIO(raw_bytes)).convert("RGB")


async def extract_text_from_image(raw_bytes: bytes) -> str:
    loop = asyncio.get_running_loop()
    try:
        image = await loop.run_in_executor(_thread_pool, preprocess_image, raw_bytes)
        reader = await loop.run_in_executor(_thread_pool, get_ocr_reader)
        text_lines = await loop.run_in_executor(_thread_pool, reader.readtext, image, 0, True)
        if isinstance(text_lines, list):
            return "\n".join(text_lines)
        return ""
    except Exception as exc:
        logger.error("Image OCR failed: %s", exc)
        raise

import re
from typing import List

SUPPORTED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "tiff", "bmp", "gif"}


def clean_text(text: str) -> str:
    text = re.sub(r"[\r\t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def split_lines(text: str) -> List[str]:
    return [line.strip() for line in re.split(r"\r?\n", text) if line.strip()]


def has_supported_extension(filename: str) -> bool:
    extension = filename.lower().split(".")[-1]
    return extension in SUPPORTED_EXTENSIONS

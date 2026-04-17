import asyncio
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "llama3"


def _call_ollama(prompt: str) -> str:
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 400,
                    "temperature": 0.2,
                },
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("response", "").strip()
    except Exception as exc:
        logger.warning("Ollama request failed: %s", exc)
        return ""


async def generate_summary_with_ollama(prompt_text: str) -> str:
    if not prompt_text.strip():
        return ""

    loop = asyncio.get_running_loop()
    generated = await loop.run_in_executor(None, _call_ollama, prompt_text)
    return generated.strip() if generated else ""


async def refine_text_with_ollama(original_text: str) -> str:
    if not original_text.strip():
        return original_text

    prompt = (
        "Refine the following medical report summary text for clarity and readability. "
        "Keep the same meaning and do not add new medical findings.\n\n"
        f"Summary:\n{original_text}"
    )
    loop = asyncio.get_running_loop()
    refined = await loop.run_in_executor(None, _call_ollama, prompt)
    return refined or original_text

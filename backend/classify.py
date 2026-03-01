"""Single-call image classifier: sends image + full city MRF doc to Claude in one request."""

import base64
import json
import os

from dotenv import load_dotenv
from perplexity import Perplexity

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

pplx_client = Perplexity(api_key=os.getenv("PERPLEXITY_API_KEY"))

SYSTEM_PROMPT = """You are a recycling compliance system for a Materials Recovery Facility.
You reason strictly from the facility documentation provided. Never use general knowledge.

STEP 1: Identify the PRIMARY disposable/waste item in the image.
Ignore people, hands, background, furniture, and surfaces.
If there is no disposable or waste item visible, return {"action":"N/A"}.

STEP 2: Classify it using ONLY the facility specs below.

When the item is black plastic of any kind, you MUST state that NIR optical
sorters cannot detect carbon-black pigmented polymers.

Return ONLY a JSON object with exactly these keys:
- item: specific name (e.g. "black plastic takeout container", "clear PET water bottle")
- action: "RECYCLE", "TRASH", "COMPOST", or "SPECIAL"
  - COMPOST: only for cities with composting programs, only for food waste/food-soiled items
  - SPECIAL: only for hazardous/regulated items (batteries, electronics, paint, chemicals)
  - TRASH: everything else not recyclable or compostable
- reason: one sentence citing specific facility equipment or rule from the docs
- confidence: "high", "medium", or "low"

No preamble. No markdown. No text outside the JSON object."""

# Load all city MRF docs into memory at startup
_city_docs: dict[str, str] = {}

CITY_FILES = {
    "seattle": "seattle_mrf.txt",
    "nyc": "nyc_mrf.txt",
    "la": "la_mrf.txt",
    "chicago": "chicago_mrf.txt",
}

for city_key, filename in CITY_FILES.items():
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            _city_docs[city_key] = f.read()
        print(f"[classify] loaded {filename} ({len(_city_docs[city_key])} chars)")


def _detect_mime_type(image_bytes: bytes) -> str:
    if image_bytes[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def classify_image(image_bytes: bytes, city: str) -> dict:
    """Single API call: identify item from image + classify against city MRF docs."""
    city_doc = _city_docs.get(city)
    if not city_doc:
        raise ValueError(f"No MRF document found for city: {city}")

    mime_type = _detect_mime_type(image_bytes)
    b64 = base64.b64encode(image_bytes).decode()
    data_uri = f"data:{mime_type};base64,{b64}"

    user_prompt = f"""FACILITY SPECS ({city} MRF documentation):
{city_doc}

CITY: {city}

Look at the image and classify the waste item based only on the facility specs above."""

    response = pplx_client.responses.create(
        model="anthropic/claude-sonnet-4-6",
        instructions=SYSTEM_PROMPT,
        input=[
            {
                "type": "message",
                "role": "user",
                "content": [
                    {"type": "input_text", "text": user_prompt},
                    {"type": "input_image", "image_url": data_uri},
                ],
            }
        ],
        max_output_tokens=200,
    )

    raw = response.output_text.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        print(f"[classify] JSON parse error. Raw: {raw}")
        return {
            "item": "unknown item",
            "action": "TRASH",
            "reason": "Classification error — defaulting to trash",
            "confidence": "low",
        }

    print(f"[classify] {result.get('item')} → {result.get('action')} ({result.get('confidence')})")

    return {
        "item": result.get("item", "unknown item"),
        "action": result.get("action", "TRASH"),
        "reason": result.get("reason", "No reason provided"),
        "confidence": result.get("confidence", "low"),
    }

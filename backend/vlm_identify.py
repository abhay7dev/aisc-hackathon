import base64
import json
import os

from dotenv import load_dotenv
from perplexity import Perplexity

load_dotenv()

pplx_client = Perplexity(api_key=os.getenv("PERPLEXITY_API_KEY"))

VLM_PROMPT = """You are a waste item identification system. Identify the PRIMARY disposable/waste item
the user is presenting to the camera. Ignore background objects, people, and surfaces.

Return ONLY a JSON object with these keys:
- item_name: specific name using recycling vocabulary (e.g. "black plastic takeout container",
  "clear PET water bottle", "plastic grocery bag", "greasy pizza box", "garden hose")
- material: primary material (plastic, metal, glass, paper, cardboard, foam, organic, mixed, unknown)
- color: the item's color, especially note if it is BLACK plastic
- condition: clean, food-soiled, contaminated, wet, crushed, or normal
- is_disposable: true if this is waste/disposable, false if it's a personal belonging
  (wallet, phone, keys, backpack, clothing, laptop, etc.)

No preamble. No markdown fences. Just the JSON object."""


def _detect_mime_type(image_bytes: bytes) -> str:
    """Detect MIME type from magic bytes."""
    if image_bytes[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    if image_bytes[:3] == b"GIF":
        return "image/gif"
    return "image/jpeg"  # default fallback


def identify_object_vlm(image_bytes: bytes) -> dict:
    """Send image to Claude VLM via Perplexity to identify the waste item."""
    mime_type = _detect_mime_type(image_bytes)
    b64 = base64.b64encode(image_bytes).decode()
    data_uri = f"data:{mime_type};base64,{b64}"

    response = pplx_client.responses.create(
        model="anthropic/claude-sonnet-4-6",
        input=[
            {
                "type": "message",
                "role": "user",
                "content": [
                    {"type": "input_text", "text": VLM_PROMPT},
                    {"type": "input_image", "image_url": data_uri},
                ],
            }
        ],
        max_output_tokens=300,
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
        print(f"[vlm] JSON parse error. Raw: {raw}")
        # Fallback: try to extract what we can
        return {
            "item_name": "unknown item",
            "material": "unknown",
            "color": "unknown",
            "condition": "unknown",
            "is_disposable": True,
        }

    print(f"[vlm] identified: {result.get('item_name')} ({result.get('material')}, {result.get('color')})")

    return {
        "item_name": result.get("item_name", "unknown item"),
        "material": result.get("material", "unknown"),
        "color": result.get("color", "unknown"),
        "condition": result.get("condition", "normal"),
        "is_disposable": result.get("is_disposable", True),
    }

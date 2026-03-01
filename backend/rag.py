import json
import os

import chromadb
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from perplexity import Perplexity

load_dotenv()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

SYSTEM_PROMPT = """You are a recycling compliance system for a Materials Recovery Facility.
You reason strictly from the facility documentation provided. Never use general knowledge.

MATERIAL IDENTIFICATION IS CRITICAL:
You will receive multiple vision signals: detected objects, raw CV labels, web-matched
product names, and OCR text. Use ALL of these to determine the TRUE material of the item:
- Web entities often reveal the actual product (e.g. "Hydro Flask" = stainless steel,
  "Yeti Rambler" = stainless steel, "Nalgene" = plastic).
- Raw labels may include material hints like "metal", "aluminum", "steel", "plastic",
  "glass", "ceramic", "wood" — use these even if the primary label says something generic.
- A painted/coated metal bottle is still METAL, not plastic. Look for material cues.
- If web entities identify a known reusable product (metal water bottle, thermos, etc.),
  it is NOT single-use disposable — classify as SPECIAL or TRASH depending on facility rules.

When the item is black plastic of any kind, you MUST state in the reason that NIR optical
sorters cannot detect carbon-black pigmented polymers.

CRITICAL: The ITEM DETECTED field is the primary object identified by computer vision.
Classify ONLY that item. Background text may refer to other objects — ignore it.

NON-DISPOSABLE DETECTION:
Check the raw CV labels carefully. If labels include things like "wallet", "leather",
"handbag", "purse", "keychain", "key", "backpack", "luggage", "watch", "phone",
"laptop", or other personal belongings that are NOT waste, return NOT_DISPOSABLE.
These items should not be thrown away in any bin. The primary detected label may be
generic (e.g. "Bag") but the raw labels reveal the true identity.

Return ONLY a JSON object with exactly these keys:
- action: one of "RECYCLE", "TRASH", "COMPOST", "SPECIAL", or "NOT_DISPOSABLE"
  - COMPOST: valid for cities with composting programs (NYC, Seattle, LA) for food waste
    and food-soiled items. Check the facility docs for composting rules.
  - SPECIAL: use when the facility docs say the item requires special disposal,
    drop-off, or should NOT go in recycling OR trash (e.g. electronics, batteries,
    hazardous waste, paint, vape pens).
  - NOT_DISPOSABLE: use when the item is a personal belonging or reusable item that
    should not be disposed of (wallet, keys, phone, backpack, clothing, etc.).
    The reason should say what the item actually is.
- reason: one sentence citing specific facility equipment or rule from the retrieved docs.
  For NOT_DISPOSABLE, explain what the item is and that it should not be disposed of.
- confidence: "high", "medium", or "low"

No preamble. No markdown. No text outside the JSON object."""

HUMAN_PROMPT = """FACILITY SPECS (retrieved from {city} MRF documentation):
{context}

ITEM DETECTED: {item}
{extra_signals}CITY: {city}

Classify the ITEM DETECTED based on the facility specs and all visual signals above."""

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
vectorstore = Chroma(
    client=chroma_client,
    collection_name="mrf_docs",
    embedding_function=embeddings,
)

pplx_client = Perplexity(api_key=os.getenv("PERPLEXITY_API_KEY"))


def get_facility_verdict(normalized_item: str, city: str, vision_result: dict = None) -> dict:
    if vision_result is None:
        vision_result = {}

    query = f"{normalized_item} {city} MRF recycling"
    docs = vectorstore.similarity_search(query, k=4)

    if not docs:
        raise ValueError("No facility documents found — cannot classify without MRF specs")

    context = "\n\n".join(doc.page_content for doc in docs)

    # Build extra signals block for Claude
    signals = []
    raw_labels = vision_result.get("raw_labels", [])
    if raw_labels:
        signals.append(f"RAW CV LABELS (all, unfiltered): {', '.join(raw_labels)}")

    web_entities = vision_result.get("web_entities", [])
    if web_entities:
        signals.append(f"WEB-MATCHED PRODUCTS/ENTITIES: {', '.join(web_entities)}")

    web_labels = vision_result.get("web_labels", [])
    if web_labels:
        signals.append(f"WEB BEST GUESS: {', '.join(web_labels)}")

    detected_text = vision_result.get("text", "")
    if detected_text:
        signals.append(f"OCR TEXT (may include background): {detected_text[:200]}")

    extra_signals = "\n".join(signals) + "\n" if signals else ""

    prompt = HUMAN_PROMPT.format(
        context=context, item=normalized_item, city=city, extra_signals=extra_signals
    )

    response = pplx_client.responses.create(
        model="anthropic/claude-sonnet-4-6",
        instructions=SYSTEM_PROMPT,
        input=prompt,
        max_output_tokens=400,
    )

    raw = response.output_text.strip()

    # Strip markdown fences if Claude wrapped the JSON
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        print(f"[rag] JSON parse error. Raw response: {raw}")
        return {
            "action": "TRASH",
            "reason": "Classification error — defaulting to trash",
            "confidence": "low",
        }

    return {
        "action": result.get("action", "TRASH"),
        "reason": result.get("reason", "No reason provided"),
        "confidence": result.get("confidence", "low"),
    }

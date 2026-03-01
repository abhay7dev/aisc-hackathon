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

When the item is black plastic of any kind, you MUST state in the reason that NIR optical
sorters cannot detect carbon-black pigmented polymers.

Return ONLY a JSON object with exactly these keys:
- action: one of "RECYCLE", "TRASH", "COMPOST", or "SPECIAL"
  - COMPOST: valid for cities with composting programs (NYC, Seattle, LA) for food waste
    and food-soiled items. Check the facility docs for composting rules.
  - SPECIAL: use ONLY for items with specific hazardous or regulated disposal requirements
    (batteries, electronics, paint, chemicals, vape pens, fluorescent bulbs, motor oil, etc.).
    These items must NOT go in regular trash or recycling.
  - TRASH: use for everything else that isn't recyclable or compostable, INCLUDING ordinary
    personal belongings like keychains, wallets, clothing, toys, etc. If the item is not
    hazardous and has no special disposal rules, it's just TRASH.
- reason: one sentence citing specific facility equipment or rule from the retrieved docs.
  For SPECIAL items, explain what the specific disposal requirement is.
- confidence: "high", "medium", or "low"

No preamble. No markdown. No text outside the JSON object."""

HUMAN_PROMPT = """FACILITY SPECS (retrieved from {city} MRF documentation):
{context}

ITEM: {item_name}
MATERIAL: {material}
COLOR: {color}
CONDITION: {condition}
{hint}CITY: {city}

Classify this item based only on the facility specs above."""

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
vectorstore = Chroma(
    client=chroma_client,
    collection_name="mrf_docs",
    embedding_function=embeddings,
)

pplx_client = Perplexity(api_key=os.getenv("PERPLEXITY_API_KEY"))


def get_facility_verdict(item_identification: dict, city: str) -> dict:
    item_name = item_identification.get("item_name", "unknown item")
    material = item_identification.get("material", "unknown")
    color = item_identification.get("color", "unknown")
    condition = item_identification.get("condition", "normal")
    is_disposable = item_identification.get("is_disposable", True)

    query = f"{item_name} {material} {color} {city} MRF recycling"
    docs = vectorstore.similarity_search(query, k=4)

    if not docs:
        raise ValueError("No facility documents found — cannot classify without MRF specs")

    context = "\n\n".join(doc.page_content for doc in docs)

    hint = ""
    if not is_disposable:
        hint = "NOTE: This appears to be a personal belonging, not typical waste. Classify as TRASH unless it has specific hazardous/regulated disposal requirements (then SPECIAL).\n"

    prompt = HUMAN_PROMPT.format(
        context=context,
        item_name=item_name,
        material=material,
        color=color,
        condition=condition,
        hint=hint,
        city=city,
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

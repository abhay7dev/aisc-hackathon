from google.cloud import vision

from vision_normalize import normalize_labels

# Substrings to ignore — if ANY of these appear anywhere in the label, skip it.
# This catches compound terms like "Vision care", "Flash photography", etc.
IGNORED_SUBSTRINGS = {
    # People and body
    "person", "people", "human", "woman", "man ", "boy", "girl", "child",
    "adult", "baby", "crowd", "audience",
    "face", "head", "nose", "mouth", "lip", "chin", "cheek", "forehead",
    "eye", "brow", "lash", "ear", "neck", "jaw", "tooth", "tongue",
    "hand", "finger", "thumb", "nail", "wrist", "palm", "fist",
    "arm", "elbow", "shoulder", "leg", "foot", "toe", "knee", "torso", "chest",
    "skin", "hair", "beard", "mustache", "wrinkle",
    # Expressions and emotions
    "smile", "facial", "gesture", "selfie", "laugh",
    "happiness", "happy", "sadness", "anger", "surprise", "disgust", "fear",
    "emotion", "joy", "excite", "cool", "fun",
    # Clothing, accessories, personal wear
    "cloth", "shirt", "sleeve", "glove", "jacket", "pants", "jeans",
    "dress", "coat", "shoe", "boot", "sock", "belt", "vest",
    "outerwear", "shorts", "skirt", "scarf", "hoodie", "sweater", "uniform",
    "costume", "t-shirt",
    "glasses", "sunglass", "eyewear", "goggle", "spectacle", "vision care",
    "watch", "jewel", "ring", "bracelet", "necklace", "earring",
    "fashion", "accessory",
    # Photography and scene
    "photo", "camera", "snapshot", "monochrome", "black and white", "flash", "selfie",
    # Personal care noise (not the item being scanned)
    "personal care", "cosmetic", "lipstick", "makeup", "nail", "step cutting",
    "hair care", "hair",
    # Background and environment
    "room", "ceiling", "floor", "wall", "table", "desk", "chair",
    "couch", "sofa", "bed", "furniture", "shelf", "cabinet",
    "window", "door", "curtain", "carpet", "rug", "interior",
    "building", "house", "architecture", "sky", "cloud", "landscape",
    "outdoor", "indoor", "comfort", "event",
    # Abstract / visual noise
    "pattern", "design", "logo", "symbol", "font", "text",
    "circle", "rectangle", "line", "color",
    "material property", "electric blue", "magenta", "tint",
}

# Labels that are likely disposable/physical items — these get a priority boost
# when picking from label_detection results (which mix scene tags with object tags).
ITEM_KEYWORDS = {
    "bottle", "can", "cup", "container", "box", "bag", "wrapper", "packaging",
    "carton", "lid", "cap", "straw", "utensil", "cutlery", "fork", "spoon",
    "knife", "plate", "bowl", "tray", "napkin", "towel", "tissue",
    "food", "cupcake", "cake", "pizza", "bread", "fruit", "vegetable", "meat",
    "ice cream", "dessert", "candy", "snack", "sandwich", "burrito",
    "plastic", "paper", "cardboard", "aluminum", "glass", "metal", "tin",
    "foam", "styrofoam", "polystyrene", "newspaper", "magazine",
    "battery", "electronic", "phone", "computer", "device", "charger", "cable",
    "gadget", "headphone", "headset", "earbud", "airpod", "speaker", "remote",
    "keyboard", "mouse", "tablet", "laptop", "monitor", "screen",
    "hose", "garden", "yard",
    "tube", "spray",
    "toy", "pen", "marker", "crayon",
    "drink", "beverage", "juice", "soda", "water", "coffee", "tea", "milk",
}


def _is_ignored(label: str) -> bool:
    low = label.lower()
    return any(sub in low for sub in IGNORED_SUBSTRINGS)


def _is_item_like(label: str) -> bool:
    low = label.lower()
    return any(kw in low for kw in ITEM_KEYWORDS)


def identify_object(image_bytes: bytes) -> dict:
    client = vision.ImageAnnotatorClient()
    full_image = vision.Image(content=image_bytes)

    # Run all detection on full image — we'll filter via scoring, not cropping.
    # Cropping was too aggressive and cut out items held to the side.
    label_response = client.label_detection(image=full_image)
    labels = label_response.label_annotations

    object_response = client.object_localization(image=full_image)
    objects = object_response.localized_object_annotations

    text_response = client.text_detection(image=full_image)
    detected_text = ""
    if text_response.text_annotations:
        detected_text = text_response.text_annotations[0].description.strip()

    web_response = client.web_detection(image=full_image)
    web_entities = []
    web_labels = []
    if web_response.web_detection:
        web = web_response.web_detection
        web_entities = [
            e.description for e in (web.web_entities or [])
            if e.description and e.score > 0.3
        ][:5]
        web_labels = [
            l.label for l in (web.best_guess_labels or [])
        ]

    # Collect ALL raw material-related labels before filtering
    raw_all = [l.description for l in labels[:10]]

    # Filter out human/irrelevant results
    filtered_labels = [l for l in labels if not _is_ignored(l.description)]
    filtered_objects = [o for o in objects if not _is_ignored(o.name)]

    # Score objects by closeness to frame center + size
    def _center_score(obj):
        verts = obj.bounding_poly.normalized_vertices
        if len(verts) < 4:
            return 0
        xs = [v.x for v in verts]
        ys = [v.y for v in verts]
        cx = (min(xs) + max(xs)) / 2
        cy = (min(ys) + max(ys)) / 2
        area = (max(xs) - min(xs)) * (max(ys) - min(ys))
        dist = ((cx - 0.5) ** 2 + (cy - 0.5) ** 2) ** 0.5
        return (1 - dist) * (area ** 0.5)

    filtered_objects.sort(key=_center_score, reverse=True)

    object_names = [obj.name for obj in filtered_objects]

    # Sort labels: item-like labels first, then the rest
    item_labels = [l for l in filtered_labels if _is_item_like(l.description)]
    other_labels = [l for l in filtered_labels if not _is_item_like(l.description)]
    sorted_labels = item_labels + other_labels
    label_names = [l.description for l in sorted_labels[:5]]

    # Filter web entities the same way
    filtered_web = [w for w in web_entities if not _is_ignored(w)]
    item_web = [w for w in filtered_web if _is_item_like(w)]

    # Pick the best item name from all sources, prioritizing item-like matches:
    # 1. Objects (center-scored, physical bounding boxes)
    # 2. Item-like web entities (product names from reverse image search)
    # 3. Item-like labels
    # 4. Any remaining labels
    # 5. Any remaining web entities
    if object_names:
        top_item = object_names[0]
    elif item_web:
        top_item = item_web[0]
    elif label_names:
        top_item = label_names[0]
    elif filtered_web:
        top_item = filtered_web[0]
    else:
        top_item = "unknown item"

    # Combine all sources for normalization
    combined = object_names[:2] + label_names[:2]
    if not combined:
        combined = [top_item]

    normalized = normalize_labels(combined)

    print(f"[vision] objects: {object_names[:5]}")
    print(f"[vision] labels (sorted): {label_names[:5]}")
    print(f"[vision] raw labels: {raw_all}")
    print(f"[vision] web entities: {web_entities[:5]}")
    print(f"[vision] web best guess: {web_labels}")
    if detected_text:
        print(f"[vision] OCR text: {detected_text[:100]}")

    return {
        "label": top_item,
        "all_labels": label_names,
        "objects": object_names,
        "raw_labels": raw_all,
        "web_entities": web_entities,
        "web_labels": web_labels,
        "text": detected_text,
        "normalized": normalized,
    }

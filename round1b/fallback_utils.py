import fitz
import re
from collections import Counter

def normalize(text):
    return re.sub(r"\s+", " ", text.strip()).lower()

def extract_title(page):
    """Extract a plausible title from the first page using font size and position."""
    blocks = page.get_text("dict")["blocks"]
    max_font = 0
    candidates = []
    height = page.rect.height

    for block in blocks:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span["text"].strip()
                if not text or len(text) < 3:
                    continue
                if re.match(r"^(Copyright|Page|May|©|www\.|file:|http)", text, re.I):
                    continue
                if "qualification" in text.lower() or "board" in text.lower():
                    continue
                if span["size"] > max_font:
                    max_font = span["size"]

    for block in blocks:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span["text"].strip()
                if not text or len(text) < 3:
                    continue
                if re.match(r"^(Copyright|Page|May|©|www\.|file:|http)", text, re.I):
                    continue
                if "qualification" in text.lower() or "board" in text.lower():
                    continue
                if span["size"] >= max_font - 1 and span["bbox"][1] < height * 0.35 and span["bbox"][0] < 300:
                    candidates.append(text)

    seen = set()
    ordered = []
    for c in candidates:
        if c not in seen:
            ordered.append(c)
            seen.add(c)

    return "  ".join(ordered).strip() + "  " if ordered else ""

def looks_like_form(page):
    """Detects if a PDF page looks like a government form."""
    text = page.get_text("text").lower()
    keywords = ["application", "form", "signature", "undertake", "date of",
                "name of", "designation", "service", "pay", "whether"]
    count = sum(1 for kw in keywords if kw in text)
    colon_lines = sum(1 for line in text.splitlines() if ":" in line)
    return count >= 3 or colon_lines > 10

def extract_headings_structured(doc):
    """Returns a list of headings by using regex rules and font size matching."""
    outline = []
    seen = set()
    h1_font_sizes = []

    if looks_like_form(doc[0]):
        text = doc[0].get_text("text")
        for line in text.splitlines():
            line = line.strip()
            if ":" in line and len(line) < 100 and not re.search(r"\d", line):
                if line not in seen:
                    outline.append({
                        "level": "H1",
                        "text": line.rstrip(":").strip(),
                        "page": 0
                    })
                    seen.add(line)
        return outline

    # Step 1: Estimate H1 font size from common numbered headings
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                text = "".join(span["text"] for span in spans).strip()
                if re.match(r"^\d+\.\s+\S+", text) and len(text.split()) < 10:
                    h1_font_sizes.append(spans[0]["size"])

    h1_font_size = Counter(h1_font_sizes).most_common(1)[0][0] if h1_font_sizes else None

    for i, page in enumerate(doc):
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                text = "".join(span["text"] for span in spans).strip()
                if not text or text in seen:
                    continue

                x0 = spans[0]["bbox"][0]
                font_size = spans[0]["size"]
                clean = text

                # --- H1 Rule ---
                if (re.match(r"^\d+\.\s+\S+", clean)
                        and len(clean.split()) < 10
                        and x0 < 100
                        and (h1_font_size is None or abs(font_size - h1_font_size) < 1.0)
                        and len(clean) < 60):
                    outline.append({"level": "H1", "text": clean, "page": i})
                    seen.add(clean)
                    continue

                # --- H1 Big Font No-Number ---
                if (h1_font_size is not None
                        and abs(font_size - h1_font_size) < 1.0
                        and x0 < 100 and 7 < len(clean) < 50
                        and clean not in seen
                        and not re.match(r"^\d+(\.|,)", clean)):
                    outline.append({"level": "H1", "text": clean, "page": i})
                    seen.add(clean)
                    continue

                # --- H2 Rule ---
                if re.match(r"^\d+\.\d+\s+\S+", clean):
                    outline.append({"level": "H2", "text": clean, "page": i})
                    seen.add(clean)
                    continue

                # --- H3 Rule ---
                if re.match(r"^\d+\.\d+\.\d+\s+\S+", clean):
                    outline.append({"level": "H3", "text": clean, "page": i})
                    seen.add(clean)
                    continue

    # Deduplicate
    final_outline = []
    seen_keys = set()
    for item in outline:
        key = (item["text"], item["page"], item["level"])
        if key not in seen_keys:
            final_outline.append(item)
            seen_keys.add(key)
    return final_outline

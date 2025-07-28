import os
import json
import joblib
import fitz
import re
from pathlib import Path
from datetime import datetime
from fallback_utils import extract_title, extract_headings_structured
from subsummarizer import predict_summary

INPUT_ROOT = Path("input")
OUTPUT_ROOT = Path("output")
OUTPUT_ROOT.mkdir(exist_ok=True)

clf = joblib.load("model/heading_classifier.joblib")
label_encoder = joblib.load("model/label_encoder.joblib")
font_encoder = joblib.load("model/font_encoder.joblib")
punct_encoder = joblib.load("model/punctuation_encoder.joblib")

features_cols = [
    "font_size", "font_name_encoded", "is_bold", "is_italic",
    "x0", "x1", "y0", "y1",
    "char_count", "capital_ratio", "line_y_ratio",
    "punctuation_encoded", "has_numbering"
]

def normalize(text):
    return re.sub(r"\s+", " ", text.strip()).lower()

def encode_punctuation(p):
    return punct_encoder.transform([p])[0] if p in punct_encoder.classes_ else 0

def relevance_score(section, persona, job):
    section = section.lower()
    keywords = (persona + " " + job).lower().split()
    return sum(1 for word in keywords if word in section)

for case_dir in sorted(INPUT_ROOT.glob("challenge_case_*")):
    input_json = case_dir / "challenge1b_input.json"
    with open(input_json, "r", encoding="utf-8") as f:
        meta = json.load(f)

    persona = meta.get("persona", {}).get("role", "") or meta.get("persona", "")
    job = meta.get("job_to_be_done", {}).get("task", "") or meta.get("job_to_be_done", "")
    input_docs = []
    extracted_sections = []
    subsection_analysis = []
    seen_titles = set()

    for pdf_path in sorted(case_dir.glob("*.pdf")):
        doc = fitz.open(pdf_path)
        input_docs.append(pdf_path.name)

        lines_raw, features = [], []
        for page_num, page in enumerate(doc):
            blocks = page.get_text("dict")["blocks"]
            page_height = page.rect.height

            for block in blocks:
                if block["type"] != 0:
                    continue
                for line in block["lines"]:
                    spans = line.get("spans", [])
                    if not spans:
                        continue
                    text = " ".join(span["text"] for span in spans).strip()
                    if not text:
                        continue

                    font_sizes = [span["size"] for span in spans]
                    font_names = [span["font"] for span in spans]
                    is_bold = any("Bold" in f for f in font_names)
                    is_italic = any("Italic" in f for f in font_names)

                    x0 = min(span["bbox"][0] for span in spans)
                    x1 = max(span["bbox"][2] for span in spans)
                    y0 = min(span["bbox"][1] for span in spans)
                    y1 = max(span["bbox"][3] for span in spans)

                    avg_font_size = sum(font_sizes) / len(font_sizes)
                    char_count = len(text)
                    capital_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
                    line_y_ratio = y0 / page_height
                    punct = text[-1] if text and text[-1] in ":.?" else "none"
                    has_numbering = bool(re.match(r"^\d+(\.\d+)*", text.strip()))
                    font_encoded = font_encoder.transform([font_names[0]])[0] if font_names[0] in font_encoder.classes_ else 0
                    punct_encoded = encode_punctuation(punct)

                    features.append([
                        avg_font_size, font_encoded, int(is_bold), int(is_italic),
                        x0, x1, y0, y1,
                        char_count, capital_ratio, line_y_ratio,
                        punct_encoded, int(has_numbering)
                    ])
                    lines_raw.append({"text": text, "page": page_num})

        outline_model = []
        if features:
            import pandas as pd
            X_df = pd.DataFrame(features, columns=features_cols)
            preds = clf.predict(X_df)
            labels = label_encoder.inverse_transform(preds)

            for i, label in enumerate(labels):
                if label in {"H1", "H2", "H3"}:
                    outline_model.append({
                        "level": label,
                        "text": lines_raw[i]["text"],
                        "page": lines_raw[i]["page"]
                    })

        outline_rule = extract_headings_structured(doc)
        all_outline = outline_model + outline_rule

        seen = set()
        final_outline = []
        for item in all_outline:
            key = (normalize(item["text"]), item["page"], item["level"])
            if key not in seen:
                final_outline.append(item)
                seen.add(key)

        scored = sorted([
            (relevance_score(h["text"], persona, job), h)
            for h in final_outline
        ], key=lambda x: -x[0])

        top_sections = [s for score, s in scored if score >= 2][:5]

        for rank, section in enumerate(top_sections, 1):
            norm_title = normalize(section["text"])
            title_key = (pdf_path.name, section["page"], norm_title)
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)

            extracted_sections.append({
                "document": pdf_path.name,
                "page_number": section["page"],
                "section_title": section["text"],
                "importance_rank": rank
            })

            try:
                lines = doc[section["page"]].get_text().split("\n")
                lines = [l.strip() for l in lines if l.strip()]
                paragraph = " ".join(lines[:8])
                summary = predict_summary(paragraph)
            except Exception:
                summary = ""

            subsection_analysis.append({
                "document": pdf_path.name,
                "page_number": section["page"],
                "section_title": section["text"],
                "refined_text": summary
            })

    out_json = {
        "metadata": {
            "input_documents": input_docs,
            "persona": persona,
            "job_to_be_done": job,
            "processed_at": datetime.utcnow().isoformat()
        },
        "extracted_sections": extracted_sections,
        "subsection_analysis": subsection_analysis
    }

    out_path = OUTPUT_ROOT / f"{case_dir.name}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_json, f, indent=2)

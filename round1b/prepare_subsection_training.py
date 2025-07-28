# prepare_subsection_training.py

import json
import fitz
from pathlib import Path
import pandas as pd

LABEL_DIR = Path("labels")
PDF_DIR = Path("input")
OUT_CSV = "subsection_training.csv"

def extract_paragraph_from_page(pdf_path, page_number, max_lines=8):
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_number]
        lines = page.get_text("text").split("\n")
        lines = [l.strip() for l in lines if l.strip()]
        return " ".join(lines[:max_lines]).strip()
    except Exception as e:
        print(f"⚠️ Page extract failed: {pdf_path} Page {page_number} — {e}")
        return ""

rows = []

for json_file in sorted(LABEL_DIR.glob("challenge_case_*.json")):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    extracted_sections = data.get("extracted_sections", [])
    subsection_analysis = data.get("subsection_analysis", [])

    # Map: (doc, page) → summary
    subsection_map = {}
    for item in subsection_analysis:
        doc = item.get("document", "").strip()
        page = item.get("page_number")
        refined = item.get("refined_text", "")
        if doc and isinstance(page, int) and refined:
            subsection_map[(doc, page)] = refined

    for sec in extracted_sections:
        doc_name = sec.get("document", "").strip()
        title = sec.get("section_title", "").strip()
        page = sec.get("page_number")

        if not doc_name or not isinstance(page, int):
            continue

        pdf_path = next(PDF_DIR.glob(f"**/{doc_name}"), None)
        if not pdf_path:
            print(f"❌ PDF not found: {doc_name}")
            continue

        key = (doc_name, page)
        if key in subsection_map:
            gt_summary = subsection_map[key]
            para = extract_paragraph_from_page(pdf_path, page, max_lines=8)

            if para and gt_summary:
                rows.append({
                    "document": doc_name,
                    "section_title": title,
                    "page": page,
                    "paragraph": para,
                    "refined_text": gt_summary
                })

df = pd.DataFrame(rows)
df.to_csv(OUT_CSV, index=False)


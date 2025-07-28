import json
from pathlib import Path
import pandas as pd
from difflib import SequenceMatcher

LABEL_DIR = Path("labels")
PRED_DIR = Path("output")
OUT_CSV = "pseudo_training.csv"

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

rows = []

for label_file in sorted(LABEL_DIR.glob("challenge_case_*.json")):
    pred_file = PRED_DIR / label_file.name
    if not pred_file.exists():
        print(f"⚠️ Missing prediction for: {label_file.name}")
        continue

    with open(label_file, "r", encoding="utf-8") as f1:
        gt = json.load(f1)
    with open(pred_file, "r", encoding="utf-8") as f2:
        pred = json.load(f2)

    gt_map = {
        (item["document"], item["page_number"]): item["refined_text"]
        for item in gt.get("subsection_analysis", [])
    }

    for item in pred.get("subsection_analysis", []):
        key = (item["document"], item["page_number"])
        pred_text = item.get("refined_text", "").strip()
        true_text = gt_map.get(key, "").strip()

        if not pred_text or not true_text:
            continue

        score = similarity(pred_text, true_text)
        if score >= 0.85:
            rows.append({
                "document": item["document"],
                "section_title": item.get("section_title", ""),
                "page": item["page_number"],
                "paragraph": pred_text,           # used as "input"
                "refined_text": true_text         # used as "target"
            })


pd.DataFrame(rows).to_csv(OUT_CSV, index=False)


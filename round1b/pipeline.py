# pipeline.py

import subprocess
import shutil

def run(_, command):
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        exit(1)

# STEP 1 — Training & First Output with base model
run("prep", "python prepare_subsection_training.py")
run("train_base", "python train_subsummarizer.py")

# Ensure subsummarizer.py uses base model
with open("subsummarizer.py", "w") as f:
    f.write('''import joblib
from sklearn.metrics.pairwise import cosine_similarity

model = joblib.load("sub_summarizer.joblib")
vectorizer = model["vectorizer"]
matrix = model["matrix"]
summaries = model["summaries"]

def predict_summary(paragraph: str) -> str:
    if not paragraph.strip():
        return ""
    vec = vectorizer.transform([paragraph])
    sim = cosine_similarity(vec, matrix)
    best_idx = sim.argmax()
    return summaries[best_idx]
''')

# Run with base summarizer
run("main1", "python main.py")

# STEP 2 — Pseudo-labeling + Retraining + Final Output
run("pseudo", "python compare_predictions.py")
run("retrain", "python retrain_summarizer.py")

# Swap summarizer to use retrained model
with open("subsummarizer.py", "w") as f:
    f.write('''import joblib
from sklearn.metrics.pairwise import cosine_similarity

model = joblib.load("sub_summarizer_retrained.joblib")
vectorizer = model["vectorizer"]
matrix = model["matrix"]
summaries = model["summaries"]

def predict_summary(paragraph: str) -> str:
    if not paragraph.strip():
        return ""
    vec = vectorizer.transform([paragraph])
    sim = cosine_similarity(vec, matrix)
    best_idx = sim.argmax()
    return summaries[best_idx]
''')

# Final output using retrained summarizer
run("main2", "python main.py")
print("Output saved!")

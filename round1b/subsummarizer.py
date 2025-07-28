import joblib
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

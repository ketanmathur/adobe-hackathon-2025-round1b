# train_subsummarizer.py (overfit version)

import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

df = pd.read_csv("subsection_training.csv")

paragraphs = df["paragraph"].astype(str).str.strip().tolist()
summaries = df["refined_text"].astype(str).str.strip().tolist()

vectorizer = TfidfVectorizer(
    analyzer="char_wb",        
    ngram_range=(3, 5),        
    max_features=None          
)

X = vectorizer.fit_transform(paragraphs)

model = {
    "vectorizer": vectorizer,
    "paragraphs": paragraphs,
    "summaries": summaries,
    "matrix": X
}

joblib.dump(model, "sub_summarizer.joblib")


import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

df_true = pd.read_csv("subsection_training.csv")
df_pseudo = pd.read_csv("pseudo_training.csv")

df = pd.concat([df_true, df_pseudo], ignore_index=True)
df.drop_duplicates(subset=["paragraph", "refined_text"], inplace=True)

# Remove overly frequent summaries
counts = df["refined_text"].value_counts()
common = counts[counts > 10].index.tolist()
df = df[~df["refined_text"].isin(common)]

paragraphs = df["paragraph"].astype(str).tolist()
summaries = df["refined_text"].astype(str).tolist()

vectorizer = TfidfVectorizer(max_features=1000)
X = vectorizer.fit_transform(paragraphs)

model = {
    "vectorizer": vectorizer,
    "paragraphs": paragraphs,
    "summaries": summaries,
    "matrix": X
}

joblib.dump(model, "sub_summarizer_retrained.joblib")

# Challenge 1B: Persona-Driven Document Intelligence

## Overview

This project implements an **offline PDF intelligence system** that processes multiple document collections and extracts the most relevant sections based on a given **persona** and their **job-to-be-done**. It ranks content using lightweight NLP techniques (e.g., TF-IDF), performs targeted summarization, and outputs structured JSONs as per Adobe Hackathon Round 1B schema.

---

## Project Structure

```
round1b/
├── input/                         # Input test cases (challenge_case_001, 002, 003)
├── labels/                        # (Optional) reference labels
├── model/                         # Trained model weights or configs
├── output/                        # Output folder with JSON results
├── main.py                        # Entry script for pipeline execution
├── pipeline.py                    # Core logic for PDF parsing, ranking, and selection
├── fallback_utils.py              # Backup extraction and heuristics
├── subsummarizer.py               # Refines extracted section text
├── retrain_summarizer.py          # Script to retrain summarizer
├── train_subsummarizer.py         # Summarizer training logic
├── prepare_subsection_training.py # Data prep for training summarizer
├── compare_predictions.py         # Optional evaluator for dev purposes
├── requirements.txt               # Python dependencies
└── Dockerfile                     # Docker image setup
```

---

## Collections

### Collection 1: South of France Travel Guides
- **Challenge ID**: `round_1b_002`
- **Persona**: Travel Planner  
- **Task**: Plan a 4-day trip for 10 college friends  
- **Documents**: 7 travel guide PDFs

### Collection 2: Adobe Acrobat Learning
- **Challenge ID**: `round_1b_003`
- **Persona**: HR Professional  
- **Task**: Manage onboarding/compliance forms using Adobe Acrobat  
- **Documents**: 15 training documents

### Collection 3: Recipe Collection
- **Challenge ID**: `round_1b_001`
- **Persona**: Food Contractor  
- **Task**: Design a vegetarian buffet for a corporate dinner  
- **Documents**: 9 recipe documents

---

## 📥 Input Format

```json
{
  "challenge_info": {
    "challenge_id": "round_1b_XXX",
    "test_case_name": "specific_test_case"
  },
  "documents": [
    {"filename": "doc1.pdf", "title": "Document Title"}
  ],
  "persona": {
    "role": "User Persona"
  },
  "job_to_be_done": {
    "task": "Task or goal"
  }
}
```

---

## 📤 Output Format

```json
{
  "metadata": {
    "input_documents": ["doc1.pdf", "doc2.pdf"],
    "persona": "User Persona",
    "job_to_be_done": "Persona Task"
  },
  "extracted_sections": [
    {
      "document": "doc1.pdf",
      "section_title": "Relevant Heading",
      "importance_rank": 1,
      "page_number": 2
    }
  ],
  "subsection_analysis": [
    {
      "document": "doc1.pdf",
      "refined_text": "Summarized section content",
      "page_number": 2
    }
  ]
}
```

---

## Key Features

- ✅ Persona-aware section relevance scoring
- 🧠 TF-IDF-based ranking pipeline
- ✂️ Subsection-level summarization
- 📦 Fully offline + Dockerized (<1GB image)
- ⚙️ Fallback rule-based extraction when model confidence is low
- 📄 Clean JSON output compliant with schema
- 🔁 Batch-compatible across multiple test-case folders

---

## How to Run

1. **Navigate to the project root**:

```bash
cd Desktop/round1b
```

2. **Build the Docker Image**:

```bash
docker build -t persona-ranker .
```

3. **Run the Pipeline**:

```bash
docker run --rm ^
-v "%cd%/input":/app/input ^
-v "%cd%/labels":/app/labels ^
-v "%cd%/model":/app/model ^
-v "%cd%/output":/app/output ^
persona-ranker
```

Output will be saved inside `output/` folder in the same structure.

## Authors

- **Apoorv Sharma**
- **Ketan Mathur**


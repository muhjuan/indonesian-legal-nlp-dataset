# Indonesian Legal NLP Dataset for Contradiction Detection

This repository builds a structured Indonesian legal dataset for:
- legal NLP
- contradiction detection
- natural language inference (NLI)
- semantic similarity
- legal QA (RAG-based)
- legal knowledge graph

The pipeline converts legal PDF documents into hierarchical JSONL records:
- Document
- Chapter (Bab)
- Article (Pasal)
- Paragraph (Ayat)
- Item (Huruf/Angka)

## Repository Structure

```text
indonesian-legal-nlp-dataset/
├── data/
│   ├── raw/pdf/
│   ├── processed/
│   └── annotations/
├── scripts/
├── schema/
├── notebooks/
└── docs/
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Tesseract OCR is optional but recommended for scanned PDFs.

## Pipeline

Run from repository root:

1. Extract text from PDF:
```bash
python scripts/extract_pdf_text.py --input-dir data/raw/pdf --output data/processed/extracted_text.jsonl
```

2. Clean text:
```bash
python scripts/clean_text.py --input data/processed/extracted_text.jsonl --output data/processed/cleaned_text.jsonl
```

3. Segment legal hierarchy:
```bash
python scripts/segment_legal_text.py --input data/processed/cleaned_text.jsonl --output data/processed/segmented_units.jsonl
```

4. Build final dataset + NLI pairs:
```bash
python scripts/build_dataset.py \
  --input data/processed/segmented_units.jsonl \
  --output data/processed/legal_units.jsonl \
  --nli-output data/annotations/nli_pairs.jsonl
```

5. Validate schema and quality checks:
```bash
python scripts/validate_schema.py \
  --dataset data/processed/legal_units.jsonl \
  --nli-dataset data/annotations/nli_pairs.jsonl \
  --schema schema/legal_unit.schema.json \
  --nli-schema schema/nli_pair.schema.json
```

6. Generate statistics:
```bash
python scripts/generate_statistics.py \
  --dataset data/processed/legal_units.jsonl \
  --nli-dataset data/annotations/nli_pairs.jsonl \
  --extraction-log data/processed/extracted_text.jsonl \
  --output data/processed/statistics.json
```

## Outputs

- Main dataset: `data/processed/legal_units.jsonl`
- NLI pairs: `data/annotations/nli_pairs.jsonl`
- Validation report: `data/processed/validation_report.json`
- Statistics report: `data/processed/statistics.json`

## Legal Hierarchy Mapping

- UUD 1945 -> 1
- TAP MPR -> 2
- Undang-Undang / Perppu -> 3
- PP -> 4
- Perpres -> 5
- Permen / Lembaga -> 6
- Perda -> 7
- Putusan MK -> reference

## FAIR and Reproducibility

- FAIR guidelines: `docs/FAIR.md`
- Reproducibility notes: `docs/reproducibility.md`
- Data dictionary and field definitions: `DATA.md`

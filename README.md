# Indonesian Legal NLP Dataset for Contradiction Detection

This repository builds a structured Indonesian legal dataset for:
- legal NLP
- contradiction detection
- natural language inference (NLI) (manual annotation workflow)
- semantic similarity
- legal QA (RAG-based)
- legal knowledge graph

The automated pipeline converts legal PDF documents into hierarchical JSONL records:
- Document
- Chapter (Bab)
- Article (Pasal)
- Paragraph (Ayat)
- Item (Huruf/Angka)

## Repository Structure

```text
indonesian-legal-nlp-dataset/
|-- data/
|   |-- raw/pdf/
|   |-- processed/
|   `-- annotations/
|       |-- nli_manual/
|       |-- ontology_manual/
|       `-- formal_verification_manual/
|-- scripts/
|-- schema/
|-- notebooks/
`-- docs/
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

4. Build final corpus dataset:
```bash
python scripts/build_dataset.py \
  --input data/processed/segmented_units.jsonl \
  --output data/processed/legal_units.jsonl
```

5. Manual annotation stage (aligned with Proposal R.2.1):
- NLI labels are curated manually in `data/annotations/nli_manual/`
- Ontology reasoning artifacts are curated manually in `data/annotations/ontology_manual/`
- Formal verification artifacts (e.g., SMT/Z3 outputs) are curated manually in `data/annotations/formal_verification_manual/`

6. Validate schema and quality checks:
Corpus-only mode:
```bash
python scripts/validate_schema.py \
  --dataset data/processed/legal_units.jsonl \
  --schema schema/legal_unit.schema.json
```

Corpus + manual NLI mode:
```bash
python scripts/validate_schema.py \
  --dataset data/processed/legal_units.jsonl \
  --nli-dataset data/annotations/nli_manual/nli_pairs.manual.jsonl \
  --schema schema/legal_unit.schema.json \
  --nli-schema schema/nli_pair.schema.json
```

7. Generate statistics:
```bash
python scripts/generate_statistics.py \
  --dataset data/processed/legal_units.jsonl \
  --nli-dataset data/annotations/nli_manual/nli_pairs.manual.jsonl \
  --extraction-log data/processed/extracted_text.jsonl \
  --output data/processed/statistics.json
```

## Outputs

- Main dataset: `data/processed/legal_units.jsonl`
- NLI pairs (manual): `data/annotations/nli_manual/nli_pairs.manual.jsonl`
- Ontology reasoning artifacts (manual): `data/annotations/ontology_manual/`
- Formal verification artifacts (manual): `data/annotations/formal_verification_manual/`
- Validation report: `data/processed/validation_report.json`
- Statistics report: `data/processed/statistics.json`

## Annotation Policy (Important)

This repository follows the dissertation workflow in `01-PPT DCS 2025 - Proposal R.2.1.pptx`:
- Automated stage: corpus creation only (`extract -> clean -> segment -> build corpus`).
- Manual stage: NLI labeling, ontology reasoning annotations, and formal verification outputs.

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

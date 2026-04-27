# Reproducibility Guide

## Environment

- Python 3.10+ recommended
- Install dependencies from `requirements.txt`
- Optional system dependency: Tesseract OCR executable

## Determinism

- IDs are generated using deterministic SHA-1 hashes from structural fields.
- Automated pipeline stages are file-based and produce explicit intermediate artifacts.
- Validation and statistics scripts output JSON reports for traceability.

## Suggested Run Order

1. `extract_pdf_text.py`
2. `clean_text.py`
3. `segment_legal_text.py`
4. `build_dataset.py` (corpus only)
5. Manual annotation stages (NLI / ontology / formal verification)
6. `validate_schema.py`
7. `generate_statistics.py`

## Versioning Best Practice

- Commit scripts, schemas, and docs together.
- Store only sample JSONL in Git.
- Keep full generated datasets in release artifacts or object storage.
- Keep manual annotation decisions in versioned files with annotator notes.

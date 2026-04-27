# Manual Annotation Workflow (Proposal R.2.1)

This repository separates automated and manual stages:

- Automated: corpus building (`extract -> clean -> segment -> build corpus`).
- Manual: NLI labels, ontology links, and formal verification outcomes.

## 1) Prepare corpus baseline

Generate `data/processed/legal_units.jsonl` using pipeline scripts.

## 2) Manual NLI annotation

- Use template: `data/annotations/nli_manual/nli_pairs.manual.template.jsonl`
- Output file convention: `data/annotations/nli_manual/nli_pairs.manual.jsonl`
- Required final schema: `schema/nli_pair.schema.json`

## 3) Manual ontology reasoning annotation

- Use template: `data/annotations/ontology_manual/ontology_links.manual.template.jsonl`
- Relation types (project convention): `lex_superior`, `lex_specialis`, `exception`, `reference`

## 4) Manual formal verification records

- Use template: `data/annotations/formal_verification_manual/formal_verification.manual.template.jsonl`
- Store SMT-LIB/Z3 artifacts and interpretation notes per pair.

## 5) Validation

- Corpus only:
  - `python scripts/validate_schema.py --dataset data/processed/legal_units.jsonl --schema schema/legal_unit.schema.json`
- Corpus + manual NLI:
  - `python scripts/validate_schema.py --dataset data/processed/legal_units.jsonl --nli-dataset data/annotations/nli_manual/nli_pairs.manual.jsonl --schema schema/legal_unit.schema.json --nli-schema schema/nli_pair.schema.json`

## Notes

This workflow follows the architecture in `01-PPT DCS 2025 - Proposal R.2.1.pptx` where contradiction analysis layers (NLI, ontology reasoning, formal verification) are expert-driven.

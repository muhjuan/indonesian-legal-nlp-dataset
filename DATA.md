# Data Dictionary

## Main Dataset (`legal_units.jsonl`)

Each line is a JSON object with schema:

```json
{
  "unit_id": "string",
  "doc_id": "string",
  "title": "string",
  "reg_type": "string",
  "hierarchy_level": 3,
  "year": 2017,
  "number": "7",
  "chapter": "BAB II",
  "chapter_title": "PENDAFTARAN PEMILIH",
  "article": "Pasal 7",
  "paragraph": "(1)",
  "item": "a",
  "text": "string",
  "source_url": "https://...",
  "source_file": "uu_7_2017.pdf",
  "language": "id",
  "created_at": "2026-04-27T10:00:00Z"
}
```

Notes:
- `item` can be `null`.
- `hierarchy_level` follows legal hierarchy mapping.
- `created_at` is ISO-8601 UTC timestamp.

## Manual NLI Dataset (`nli_pairs.manual.jsonl`)

NLI is curated manually (not auto-generated). Final accepted records follow:

```json
{
  "pair_id": "string",
  "premise_id": "string",
  "hypothesis_id": "string",
  "premise": "string",
  "hypothesis": "string",
  "label": "entailment",
  "legal_issue": "string",
  "confidence": 0.91
}
```

Allowed labels:
- `entailment`
- `contradiction`
- `neutral`

## Manual Ontology Artifacts (`ontology_manual/`)

Recommended JSONL fields (project convention):

```json
{
  "relation_id": "string",
  "source_unit_id": "string",
  "target_unit_id": "string",
  "relation_type": "lex_superior | lex_specialis | exception | reference",
  "annotator": "string",
  "notes": "string"
}
```

## Manual Formal Verification Artifacts (`formal_verification_manual/`)

Recommended JSONL fields (project convention):

```json
{
  "verification_id": "string",
  "pair_id": "string",
  "smtlib_path": "string",
  "solver": "z3",
  "result": "SAT | UNSAT | UNKNOWN",
  "annotator": "string",
  "notes": "string"
}
```

## Data Quality Controls

Validation pipeline checks:
- duplicate IDs (`unit_id`, `pair_id`)
- schema compliance
- missing field check
- random sampling check

## Provenance Fields

Provenance is captured through:
- `source_url`
- `source_file`
- extraction and processing reports in `data/processed/*.json`

## Annotation Policy

Aligned with `01-PPT DCS 2025 - Proposal R.2.1.pptx`:
- Automated: corpus construction only.
- Manual: NLI annotation, ontology reasoning links, and formal verification outputs.

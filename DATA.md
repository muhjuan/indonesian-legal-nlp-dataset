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

## NLI Dataset (`nli_pairs.jsonl`)

Each line is a JSON object:

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

## Data Quality Controls

Validation pipeline checks:
- duplicate IDs (`unit_id`, `pair_id`)
- schema compliance
- missing fields
- random sample sanity checks

## Provenance Fields

Provenance is captured through:
- `source_url`
- `source_file`
- extraction and processing reports in `data/processed/*.json`

# FAIR Principles Compliance

## Findable
- Clear repository name and domain-specific scope.
- Stable file naming for datasets and schemas.
- Metadata fields include `doc_id`, `unit_id`, `source_file`, and `source_url`.

## Accessible
- Dataset format uses JSONL for broad interoperability.
- Scripts are CLI-based and reproducible in local environments.
- Documentation includes setup and execution instructions.

## Interoperable
- JSON schemas define strict field types and constraints.
- Language field is explicitly set (`language: "id"`).
- Final NLI labels follow standard NLI taxonomy and are curated manually.

## Reusable
- Data dictionary is documented in `DATA.md`.
- Source provenance fields are included per record.
- Validation and quality control scripts enforce consistency.
- Manual annotation protocol is documented in `docs/manual_annotation_workflow.md`.

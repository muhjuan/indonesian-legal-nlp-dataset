#!/usr/bin/env python
"""Validate dataset and NLI JSONL against schema plus quality checks."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

try:
    from jsonschema import ValidationError, validate
except Exception:  # pragma: no cover - optional runtime import
    ValidationError = Exception  # type: ignore[assignment]
    validate = None  # type: ignore[assignment]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_duplicates(records: list[dict[str, Any]], key: str) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for rec in records:
        val = str(rec.get(key, ""))
        if val in seen:
            duplicates.append(val)
        else:
            seen.add(val)
    return duplicates


def find_missing_fields(records: list[dict[str, Any]], required_fields: list[str]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for idx, rec in enumerate(records, start=1):
        missing = [f for f in required_fields if f not in rec or rec[f] is None or rec[f] == ""]
        # "item" is nullable in legal unit dataset.
        if "item" in missing:
            missing.remove("item")
        if missing:
            issues.append({"line": idx, "missing_fields": missing})
    return issues


def random_sampling_check(records: list[dict[str, Any]], sample_size: int) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if not records:
        return issues
    sample_size = min(sample_size, len(records))
    sampled = random.sample(records, sample_size)
    for rec in sampled:
        text = str(rec.get("text", "")).strip()
        if text and len(text) < 20:
            issues.append({"unit_id": rec.get("unit_id", ""), "issue": "text_too_short"})
    return issues


def validate_records_with_schema(records: list[dict[str, Any]], schema: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if validate is None:
        return issues
    for idx, rec in enumerate(records, start=1):
        try:
            validate(instance=rec, schema=schema)
        except ValidationError as exc:
            issues.append({"line": idx, "error": str(exc.message)})
    return issues


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate schema and quality controls.")
    parser.add_argument("--dataset", type=Path, default=Path("data/processed/legal_units.jsonl"))
    parser.add_argument("--nli-dataset", type=Path, default=Path("data/annotations/nli_pairs.jsonl"))
    parser.add_argument("--schema", type=Path, default=Path("schema/legal_unit.schema.json"))
    parser.add_argument("--nli-schema", type=Path, default=Path("schema/nli_pair.schema.json"))
    parser.add_argument("--sample-size", type=int, default=30)
    parser.add_argument("--output", type=Path, default=Path("data/processed/validation_report.json"))
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    dataset = read_jsonl(args.dataset)
    nli_dataset = read_jsonl(args.nli_dataset)
    legal_schema = read_json(args.schema)
    nli_schema = read_json(args.nli_schema)

    legal_required = list(legal_schema.get("required", []))
    nli_required = list(nli_schema.get("required", []))

    report = {
        "dataset_records": len(dataset),
        "nli_records": len(nli_dataset),
        "schema_issues": {
            "legal": validate_records_with_schema(dataset, legal_schema),
            "nli": validate_records_with_schema(nli_dataset, nli_schema),
        },
        "duplicate_issues": {
            "unit_id_duplicates": find_duplicates(dataset, "unit_id"),
            "pair_id_duplicates": find_duplicates(nli_dataset, "pair_id"),
        },
        "missing_field_issues": {
            "legal": find_missing_fields(dataset, legal_required),
            "nli": find_missing_fields(nli_dataset, nli_required),
        },
        "random_sampling_issues": random_sampling_check(dataset, args.sample_size),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    total_issues = (
        len(report["schema_issues"]["legal"])
        + len(report["schema_issues"]["nli"])
        + len(report["duplicate_issues"]["unit_id_duplicates"])
        + len(report["duplicate_issues"]["pair_id_duplicates"])
        + len(report["missing_field_issues"]["legal"])
        + len(report["missing_field_issues"]["nli"])
        + len(report["random_sampling_issues"])
    )
    print(f"Validation report -> {args.output}")
    print(f"Total issues found: {total_issues}")
    return 1 if total_issues > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())

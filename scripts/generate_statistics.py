#!/usr/bin/env python
"""Generate dataset statistics and processing success metrics."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def count_tokens(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+", text))


def compute_processing_success_rate(extraction_records: list[dict[str, Any]]) -> float:
    if not extraction_records:
        return 0.0
    success = sum(1 for rec in extraction_records if rec.get("success") is True)
    return round(success / len(extraction_records), 4)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate statistics for legal dataset.")
    parser.add_argument("--dataset", type=Path, default=Path("data/processed/legal_units.jsonl"))
    parser.add_argument("--nli-dataset", type=Path, default=Path("data/annotations/nli_pairs.jsonl"))
    parser.add_argument("--extraction-log", type=Path, default=Path("data/processed/extracted_text.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/statistics.json"))
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    dataset = read_jsonl(args.dataset)
    nli_dataset = read_jsonl(args.nli_dataset)
    extraction_records = read_jsonl(args.extraction_log)

    total_documents = len({rec.get("doc_id", "") for rec in dataset})
    total_pasal = len({(rec.get("doc_id", ""), rec.get("article", "")) for rec in dataset if rec.get("article")})
    total_ayat = len(
        {
            (rec.get("doc_id", ""), rec.get("article", ""), rec.get("paragraph", ""))
            for rec in dataset
            if rec.get("paragraph")
        }
    )
    total_tokens = sum(count_tokens(str(rec.get("text", ""))) for rec in dataset)

    stats = {
        "total_documents": total_documents,
        "total_units": len(dataset),
        "total_pasal": total_pasal,
        "total_ayat": total_ayat,
        "token_count": total_tokens,
        "total_nli_pairs": len(nli_dataset),
        "label_distribution": {
            "entailment": sum(1 for r in nli_dataset if r.get("label") == "entailment"),
            "contradiction": sum(1 for r in nli_dataset if r.get("label") == "contradiction"),
            "neutral": sum(1 for r in nli_dataset if r.get("label") == "neutral"),
        },
        "processing_success_rate": compute_processing_success_rate(extraction_records),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"Statistics -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

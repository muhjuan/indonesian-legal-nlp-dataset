#!/usr/bin/env python
"""Build final JSONL corpus dataset from segmented legal units.

Important design note (aligned with Proposal R.2.1):
- This script automates corpus construction only.
- NLI, ontology, and formal verification artifacts are curated manually.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def map_hierarchy_level(reg_type: str) -> int:
    """Map legal document type to hierarchy level."""
    norm = normalized(reg_type)
    mapping = {
        "uud 1945": 1,
        "tap mpr": 2,
        "undang undang": 3,
        "uu": 3,
        "perppu": 3,
        "pp": 4,
        "perpres": 5,
        "permen lembaga": 6,
        "permen": 6,
        "lembaga": 6,
        "perda": 7,
    }
    if "putusan mk" in norm:
        return 0  # reference only
    return mapping.get(norm, 99)


def stable_hash(parts: list[str], prefix: str) -> str:
    joined = "||".join(parts)
    digest = hashlib.sha1(joined.encode("utf-8")).hexdigest()[:14]
    return f"{prefix}-{digest}"


def build_legal_units(segmented_units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    created_at = utc_now_iso()
    units: list[dict[str, Any]] = []
    for rec in segmented_units:
        unit_id = stable_hash(
            [
                rec.get("doc_id", ""),
                rec.get("chapter", ""),
                rec.get("article", ""),
                rec.get("paragraph", ""),
                str(rec.get("item", "")),
                rec.get("text", ""),
            ],
            prefix="UNIT",
        )
        unit = {
            "unit_id": unit_id,
            "doc_id": rec.get("doc_id", ""),
            "title": rec.get("title", ""),
            "reg_type": rec.get("reg_type", ""),
            "hierarchy_level": map_hierarchy_level(rec.get("reg_type", "")),
            "year": rec.get("year") if rec.get("year") is not None else 0,
            "number": str(rec.get("number", "")),
            "chapter": rec.get("chapter", ""),
            "chapter_title": rec.get("chapter_title", ""),
            "article": rec.get("article", ""),
            "paragraph": rec.get("paragraph", ""),
            "item": rec.get("item", None),
            "text": rec.get("text", ""),
            "source_url": rec.get("source_url", ""),
            "source_file": rec.get("source_file", ""),
            "language": "id",
            "created_at": created_at,
        }
        units.append(unit)
    return units


def save_build_report(path: Path, units: list[dict[str, Any]]) -> None:
    report = {
        "generated_at": utc_now_iso(),
        "total_units": len(units),
        "total_docs": len({u["doc_id"] for u in units}),
        "annotation_policy": {
            "nli": "manual",
            "ontology_reasoning": "manual",
            "formal_verification": "manual",
            "note": "Only corpus construction is automated in this repository.",
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build final legal corpus dataset (automated corpus stage).")
    parser.add_argument("--input", type=Path, default=Path("data/processed/segmented_units.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/legal_units.jsonl"))
    parser.add_argument("--report-output", type=Path, default=Path("data/processed/build_report.json"))
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    segmented = read_jsonl(args.input)
    units = build_legal_units(segmented)

    write_jsonl(args.output, units)
    save_build_report(args.report_output, units)

    print(f"Wrote {len(units)} legal units -> {args.output}")
    print("NLI / ontology / formal verification artifacts are manual (not auto-generated).")
    print(f"Build report -> {args.report_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

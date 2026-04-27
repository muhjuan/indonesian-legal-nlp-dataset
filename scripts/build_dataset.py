#!/usr/bin/env python
"""Build final JSONL dataset and NLI pairs from segmented legal units."""

from __future__ import annotations

import argparse
import hashlib
import itertools
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


def token_set(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z0-9]+", text.lower()))


def has_negation(text: str) -> bool:
    return any(k in text.lower() for k in (" tidak ", " bukan ", " dilarang ", " kecuali "))


def infer_label(premise: str, hypothesis: str) -> tuple[str, float]:
    p_tokens = token_set(premise)
    h_tokens = token_set(hypothesis)
    if not p_tokens or not h_tokens:
        return "neutral", 0.4

    overlap = len(p_tokens & h_tokens) / max(1, len(p_tokens | h_tokens))
    p_neg = has_negation(f" {premise.lower()} ")
    h_neg = has_negation(f" {hypothesis.lower()} ")

    if overlap >= 0.40 and p_neg != h_neg:
        return "contradiction", min(0.95, 0.60 + overlap)
    if overlap >= 0.55 and p_neg == h_neg:
        return "entailment", min(0.95, 0.55 + overlap)
    return "neutral", max(0.45, overlap)


def infer_legal_issue(article: str, text: str) -> str:
    if article:
        return article
    if "pemilih" in text.lower():
        return "Pemilih"
    if "kpu" in text.lower():
        return "KPU"
    return "Isu Umum"


def generate_nli_pairs(units: list[dict[str, Any]], max_pairs: int) -> list[dict[str, Any]]:
    """Generate heuristic NLI pairs for quick contradiction baseline."""
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for u in units:
        key = (u.get("doc_id", ""), u.get("article", ""))
        grouped.setdefault(key, []).append(u)

    pairs: list[dict[str, Any]] = []
    for (_, article), article_units in grouped.items():
        for a, b in itertools.combinations(article_units, 2):
            if len(pairs) >= max_pairs:
                return pairs

            premise = a.get("text", "")
            hypothesis = b.get("text", "")
            label, confidence = infer_label(premise, hypothesis)
            pair_id = stable_hash([a["unit_id"], b["unit_id"], label], prefix="PAIR")
            pairs.append(
                {
                    "pair_id": pair_id,
                    "premise_id": a["unit_id"],
                    "hypothesis_id": b["unit_id"],
                    "premise": premise,
                    "hypothesis": hypothesis,
                    "label": label,
                    "legal_issue": infer_legal_issue(article, premise),
                    "confidence": round(float(confidence), 4),
                }
            )
    return pairs


def save_build_report(path: Path, units: list[dict[str, Any]], nli_pairs: list[dict[str, Any]]) -> None:
    report = {
        "generated_at": utc_now_iso(),
        "total_units": len(units),
        "total_docs": len({u["doc_id"] for u in units}),
        "total_nli_pairs": len(nli_pairs),
        "labels": {
            "entailment": sum(1 for p in nli_pairs if p["label"] == "entailment"),
            "contradiction": sum(1 for p in nli_pairs if p["label"] == "contradiction"),
            "neutral": sum(1 for p in nli_pairs if p["label"] == "neutral"),
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build final legal dataset and NLI pairs.")
    parser.add_argument("--input", type=Path, default=Path("data/processed/segmented_units.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/legal_units.jsonl"))
    parser.add_argument("--nli-output", type=Path, default=Path("data/annotations/nli_pairs.jsonl"))
    parser.add_argument("--max-nli-pairs", type=int, default=1000)
    parser.add_argument("--report-output", type=Path, default=Path("data/processed/build_report.json"))
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    segmented = read_jsonl(args.input)
    units = build_legal_units(segmented)
    nli_pairs = generate_nli_pairs(units, max_pairs=args.max_nli_pairs)

    write_jsonl(args.output, units)
    write_jsonl(args.nli_output, nli_pairs)
    save_build_report(args.report_output, units, nli_pairs)

    print(f"Wrote {len(units)} legal units -> {args.output}")
    print(f"Wrote {len(nli_pairs)} NLI pairs -> {args.nli_output}")
    print(f"Build report -> {args.report_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

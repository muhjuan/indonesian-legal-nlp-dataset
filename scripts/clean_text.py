#!/usr/bin/env python
"""Clean extracted legal text while preserving legal meaning markers."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

# Core lexical markers that must remain intact in cleaned text.
PRESERVE_TERMS = {"wajib", "tidak", "dilarang", "kecuali"}


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


def remove_page_numbers(text: str) -> str:
    # Matches standalone page number lines such as "12" or "- 12 -".
    text = re.sub(r"(?m)^\s*[-–]?\s*\d{1,4}\s*[-–]?\s*$", "", text)
    return text


def remove_common_noise(text: str) -> str:
    # Remove common watermark/header/footer tokens.
    patterns = [
        r"(?i)www\.[^\s]+",
        r"(?i)jdih\.[^\s]+",
        r"(?i)salinan\s+resmi",
        r"(?i)lembaran\s+negara\s+republik\s+indonesia",
        r"(?i)berita\s+negara\s+republik\s+indonesia",
    ]
    out = text
    for pat in patterns:
        out = re.sub(pat, "", out)
    return out


def normalize_whitespace(text: str) -> str:
    # Normalize line endings and collapse repeated spaces.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def merge_broken_lines(text: str) -> str:
    """Join lines broken by OCR/PDF extraction while keeping legal structure lines."""
    lines = [ln.strip() for ln in text.split("\n")]
    merged: list[str] = []

    heading_re = re.compile(r"^(BAB\s+[IVXLCDM]+|Pasal\s+\d+[A-Za-z]?|\(\d+[A-Za-z]?\)|[a-z]\.|[0-9]+\.)\b", re.IGNORECASE)

    for line in lines:
        if not line:
            merged.append("")
            continue
        if not merged:
            merged.append(line)
            continue
        prev = merged[-1]
        if not prev:
            merged.append(line)
            continue
        if heading_re.match(line):
            merged.append(line)
            continue

        # Join likely wrapped line when previous line is not sentence-ending.
        if prev[-1] not in ".;:!?":
            merged[-1] = f"{prev} {line}"
        else:
            merged.append(line)

    return "\n".join(merged)


def ensure_preserve_terms(cleaned_text: str, original_text: str) -> dict[str, bool]:
    """Signal if mandatory legal markers disappeared during cleaning."""
    flags: dict[str, bool] = {}
    clean_lower = cleaned_text.lower()
    original_lower = original_text.lower()
    for term in PRESERVE_TERMS:
        flags[term] = (term in original_lower) and (term in clean_lower)
    return flags


def clean_text(text: str) -> str:
    out = text
    out = remove_page_numbers(out)
    out = remove_common_noise(out)
    out = normalize_whitespace(out)
    out = merge_broken_lines(out)
    out = normalize_whitespace(out)
    return out


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Clean extracted legal text.")
    parser.add_argument("--input", type=Path, default=Path("data/processed/extracted_text.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/cleaned_text.jsonl"))
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    records = read_jsonl(args.input)
    out_records: list[dict[str, Any]] = []

    for rec in records:
        original = rec.get("text", "") or ""
        cleaned = clean_text(original)
        preserve_flags = ensure_preserve_terms(cleaned, original)
        rec_out = dict(rec)
        rec_out["text_clean"] = cleaned
        rec_out["cleaning"] = {
            "original_chars": len(original),
            "cleaned_chars": len(cleaned),
            "preserve_terms_ok": preserve_flags,
        }
        out_records.append(rec_out)

    write_jsonl(args.output, out_records)
    print(f"Cleaned {len(out_records)} documents -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

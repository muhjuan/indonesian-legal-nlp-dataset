#!/usr/bin/env python
"""Segment cleaned legal text into chapter/article/paragraph/item hierarchy."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CHAPTER_RE = re.compile(r"^BAB\s+([IVXLCDM]+)\b", re.IGNORECASE)
ARTICLE_RE = re.compile(r"^Pasal\s+(\d+[A-Za-z]?)\b", re.IGNORECASE)
PARAGRAPH_RE = re.compile(r"^\((\d+[A-Za-z]?)\)\s*(.*)$")
ITEM_ALPHA_RE = re.compile(r"^([a-z])\.\s*(.*)$")
ITEM_NUM_RE = re.compile(r"^(\d+)\.\s*(.*)$")


@dataclass
class Context:
    chapter: str = ""
    chapter_title: str = ""
    article: str = ""
    paragraph: str = ""
    item: str | None = None


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


def is_probable_chapter_title(line: str) -> bool:
    """Heuristic: uppercase line after BAB heading."""
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("Pasal"):
        return False
    alpha = re.sub(r"[^A-Za-z]", "", stripped)
    return bool(alpha) and alpha.isupper()


def build_unit(base: dict[str, Any], ctx: Context, text: str, idx: int) -> dict[str, Any]:
    return {
        "segment_index": idx,
        "doc_id": base.get("doc_id", ""),
        "title": base.get("title", ""),
        "reg_type": base.get("reg_type", ""),
        "year": base.get("year"),
        "number": base.get("number", ""),
        "chapter": ctx.chapter,
        "chapter_title": ctx.chapter_title,
        "article": ctx.article,
        "paragraph": ctx.paragraph,
        "item": ctx.item,
        "text": text.strip(),
        "source_url": base.get("source_url", ""),
        "source_file": base.get("source_file", ""),
        "language": "id",
    }


def segment_one_document(doc: dict[str, Any]) -> list[dict[str, Any]]:
    text = doc.get("text_clean") or doc.get("text") or ""
    lines = [ln.strip() for ln in text.split("\n")]
    ctx = Context()
    units: list[dict[str, Any]] = []
    buffer: list[str] = []
    idx = 0
    chapter_just_set = False

    def flush_buffer() -> None:
        nonlocal idx, buffer
        payload = " ".join([x for x in buffer if x]).strip()
        if payload and ctx.article:
            idx += 1
            units.append(build_unit(doc, ctx, payload, idx))
        buffer = []

    for line in lines:
        if not line:
            continue

        chapter_match = CHAPTER_RE.match(line)
        if chapter_match:
            flush_buffer()
            ctx.chapter = f"BAB {chapter_match.group(1).upper()}"
            ctx.chapter_title = ""
            ctx.article = ""
            ctx.paragraph = ""
            ctx.item = None
            chapter_just_set = True
            continue

        if chapter_just_set and is_probable_chapter_title(line):
            ctx.chapter_title = line
            chapter_just_set = False
            continue
        chapter_just_set = False

        article_match = ARTICLE_RE.match(line)
        if article_match:
            flush_buffer()
            ctx.article = f"Pasal {article_match.group(1)}"
            ctx.paragraph = ""
            ctx.item = None
            remainder = line[article_match.end() :].strip(" -:")
            if remainder:
                buffer.append(remainder)
            continue

        paragraph_match = PARAGRAPH_RE.match(line)
        if paragraph_match:
            flush_buffer()
            ctx.paragraph = f"({paragraph_match.group(1)})"
            ctx.item = None
            remainder = paragraph_match.group(2).strip()
            if remainder:
                buffer.append(remainder)
            continue

        item_alpha = ITEM_ALPHA_RE.match(line)
        if item_alpha:
            flush_buffer()
            ctx.item = item_alpha.group(1)
            remainder = item_alpha.group(2).strip()
            if remainder:
                buffer.append(remainder)
            continue

        item_num = ITEM_NUM_RE.match(line)
        if item_num:
            flush_buffer()
            ctx.item = item_num.group(1)
            remainder = item_num.group(2).strip()
            if remainder:
                buffer.append(remainder)
            continue

        # Regular content line belongs to current unit context.
        if ctx.article:
            buffer.append(line)

    flush_buffer()
    return units


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Segment cleaned legal text into hierarchy units.")
    parser.add_argument("--input", type=Path, default=Path("data/processed/cleaned_text.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/segmented_units.jsonl"))
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    docs = read_jsonl(args.input)
    all_units: list[dict[str, Any]] = []
    for doc in docs:
        all_units.extend(segment_one_document(doc))

    write_jsonl(args.output, all_units)
    print(f"Segmented {len(docs)} docs into {len(all_units)} units -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

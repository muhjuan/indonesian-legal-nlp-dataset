#!/usr/bin/env python
"""Extract text from Indonesian legal PDFs with OCR fallback."""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

try:
    import pytesseract
except Exception:  # pragma: no cover - optional dependency at runtime
    pytesseract = None  # type: ignore[assignment]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_doc_metadata(pdf_path: Path) -> dict[str, Any]:
    """Infer minimal legal metadata from filename patterns."""
    stem = pdf_path.stem.lower()
    year_match = re.search(r"(19|20)\d{2}", stem)
    number_match = re.search(r"(?:no|nomor|nr|n)\s*[_-]?(\d+)", stem)
    if not number_match:
        number_match = re.search(r"_(\d{1,3})_(?:19|20)\d{2}", stem)

    reg_type = "Unknown"
    if "uud1945" in stem or "uud_1945" in stem or "uud" in stem:
        reg_type = "UUD 1945"
    elif "tap_mpr" in stem or "tapmpr" in stem:
        reg_type = "TAP MPR"
    elif "perppu" in stem:
        reg_type = "Perppu"
    elif stem.startswith("uu") or "undang" in stem:
        reg_type = "Undang-Undang"
    elif stem.startswith("pp_") or re.search(r"\bpp\b", stem):
        reg_type = "PP"
    elif "perpres" in stem:
        reg_type = "Perpres"
    elif "permen" in stem or "kpu" in stem or "bawaslu" in stem:
        reg_type = "Permen/Lembaga"
    elif "perda" in stem:
        reg_type = "Perda"
    elif "mk" in stem or "puu" in stem:
        reg_type = "Putusan MK"

    return {
        "doc_id": f"DOC-{pdf_path.stem.upper().replace(' ', '_')}",
        "title": pdf_path.stem.replace("_", " ").strip(),
        "reg_type": reg_type,
        "year": int(year_match.group(0)) if year_match else None,
        "number": number_match.group(1) if number_match else "",
        "source_file": pdf_path.name,
    }


def extract_native_text(pdf_path: Path) -> str:
    """Extract embedded text directly from PDF objects."""
    text_parts: list[str] = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text_parts.append(page.get_text("text"))
    return "\n".join(text_parts).strip()


def extract_ocr_text(pdf_path: Path, dpi: int = 300) -> str:
    """OCR each PDF page using Tesseract via temporary PNG files."""
    if pytesseract is None:
        raise RuntimeError("pytesseract is not installed; cannot run OCR fallback.")

    text_parts: list[str] = []
    with tempfile.TemporaryDirectory(prefix="ocr_pdf_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        with fitz.open(pdf_path) as doc:
            for i, page in enumerate(doc):
                pix = page.get_pixmap(dpi=dpi)
                image_path = tmp_path / f"page_{i+1:04d}.png"
                pix.save(image_path.as_posix())
                text = pytesseract.image_to_string(image_path.as_posix(), lang="ind+eng")
                text_parts.append(text)

    return "\n".join(text_parts).strip()


def should_use_ocr(native_text: str, force_ocr: bool, min_chars: int) -> bool:
    """Decide OCR fallback using manual override or minimum text threshold."""
    if force_ocr:
        return True
    return len(native_text) < min_chars


def process_pdf(pdf_path: Path, source_url: str, force_ocr: bool, min_chars: int) -> dict[str, Any]:
    """Process one PDF file and return extraction record."""
    meta = parse_doc_metadata(pdf_path)
    record: dict[str, Any] = {
        **meta,
        "source_url": source_url,
        "language": "id",
        "extracted_at": utc_now_iso(),
        "success": False,
        "extraction_method": None,
        "text": "",
        "error": "",
    }

    try:
        native_text = extract_native_text(pdf_path)
        if should_use_ocr(native_text, force_ocr=force_ocr, min_chars=min_chars):
            ocr_text = extract_ocr_text(pdf_path)
            record["text"] = ocr_text
            record["extraction_method"] = "ocr_tesseract"
        else:
            record["text"] = native_text
            record["extraction_method"] = "native_pymupdf"
        record["success"] = bool(record["text"].strip())
    except Exception as exc:  # noqa: BLE001 - keep robust for dataset pipeline
        record["error"] = str(exc)

    return record


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract text from PDF with OCR fallback.")
    parser.add_argument("--input-dir", type=Path, default=Path("data/raw/pdf"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/extracted_text.jsonl"))
    parser.add_argument("--source-url", type=str, default="")
    parser.add_argument("--force-ocr", action="store_true")
    parser.add_argument("--min-native-chars", type=int, default=200)
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    pdf_files = sorted(args.input_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {args.input_dir}")
        return 0

    records: list[dict[str, Any]] = []
    for pdf in pdf_files:
        url = args.source_url or f"file://{pdf.name}"
        records.append(process_pdf(pdf, source_url=url, force_ocr=args.force_ocr, min_chars=args.min_native_chars))

    write_jsonl(args.output, records)
    ok = sum(1 for r in records if r.get("success"))
    print(f"Extracted {ok}/{len(records)} documents -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

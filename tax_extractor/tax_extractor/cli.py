#!/usr/bin/env python3
"""
Command-line interface.

Examples:
  python cli.py myW2.pdf -o out.xlsx
  python cli.py ./tax_pdfs/ -o 2024_summary.xlsx
  python cli.py form1040.pdf --engine llm
  python cli.py scanned.pdf --ocr
"""

from __future__ import annotations
import argparse
import sys

from tax_extractor import process_path, write_workbook


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Extract W-2 / 1040 PDFs into an Excel workbook.")
    p.add_argument("input", help="PDF file, directory, or glob of PDFs")
    p.add_argument("-o", "--output", default="tax_extract.xlsx",
                   help="output .xlsx path (default: tax_extract.xlsx)")
    p.add_argument("--engine", choices=["auto", "positional", "llm"],
                   default="auto",
                   help="extraction engine (default: auto — local first, "
                        "LLM fallback if available)")
    p.add_argument("--ocr", action="store_true",
                   help="force OCR (for scanned PDFs)")
    p.add_argument("--form", choices=["W-2", "1040"], default=None,
                   help="skip auto-detection and force a form type")
    args = p.parse_args(argv)

    try:
        results = process_path(
            args.input, engine=args.engine,
            force_ocr=args.ocr, form_type=args.form,
        )
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    write_workbook(results, args.output)

    print(f"Processed {len(results)} file(s) -> {args.output}\n")
    for fr in results:
        have = sum(1 for f in fr.fields.values() if f.value not in (None, ""))
        print(f"  {fr.filename}: {fr.form_type} "
              f"[{fr.engine}/{fr.source}] "
              f"{have}/{len(fr.fields)} fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

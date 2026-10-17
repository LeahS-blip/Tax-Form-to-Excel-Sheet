#!/usr/bin/env python3
"""
MCP server for tax_extractor ("tax-form-to-excel").

Exposes the extractor as tools so that, inside an MCP client (e.g. Claude
Desktop), you can say "extract this W-2 to a spreadsheet" and point at a PDF.

Tools:
  - list_supported_forms(): the forms and fields the server can parse
  - extract_tax_form(path, engine, form_type): returns parsed fields as JSON
  - extract_to_excel(input_path, output_path, engine, form_type): writes .xlsx

Run:
  pip install pdfplumber openpyxl "mcp[cli]"
  python mcp_server.py            # stdio transport

Claude Desktop setup: see references/claude-desktop-setup.md.

PRIVACY: with engine="positional" everything runs locally. engine="auto" (the
default) stays local unless ANTHROPIC_API_KEY is set AND local extraction comes
up short. engine="llm" always sends document text to the Anthropic API.
"""

from __future__ import annotations
import json
import os
import sys

# Make the bundled package importable no matter what the working directory is.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    raise SystemExit(
        "The MCP SDK is required to run the server:\n"
        '    pip install "mcp[cli]"\n'
    )

from tax_extractor import process_path, write_workbook
from tax_extractor.schemas import SCHEMAS

mcp = FastMCP("tax-form-to-excel")


def _fields_to_dict(fr):
    return {
        "filename": fr.filename,
        "form_type": fr.form_type,
        "text_source": fr.source,
        "engine": fr.engine,
        "fields": {
            k: {"label": v.label, "value": v.value, "confidence": v.confidence}
            for k, v in fr.fields.items()
        },
    }


def _missing(path: str) -> bool:
    return not os.path.exists(path) and not any(c in path for c in "*?[")


@mcp.tool()
def list_supported_forms() -> str:
    """List the tax forms this server can parse and the fields it extracts."""
    return json.dumps({name: [f.label for f in schema.fields]
                       for name, schema in SCHEMAS.items()}, indent=2)


@mcp.tool()
def extract_tax_form(path: str, engine: str = "auto",
                     form_type: str | None = None) -> str:
    """Extract fields from one PDF (or a folder/glob of PDFs) and return JSON.

    Args:
        path: path to a .pdf, a directory of PDFs, or a glob pattern.
        engine: "auto" (local first, LLM fallback if available),
                "positional" (local only), or "llm" (Anthropic API).
        form_type: optionally force a form name from list_supported_forms
                   (e.g. "W-2", "1099-NEC", "Schedule K-1") instead of
                   auto-detecting.
    """
    if _missing(path):
        return json.dumps({"error": f"path not found: {path}"})
    try:
        results = process_path(path, engine=engine, form_type=form_type)
    except Exception as e:
        return json.dumps({"error": str(e)})
    return json.dumps([_fields_to_dict(r) for r in results], indent=2)


@mcp.tool()
def extract_to_excel(input_path: str, output_path: str,
                     engine: str = "auto",
                     form_type: str | None = None) -> str:
    """Extract one or more tax PDFs and write a formatted .xlsx workbook.

    Args:
        input_path: a .pdf, a directory of PDFs, or a glob pattern.
        output_path: where to write the .xlsx file (folders are created).
        engine: "auto", "positional", or "llm".
        form_type: optionally force a form name from list_supported_forms
                   (e.g. "W-2", "1099-NEC", "Schedule K-1") instead of
                   auto-detecting.

    Returns a short JSON summary including the output path and per-form
    field coverage so the result can be sanity-checked.
    """
    if _missing(input_path):
        return json.dumps({"error": f"path not found: {input_path}"})
    try:
        results = process_path(input_path, engine=engine, form_type=form_type)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        write_workbook(results, output_path)
    except Exception as e:
        return json.dumps({"error": str(e)})
    summary = [{
        "filename": r.filename, "form_type": r.form_type, "engine": r.engine,
        "fields_found": sum(1 for f in r.fields.values()
                            if f.value not in (None, "")),
        "fields_total": len(r.fields),
    } for r in results]
    return json.dumps({"output": os.path.abspath(output_path),
                       "forms": summary}, indent=2)


if __name__ == "__main__":
    mcp.run()

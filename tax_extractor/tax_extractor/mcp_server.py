#!/usr/bin/env python3
"""
MCP server wrapper for tax_extractor.

Exposes the extractor as tools so you can, inside an MCP client (e.g. Claude
Desktop), say "extract this W-2 to a spreadsheet" and point at a PDF.

Tools:
  - extract_tax_form(path, engine, form_type): returns the parsed fields as JSON
  - extract_to_excel(input_path, output_path, engine): writes an .xlsx and
    returns the path
  - list_supported_forms(): what the server can parse

Run:
  pip install "mcp[cli]"
  python mcp_server.py            # stdio transport

Claude Desktop config (claude_desktop_config.json):
  {
    "mcpServers": {
      "tax-form-to-excel": {
        "command": "python",
        "args": ["/absolute/path/to/tax_extractor/mcp_server.py"]
      }
    }
  }

PRIVACY NOTE: with engine="positional" (the default) everything runs locally.
engine="llm" sends document text to the Anthropic API; only use it if that's
acceptable for the PII in these forms.
"""

from __future__ import annotations
import json
import os

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


@mcp.tool()
def list_supported_forms() -> str:
    """List the tax forms this server can parse and the fields it extracts."""
    out = {}
    for name, schema in SCHEMAS.items():
        out[name] = [f.label for f in schema.fields]
    return json.dumps(out, indent=2)


@mcp.tool()
def extract_tax_form(path: str, engine: str = "auto",
                     form_type: str | None = None) -> str:
    """Extract fields from one PDF (or a folder/glob of PDFs) and return JSON.

    Args:
        path: path to a .pdf, a directory of PDFs, or a glob pattern.
        engine: "auto" (local first, LLM fallback if available),
                "positional" (local only), or "llm" (Anthropic API).
        form_type: optionally force "W-2" or "1040" instead of auto-detecting.
    """
    if not os.path.exists(path) and not any(c in path for c in "*?["):
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
        output_path: where to write the .xlsx file.
        engine: "auto", "positional", or "llm".
        form_type: optionally force "W-2" or "1040".

    Returns a short JSON summary including the output path and per-file
    field coverage so the result can be sanity-checked.
    """
    try:
        results = process_path(input_path, engine=engine, form_type=form_type)
        write_workbook(results, output_path)
    except Exception as e:
        return json.dumps({"error": str(e)})
    summary = [{
        "filename": r.filename, "form_type": r.form_type,
        "fields_found": sum(1 for f in r.fields.values()
                            if f.value not in (None, "")),
        "fields_total": len(r.fields),
    } for r in results]
    return json.dumps({"output": output_path, "files": summary}, indent=2)


if __name__ == "__main__":
    mcp.run()

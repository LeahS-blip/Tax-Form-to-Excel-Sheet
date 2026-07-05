# Tax Form to Excel Sheet

Turn tax-form PDFs (W-2, 1040, 1099-NEC/MISC/INT/DIV/R, Schedule C/E, K-1) into a
formatted Excel workbook — automatically detecting the form type and flagging
low-confidence values for review. Runs locally; can be driven from Claude Desktop
as an MCP server, from the command line, or by dragging PDFs onto a Windows icon.

```
PDF ─▶ text (pdfplumber, OCR fallback) ─▶ detect form ─▶ extract fields ─▶ Excel (openpyxl)
```

## What it does

- **Auto-detects** the form and extracts the key fields into a workbook: a
  Summary tab plus one detail tab per form.
- **Splits combined packets** — a single PDF with a 1040 plus schedules and K-1s
  is broken into separate forms.
- **Flags for review** — low-confidence cells are amber, missing ones red.
  *This is an extraction aid, not a filing tool; always verify the numbers.*
- **Local by default** — nothing leaves the machine. An optional LLM engine
  (Anthropic API) handles messy K-1s / unknown layouts but sends text off-device.

## Three ways to use it

1. **Claude Desktop (MCP server `tax-form-to-excel`)** — say "extract these to a
   spreadsheet." See `README - Connect Tax Form to Excel Sheet to Claude.md`.
2. **Drag-and-drop** — drop PDFs onto `Extract PDF (drag here).bat`.
3. **Command line** —
   `python tax_extractor/tax_extractor/cli.py myW2.pdf -o out.xlsx`

## Install

```
pip install pdfplumber openpyxl "mcp[cli]"
```

Optional: `anthropic` (LLM engine), `pytesseract` + `pdf2image` (OCR for scans).

## Privacy

Tax forms contain SSNs, EINs, names, and wages. The default engine and OCR run
entirely on your machine. The client-data folders (`Drop tax forms here/`,
`Extracted workbooks/`) are git-ignored and must never be committed.

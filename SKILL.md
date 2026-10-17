---
name: tax-form-to-excel
description: Extracts data from US tax-form PDFs (W-2, 1040, 1099-NEC/MISC/INT/DIV/R, Schedule C, Schedule E, Schedule K-1) into a formatted Excel workbook with a Summary tab, per-form detail tabs, and amber/red flags on values to verify. Use when the user asks to pull numbers out of tax forms, put W-2s or 1099s into a spreadsheet, tabulate a client's tax packet, or turn tax PDFs into Excel.
argument-hint: <pdf, folder of pdfs, or glob> [output.xlsx]
---

# Tax Form to Excel

Turns tax-form PDFs into an `.xlsx` workbook. It detects the form type,
splits combined packets into separate forms, extracts the key boxes, and
flags low-confidence or missing values for human review. By default it runs
entirely on the local machine.

## When to use

- "Put these W-2s in a spreadsheet"
- "Extract this client's 1040 packet to Excel"
- "What are the box 1 and box 2 amounts on these 1099s?"
- Any request to read numbers off W-2, 1040, 1099, Schedule C/E, or K-1 PDFs

## When NOT to use

- Preparing or filing a return, or giving tax advice. This skill only reads
  forms.
- Non-tax PDFs (invoices, bank statements). Use a general PDF tool instead.
- Writing values *into* a fillable PDF.

## Setup (once)

```bash
pip install -r requirements.txt     # pdfplumber, openpyxl, mcp
```

All paths below are relative to this skill's folder.

## How to run it

Prefer the MCP tools if the `tax-form-to-excel` server is connected (tools
named `mcp__tax-form-to-excel__*`). Otherwise use the CLI.

### Option A — MCP tools

1. `list_supported_forms()` shows which forms and fields are available.
2. `extract_to_excel(input_path, output_path)` writes the workbook and returns
   per-form field coverage.
3. `extract_tax_form(path)` returns the fields as JSON without writing a file.
   Use it when the user wants answers in chat rather than a spreadsheet.

### Option B — CLI

```bash
python scripts/cli.py <pdf | folder | "glob/*.pdf"> -o <output.xlsx>
```

Useful flags:

| Flag | Effect |
|---|---|
| `--form "Schedule K-1"` | Skip auto-detection and force a form type |
| `--ocr` | Force OCR for scanned PDFs (needs `pytesseract`, `pdf2image`, Tesseract, Poppler) |
| `--engine positional` | Local only, never calls an API |
| `--engine llm` | Use the Anthropic API (needs `anthropic` + `ANTHROPIC_API_KEY`) |

Example:

```bash
python scripts/cli.py assets/sample_w2.pdf -o out/sample.xlsx
# Processed 1 form(s) -> out/sample.xlsx
#   sample_w2.pdf: W-2 [positional/native] 20/21 fields
```

## Procedure

1. **Confirm inputs.** Get the PDF path(s) and where to save the workbook. If
   no output path is given, save it next to the input as
   `<name>_extracted.xlsx`.
2. **Run the extraction** (Option A or B). Point it at a folder to batch many
   forms into one workbook.
3. **Report results.** For each form, give the detected type, the engine used,
   and `found/total` fields. Call out any form with low coverage (under about
   70%) and any red (missing) fields.
4. **Remind the user to verify.** Amber cells are low confidence and red cells
   were not found. These must be checked against the PDF before anyone relies
   on them.
5. **If a form wasn't recognized or coverage is poor**, offer the next step:
   force the type with `--form`, use `--ocr` for scans, or enable the LLM engine
   (after the privacy check below).

## Privacy rules (important)

Tax forms contain SSNs, EINs, names, addresses, and income.

- The default `auto` engine stays local **unless** `ANTHROPIC_API_KEY` is set,
  in which case it may send weak or unknown forms to the Anthropic API.
- **Never** switch to `--engine llm`, or set an API key, without the user's
  explicit OK to send document text off-device.
- Don't paste full SSNs or EINs into chat summaries unless the user asks.
  Refer to forms by filename and form type instead.
- Never commit client PDFs or extracted workbooks to version control. The
  `.gitignore` already excludes `Drop tax forms here/`, `Extracted workbooks/`
  and `*_extracted.xlsx`.

## Output format

- **Summary** sheet: one table per form type, one row per form, headline
  amounts (e.g. W-2 wages and withholding, 1040 AGI / tax / refund).
- One **detail** sheet per form: Field, Value, Confidence, Note.
- Money values are numbers formatted `#,##0.00`, ready for formulas.

## Limits

- Several forms of the same type back to back in one PDF (e.g. three K-1s)
  merge into one. Split the PDF first or verify the result.
- The local parser is tuned to standard IRS layouts. Payroll-vendor renders
  (ADP, Paychex, Gusto) may need the LLM engine.
- Forms without a definition (1099-B, 1098, W-2G, …) need the LLM engine.

## References

- `references/forms-and-engines.md`: full field list, engine behaviour,
  limits, how to add a form.
- `references/claude-desktop-setup.md`: connecting the MCP server to Claude
  Desktop or Claude Code.
- `assets/sample_w2.pdf`, `assets/sample_1040.pdf`: synthetic test forms
  containing fake data only.

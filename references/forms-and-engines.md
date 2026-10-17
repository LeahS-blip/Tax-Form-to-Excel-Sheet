# Supported forms, engines, and limits

## Detection is automatic

You don't say what a file is. The extractor reads each page's text, matches it
against each form's signature phrases, and picks the form type itself. A
combined PDF (a 1040 plus schedules and K-1s) is **split page by page** into
separate forms, each with its own tab.

## Forms with built-in definitions

| Form | Layout | Key fields |
|---|---|---|
| **W-2** | grid | SSN, EIN, employer/employee names, boxes 1–8, 10–12, 15–20 |
| **1040** | row | wages, interest, dividends, AGI, deduction, taxable income, tax, withholding, refund / owed |
| **Schedule C** | row | proprietor, business, gross receipts, COGS, gross income, total expenses, net profit |
| **Schedule E** | row | rents, royalties, depreciation, expenses, total income / loss |
| **Schedule K-1** (1065 / 1120-S / 1041) | mixed | entity + recipient names and IDs, boxes 1–14, distributions, ending capital |
| **1099-NEC / MISC / INT / DIV / R** | grid | payer / recipient, main income boxes, federal withholding |

Call `list_supported_forms` (or ask Claude "list the supported tax forms") for
the exact field list per form.

## Engines

| engine | where it runs | best for | privacy |
|---|---|---|---|
| `positional` | local | standard IRS layouts: W-2, 1040, 1099s, Schedule C/E | fully on-device |
| `llm` | Anthropic API | K-1s, vendor / odd layouts, new tax years, **forms with no definition** (1099-B, 1098, W-2G, …) | sends text off-device |
| `auto` (default) | local first; LLM only if local finds < 50% of fields or the form is unknown, **and** an API key is set | everyday use | local unless it falls back |

Without an API key, `auto` behaves exactly like `positional`. Unrecognized
forms then return an error asking you to pass `form_type` or enable the LLM.

### Enabling the LLM engine

1. Create an Anthropic API key at https://console.anthropic.com. It's billed
   per use and separate from a Claude subscription; tax-form text is small, so
   each document costs very little.
2. `pip install anthropic` into the same Python the server uses.
3. Set `ANTHROPIC_API_KEY` (for Claude Desktop, put it in the server's `env`
   block; see [claude-desktop-setup.md](claude-desktop-setup.md)).
4. Optional: set `TAX_EXTRACTOR_MODEL` to override the model
   (default `claude-sonnet-4-6`).

## Reading the workbook

- **Summary** tab: one table per form type, one row per form, headline numbers.
- **Detail** tab per form: Field / Value / Confidence / Note.
- **Amber** rows have low confidence (< 0.5), so verify them. **Red** rows were
  not found, so check them manually.
- The sub-header on each detail tab shows the text source (`native` / `ocr`)
  and engine (`positional` / `llm`).

## Known limits

- **Same-type forms back to back merge.** Three K-1s in a row in one PDF are
  read as one K-1. Split such PDFs first, or verify the result.
- The positional parser is tuned to **standard IRS layouts**. Payroll-vendor
  renders (ADP, Paychex, Gusto) and state e-file printouts shuffle boxes
  around; use the LLM engine there.
- **1040 line numbers shift between years.** Fields anchor on label text
  ("adjusted gross income"), not line numbers, but unusual years may need a
  new anchor.
- Scanned PDFs need OCR (`pytesseract` + `pdf2image` + Tesseract/Poppler) or
  the LLM engine.
- **This is an extraction aid, not a filing tool, and it gives no tax advice.**
  Always check the first few extractions of each new form type against the
  source PDF.

## Extending

- **Add a field:** append a `Field(...)` to the form's schema in
  `scripts/tax_extractor/schemas.py` with one or more lowercase `anchors`
  (label fragments printed on the form).
- **Add a form:** create a `FormSchema` with `detect` phrases and a `layout`
  (`"grid"` = value below label, `"row"` = value right of label), register it
  in `SCHEMAS`, and optionally add headline keys to `_SUMMARY_FIELDS` in
  `writer.py`.

## Architecture

```
scripts/
├── cli.py                # command-line entry point
├── mcp_server.py         # MCP server (tax-form-to-excel)
├── make_sample.py        # regenerates the fake sample PDFs in assets/
└── tax_extractor/
    ├── schemas.py        # field definitions + form detection
    ├── text_extract.py   # PDF -> text + positioned words (native, OCR fallback)
    ├── parsers.py        # layout-aware positional parser
    ├── llm_extract.py    # optional Anthropic-API engine
    ├── pipeline.py       # split packets -> detect -> extract -> route engines
    └── writer.py         # Excel workbook (Summary + detail tabs)
```

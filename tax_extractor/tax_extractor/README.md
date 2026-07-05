# tax_extractor

Pull structured data out of **W-2** and **1040** PDFs and write it to a
formatted **Excel** workbook — as a command-line tool *or* as an **MCP server**
you can drive from Claude Desktop.

```
PDF ──▶ text/words ──▶ form detection ──▶ field extraction ──▶ Excel
        (pdfplumber)    (W-2 vs 1040)      (positional | LLM)   (openpyxl)
```

## What you get

- **Local by default.** Native-PDF extraction with `pdfplumber` + a layout-aware
  positional parser. Nothing leaves your machine.
- **Correct on the canonical IRS layouts** (validated end-to-end against
  synthetic W-2 and 1040 forms — see `make_sample.py`).
- **Confidence + flags** on every field, so wrong/missing values are easy to
  spot. Amber = low confidence, red = not found. (For taxes, *verify the
  numbers* — this is an extraction aid, not a filing tool.)
- **Batch mode.** Point it at a folder of W-2s and get one workbook with a
  per-file Summary sheet.
- **Two extra engines when you want them:** OCR for scanned PDFs, and an LLM
  engine that's far more robust to odd or year-shifted layouts.

## Install

```bash
pip install -r requirements.txt        # core: pdfplumber, openpyxl
```

Optional extras (uncomment in `requirements.txt`):
- **OCR** for scanned PDFs: `pip install pytesseract pdf2image` + system
  packages `tesseract-ocr` and `poppler-utils`.
- **LLM engine**: `pip install anthropic` and set `ANTHROPIC_API_KEY`.
- **MCP server**: `pip install "mcp[cli]"`.

## CLI usage

```bash
# single file
python cli.py myW2.pdf -o out.xlsx

# a whole folder -> one workbook with a Summary sheet
python cli.py ./tax_pdfs/ -o 2024_summary.xlsx

# scanned PDF (forces OCR)
python cli.py scanned.pdf --ocr

# use the LLM engine (needs ANTHROPIC_API_KEY)
python cli.py form1040.pdf --engine llm

# skip auto-detection
python cli.py ambiguous.pdf --form W-2
```

Try it with no real data:

```bash
python make_sample.py            # writes sample_w2.pdf, sample_1040.pdf
python cli.py sample_w2.pdf -o demo.xlsx
```

## MCP server (Claude Desktop)

```bash
pip install "mcp[cli]"
python mcp_server.py
```

`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "tax-extractor": {
      "command": "python",
      "args": ["/absolute/path/to/tax_extractor/mcp_server.py"]
    }
  }
}
```

Tools exposed: `extract_tax_form`, `extract_to_excel`, `list_supported_forms`.

## Engines

| engine | where it runs | robustness | privacy |
|---|---|---|---|
| `positional` (default) | local | correct on standard layouts; sensitive to vendor variants | fully local |
| `llm` | Anthropic API | high — handles odd layouts & new tax years | sends text off-device |
| `auto` | local, then LLM if local coverage is poor *and* a key is set | best of both | local unless it falls back |

## Privacy

Tax forms contain SSNs, EINs, names, and addresses. The default `positional`
engine and OCR run entirely on your machine. The `llm` engine sends document
text to the Anthropic API — only use it if that's acceptable for your data.

## Architecture

```
tax_extractor/
├── tax_extractor/
│   ├── schemas.py        # field definitions; per-form layout (grid vs row)
│   ├── text_extract.py   # PDF -> text + positioned words (native, OCR fallback)
│   ├── parsers.py        # layout-aware positional parser
│   ├── llm_extract.py    # optional Anthropic-API engine
│   ├── writer.py         # Excel workbook (detail sheets + summary)
│   └── pipeline.py       # detect -> extract -> route engines
├── cli.py
├── mcp_server.py
├── make_sample.py        # synthetic test PDFs (fake data)
└── requirements.txt
```

## Known limitations

- The positional parser is tuned to the **standard IRS layouts**. Payroll
  vendors (ADP, Paychex, Gusto) and state e-file renders shuffle boxes around;
  on those, use `--engine llm` or extend `schemas.py` with new anchors.
- **1040 line numbers shift between tax years.** This is why fields anchor on
  *label text* ("adjusted gross income"), not line numbers — but unusual years
  may still need an anchor added.
- Multi-page returns: only fields on the form's main pages are read; schedules
  are out of scope.
- **Always verify the extracted numbers before relying on them.** This tool
  reads forms; it does not give tax advice.

## Extending

Add a field by appending a `Field(...)` to the relevant schema in `schemas.py`
with one or more lowercase `anchors` (label fragments that appear on the form).
Add a new form type by creating a `FormSchema` with `detect` phrases and the
right `layout` ("grid" or "row"), then registering it in `SCHEMAS`.

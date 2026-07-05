# Connect "Tax Form to Excel Sheet" to Claude

This makes the extractor available inside Claude Desktop so you can say
**"extract these W-2s to a spreadsheet"** and point at PDFs. Do this once per
computer. It takes about 5 minutes.

The MCP server is named **`tax-form-to-excel`**. (The internal Python package is
still called `tax_extractor` — that's not user-visible, so leave it alone.)

---

## What you need

- **Claude Desktop** installed.
- **Python 3.10+** on this machine. On this computer it lives at
  `C:\Python314\python.exe` — the steps below use that. If yours differs, swap in
  your path (see *Find your Python* in Troubleshooting).
- The project folder, containing `mcp_server.py` at:
  `C:\Users\leahs\OneDrive\Documents\PDF to Excel\tax_extractor\tax_extractor\mcp_server.py`

---

## Step 1 — Install the dependencies

Open **Command Prompt** and run:

```
C:\Python314\python.exe -m pip install pdfplumber openpyxl "mcp[cli]"
```

Then confirm they load:

```
C:\Python314\python.exe -c "import mcp, pdfplumber, openpyxl; print('deps OK')"
```

You should see `deps OK`.

## Step 2 — Open the Claude config file

In Claude Desktop: **Settings → Developer → Edit Config**. That opens the folder
containing `claude_desktop_config.json` — the only file Claude actually reads
(ignore any copies named `... (2).json`). Right-click
`claude_desktop_config.json` → **Open with → Notepad**.

## Step 3 — Add the tax-form-to-excel server

Inside the `mcpServers` section, add a `tax-form-to-excel` entry. **Use the full
path to python.exe** as the command (not just `"python"`).

If the file is **empty / brand new**, paste this whole thing:

```json
{
  "mcpServers": {
    "tax-form-to-excel": {
      "command": "C:\\Python314\\python.exe",
      "args": [
        "C:\\Users\\leahs\\OneDrive\\Documents\\PDF to Excel\\tax_extractor\\tax_extractor\\mcp_server.py"
      ]
    }
  }
}
```

If you **already have other servers** (e.g. QuickBooks), add it alongside them —
one `mcpServers` object, a comma between entries:

```json
{
  "mcpServers": {
    "quickbooks": {
      "command": "node",
      "args": ["...your existing quickbooks path..."]
    },
    "tax-form-to-excel": {
      "command": "C:\\Python314\\python.exe",
      "args": [
        "C:\\Users\\leahs\\OneDrive\\Documents\\PDF to Excel\\tax_extractor\\tax_extractor\\mcp_server.py"
      ]
    }
  }
}
```

> If you previously set this up under the old name **`tax-extractor`**, just
> rename that key to `tax-form-to-excel` (or replace the block with the above).

Notes that save headaches:
- Paths use **double backslashes** (`\\`) in JSON.
- It must be **one** `mcpServers` object — don't paste a second `{ ... }` block.
- Commas go between server entries, but not after the last one.

Save the file.

## Step 4 — Restart Claude

**Fully quit** Claude Desktop (not just close the window) and reopen it.

## Step 5 — Test it

In a new chat:

1. **"List the supported tax forms."** → returns W-2, 1040,
   1099-NEC/MISC/INT/DIV/R, Schedule C/E, and K-1.
2. **"Extract this W-2 to a spreadsheet:
   `C:\Users\leahs\OneDrive\Documents\PDF to Excel\tax_extractor\tax_extractor\sample_w2.pdf`"**

You can also point it at a **folder** of PDFs for one workbook with a Summary tab.

---

## The tools it exposes

| Tool | What it does |
|---|---|
| `list_supported_forms` | Lists the forms and fields it can extract |
| `extract_tax_form` | Parses a PDF / folder / glob, returns fields as JSON |
| `extract_to_excel` | Parses and writes a formatted `.xlsx` (detail tabs + Summary) |

In Claude these appear as `mcp__tax-form-to-excel__<tool>`.

## Optional — LLM engine (for K-1 / odd / scanned layouts)

The default engine is fully **local** (nothing leaves the machine) and handles
W-2, 1040, the 1099s, and Schedule C/E well. Messy K-1s and unrecognized forms
read more reliably with the LLM engine, which needs an Anthropic API key and
**sends document text (including SSNs) to the Anthropic API** — only enable if
that's acceptable for client data.

To enable: `C:\Python314\python.exe -m pip install anthropic`, then add an `env`
block to the server entry:

```json
    "tax-form-to-excel": {
      "command": "C:\\Python314\\python.exe",
      "args": ["...mcp_server.py..."],
      "env": { "ANTHROPIC_API_KEY": "sk-ant-...your key..." }
    }
```

The key sits in plaintext in this file, so treat it as sensitive.

---

## Troubleshooting

**"Server disconnected" / it shows failed.** The server started and crashed —
almost always missing dependencies, or Claude launched a *different* Python than
the one you installed into.
1. Run the server by hand to see the real error:
   ```
   C:\Python314\python.exe "C:\Users\leahs\OneDrive\Documents\PDF to Excel\tax_extractor\tax_extractor\mcp_server.py"
   ```
   If it just sits with a blinking cursor and no error, it's fine (press Ctrl+C).
   If it prints `ModuleNotFoundError`, re-run Step 1 with this exact Python.

**Find your Python** (if `C:\Python314\python.exe` isn't right):
```
where python
python -c "import sys; print(sys.executable)"
```
Use that full path as the `command`, and install the packages into that Python.

**"No module named tax_extractor".** The `args` path must point exactly at
`...\tax_extractor\tax_extractor\mcp_server.py` (note the doubled folder).

**Config changes don't take effect.** Make sure you edited the real
`claude_desktop_config.json` (via Settings → Developer → Edit Config), not a
copy, and that you **fully quit** and reopened Claude.

**Whole config rejected / QuickBooks also broke.** The JSON is invalid — usually
a missing/extra comma or two separate `{ }` blocks.

**Scanned PDFs come back empty.** Those need OCR: install `pytesseract` and
`pdf2image` plus the Tesseract and Poppler system tools, or use the LLM engine.

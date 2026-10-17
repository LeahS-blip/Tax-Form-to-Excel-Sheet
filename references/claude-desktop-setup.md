# Connect Tax Form to Excel to Claude

This makes the extractor available as an MCP server named
**`tax-form-to-excel`**, so you can say **"extract these W-2s to a
spreadsheet"** and point at PDFs. Do this once per computer (about 5 minutes).

Throughout this guide, `<SKILL_DIR>` means the folder that contains
`SKILL.md` (for example `C:\Users\you\.claude\skills\tax-form-to-excel`).

---

## What you need

- **Claude Desktop** or **Claude Code**.
- **Python 3.10+**. Find its full path with:
  ```
  python -c "import sys; print(sys.executable)"
  ```
  e.g. `C:\Python314\python.exe`. Use that exact path below.

## Step 1 — Install the dependencies

```
<python.exe> -m pip install -r "<SKILL_DIR>\requirements.txt"
<python.exe> -c "import mcp, pdfplumber, openpyxl; print('deps OK')"
```

On Windows you can instead double-click `windows\Install dependencies.bat`.

## Step 2a — Claude Code (one command)

```
claude mcp add tax-form-to-excel -- "<python.exe>" "<SKILL_DIR>\scripts\mcp_server.py"
```

## Step 2b — Claude Desktop

1. **Settings → Developer → Edit Config**. That opens the folder containing
   `claude_desktop_config.json`, the only file Claude reads (ignore copies
   like `... (2).json`). Open it in Notepad.
2. Add a `tax-form-to-excel` entry inside `mcpServers`. Use the **full path to
   python.exe**, and **double backslashes** in JSON:

   ```json
   {
     "mcpServers": {
       "tax-form-to-excel": {
         "command": "C:\\Python314\\python.exe",
         "args": [
           "C:\\Users\\you\\.claude\\skills\\tax-form-to-excel\\scripts\\mcp_server.py"
         ]
       }
     }
   }
   ```

   If you already have other servers (e.g. QuickBooks), add this entry
   alongside them: one `mcpServers` object, commas between entries, no comma
   after the last one.

   > Set this up before under the old name **`tax-extractor`**? Rename that key
   > to `tax-form-to-excel` and update the `args` path to `scripts\mcp_server.py`.

3. Save, then **fully quit** Claude Desktop (not just close the window) and
   reopen it.

## Step 3 — Test it

In a new chat:

1. **"List the supported tax forms."** → W-2, 1040, 1099-NEC/MISC/INT/DIV/R,
   Schedule C/E, and K-1.
2. **"Extract this W-2 to a spreadsheet: `<SKILL_DIR>\assets\sample_w2.pdf`"**

You can also point it at a **folder** of PDFs to get one workbook with a
Summary tab.

---

## The tools it exposes

| Tool | What it does |
|---|---|
| `list_supported_forms` | Lists the forms and fields it can extract |
| `extract_tax_form` | Parses a PDF / folder / glob, returns fields as JSON |
| `extract_to_excel` | Parses and writes a formatted `.xlsx` (detail tabs + Summary) |

In Claude these appear as `mcp__tax-form-to-excel__<tool>`.

## Optional — LLM engine (K-1s, odd layouts, unknown forms)

See [forms-and-engines.md](forms-and-engines.md) for what this changes. To
enable: `<python.exe> -m pip install anthropic`, then add an `env` block to the
server entry:

```json
    "tax-form-to-excel": {
      "command": "C:\\Python314\\python.exe",
      "args": ["...\\scripts\\mcp_server.py"],
      "env": { "ANTHROPIC_API_KEY": "sk-ant-...your key..." }
    }
```

The key sits in plaintext in this file, so treat the file as sensitive. The
LLM engine **sends document text (including SSNs) to the Anthropic API**. Only
enable it if that's acceptable for your client data.

---

## Troubleshooting

**"Server disconnected" / shows failed.** The server started and crashed:
usually missing dependencies, or Claude launched a *different* Python than the
one you installed into. Run it by hand to see the real error:

```
<python.exe> "<SKILL_DIR>\scripts\mcp_server.py"
```

A blinking cursor with no error means it's fine (press Ctrl+C). A
`ModuleNotFoundError` means you should re-run Step 1 with this exact Python.

**"No module named tax_extractor".** The `args` path must point at
`...\scripts\mcp_server.py`, which sits next to the `tax_extractor` package.

**Config changes don't take effect.** Make sure you edited the real
`claude_desktop_config.json` (via Settings → Developer → Edit Config) and
**fully quit** and reopened Claude.

**Whole config rejected / other servers also broke.** The JSON is invalid,
usually a missing or extra comma, or two separate `{ }` blocks.

**Scanned PDFs come back empty.** Those need OCR: install `pytesseract` and
`pdf2image` plus the Tesseract and Poppler system tools, or use the LLM engine.

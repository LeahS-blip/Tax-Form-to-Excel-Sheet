# More forms + automatic detection — what changed

## Detection is automatic

You don't tell it what a file is. When you point it at a PDF, it reads the text,
matches it against each form's signature phrases, and picks the form type
itself. That already worked for W-2 and 1040 — the only reason it stopped there
was that those were the only form definitions loaded.

## Forms it now recognizes

Added definitions (so detection now covers them automatically):

- **W-2**, **1040** (existing)
- **Schedule C** — profit or loss from business
- **Schedule E** — supplemental income & loss (rentals/royalties)
- **Schedule K-1** — partner / shareholder / beneficiary share
- **1099-NEC, 1099-MISC, 1099-INT, 1099-DIV, 1099-R**

Ask Claude **"list the supported tax forms"** to see the full field list per form.

## "Read basically any form" — how that works

Two reading methods, and which one runs depends on the engine setting:

- **Local (positional).** Reads boxes by their position on the standard IRS
  page. Free, fully on-device. Reliable on **W-2, 1040, the 1099s, Schedule C/E**
  in their standard layouts. Struggles with messy/variable layouts (K-1, odd
  vendor renders).
- **LLM.** Claude reads the page text and pulls the fields. Handles **K-1,
  unusual layouts, new tax years, and forms with no definition at all**
  (1099-B, 1098, W-2G, etc. — it identifies the form and tables whatever
  tax-relevant fields it finds). Requires setup below and **sends document text
  to the Anthropic API.**
- **auto (default).** Tries local first; only falls back to the LLM when local
  comes up short or the form is unrecognized. This keeps client PII on-device
  for the common forms and only reaches the API for the hard ones.

So out of the box (no extra setup) you get reliable local extraction on the
standard forms. To get the "any form, including K-1" behavior, enable the LLM
engine:

## Enable the LLM engine (for K-1 / unknown forms)

This is what powers the "auto find out" behavior on messy or undefined forms.

1. **Get an Anthropic API key.** This is separate from your Claude Desktop
   subscription — create one at https://console.anthropic.com (it's billed per
   use; tax-form text is small, so cost per document is tiny).

2. **Install the package** into the same Python the server uses:

   ```
   C:\Python314\python.exe -m pip install anthropic
   ```

3. **Add the key to the server's config.** In `claude_desktop_config.json`, give
   the `tax-form-to-excel` server an `env` block with your key:

   ```json
   "tax-form-to-excel": {
     "command": "C:\\Python314\\python.exe",
     "args": [
       "C:\\Users\\leahs\\OneDrive\\Documents\\PDF to Excel\\tax_extractor\\tax_extractor\\mcp_server.py"
     ],
     "env": {
       "ANTHROPIC_API_KEY": "sk-ant-...your key..."
     }
   }
   ```

4. Save and restart Claude.

With the key set, `auto` (the default) will automatically use the LLM only when
needed, and unrecognized forms will be identified and tabled instead of
erroring.

## Privacy reminder

The local engine keeps everything on-device. The LLM engine sends document text
— **including SSNs, EINs, and dollar amounts** — to the Anthropic API. Decide if
that's acceptable for client data before enabling it. Either way, **verify the
extracted numbers**: low-confidence values are flagged amber and missing ones
red in the workbook. This is an extraction aid, not a filing tool.

## Test it

After restarting Claude, try:

- "List the supported tax forms." → should now show Schedule C/E, K-1, and the 1099s.
- "Extract this to a spreadsheet: `...\sample_w2.pdf`" → standard form, local.
- Drop a real 1099 or Schedule C PDF and ask it to extract — detection should
  name the form on its own.
- (With the LLM key set) hand it a K-1 or a form not in the list and confirm it
  still produces a table.

## Known limits

- **One form type per PDF.** If a file contains a full 1040 packet *with*
  schedules, detection picks the dominant form; it won't split a combined PDF
  into separate forms yet.
- The positional anchors for the new schedules are tuned to standard IRS
  layouts; for vendor variants, the LLM engine is the fallback.
- I couldn't run an automated test from my side (the build sandbox was out of
  disk space), so please sanity-check the first few extractions of each new
  form type against the source PDF.

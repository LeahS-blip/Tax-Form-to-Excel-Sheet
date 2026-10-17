"""
Maintainer helper: dump the structure of an Excel template (sheets, merged
cells, column widths, values/formulas, bold cells) so its layout can be
mirrored in the extractor's Excel writer.

Run it:
    python dump_template.py "path\\to\\template.xlsx"

It writes <template>_structure.txt next to the workbook. Nothing is uploaded.
"""
import os
import sys

from openpyxl import load_workbook


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        raise SystemExit("usage: python dump_template.py <template.xlsx>")
    src = os.path.abspath(argv[0])
    if not os.path.exists(src):
        raise SystemExit(f"Could not find the template at:\n  {src}")
    out = os.path.splitext(src)[0] + "_structure.txt"

    wb = load_workbook(src, data_only=True)      # values
    wbf = load_workbook(src, data_only=False)    # formulas + styling

    lines = [f"FILE: {os.path.basename(src)}", f"SHEETS: {wb.sheetnames}"]

    for ws, wsf in zip(wb.worksheets, wbf.worksheets):
        lines.append("")
        lines.append(f"===== SHEET: {ws.title!r}  dims={ws.dimensions}  "
                     f"max_row={ws.max_row} max_col={ws.max_column} =====")
        merged = [str(m) for m in ws.merged_cells.ranges]
        if merged:
            lines.append(f"  merged cells: {merged}")
        widths = {k: round(v.width, 1) for k, v in ws.column_dimensions.items()
                  if v.width}
        if widths:
            lines.append(f"  col widths: {widths}")
        lines.append("  --- rows (value | [formula if any]) ---")
        for row in wsf.iter_rows():
            cells = []
            for c in row:
                if c.value is None:
                    continue
                bold = " <b>" if c.font is not None and c.font.bold else ""
                cells.append(f"{c.coordinate}={str(c.value)[:60]}{bold}")
            if cells:
                lines.append("   " + " | ".join(cells))

    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote structure to:\n  {out}")
    print(f"Sheets: {wb.sheetnames}")


if __name__ == "__main__":
    main()

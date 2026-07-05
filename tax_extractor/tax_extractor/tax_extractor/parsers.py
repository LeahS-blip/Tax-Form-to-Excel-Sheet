"""
Positional field parser — layout-aware.

These two forms are laid out differently, and that difference is the whole
ballgame for positional parsing:

  * W-2  is a GRID: each value sits directly BELOW its box label, left-aligned
    to the box. A naive "nearest token" grabs the neighbouring box's number.
  * 1040 is ROWS: each value sits to the RIGHT of its label, right-aligned at
    the far edge of the line. A naive "nearest token" grabs the next row down.

So we select values per the schema's declared layout instead of one universal
distance rule. Money tokens are scored by *richness* (a comma/decimal/$ marks a
real amount, distinguishing "84,500.00" from a bare box number like "2").

This is correct on the canonical IRS layouts. Real-world vendor variants (ADP,
Paychek, state e-file renders) differ enough that the LLM engine is the right
tool there; everything here is flagged with a confidence so a human can verify.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any

from .schemas import Field, FormSchema
from .text_extract import Word

_MONEY_RE = re.compile(r"-?\$?\(?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\)?")
_RICH_RE = re.compile(r"[,\.\$]")
_SSN_RE = re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b")
_EIN_RE = re.compile(r"\b\d{2}-?\d{7}\b")
_BOX12_CODES = {
    "A","B","C","D","E","F","G","H","J","K","L","M","N","P","Q","R","S","T",
    "V","W","Y","Z","AA","BB","DD","EE","FF","GG","HH",
}
_LABEL_WORDS = {"code","name","number","address","zip","first","last","initial",
                "state","id","tips","wages","tax","income","etc."}
_BOX_W = 150.0  # approx width of one W-2 box, for vertical-column matching


@dataclass
class FieldResult:
    key: str
    label: str
    value: Any
    raw: str
    confidence: float


def _clean_money(s: str):
    m = _MONEY_RE.search(s.replace(" ", ""))
    if not m:
        return None
    t = m.group(0)
    neg = t.startswith("(") and t.endswith(")")
    t = t.replace("$", "").replace(",", "").replace("(", "").replace(")", "")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def _clean(kind, s):
    s = (s or "").strip()
    if kind == "money":
        return _clean_money(s)
    if kind == "ssn":
        m = _SSN_RE.search(s); return m.group(0) if m else None
    if kind == "ein":
        m = _EIN_RE.search(s); return m.group(0) if m else None
    return s or None


def _is_money(t):
    return bool(_MONEY_RE.fullmatch(t.replace(" ", ""))) and any(c.isdigit() for c in t)


def _is_rich(t):
    return _is_money(t) and bool(_RICH_RE.search(t))


def _accepts(kind, t):
    if kind == "money":
        return _is_money(t)
    if kind == "ssn":
        return bool(_SSN_RE.search(t))
    if kind == "ein":
        return bool(_EIN_RE.search(t))
    if kind == "text":
        return len(t.strip()) >= 2 and t.strip().lower() not in _LABEL_WORDS
    return True


def _find_anchor_spans(words, anchor):
    """Yield (first_word, last_word, member_index_set) for each line-run whose
    joined lowercased text contains the anchor phrase. The span is trimmed to
    the *minimal* prefix that contains the phrase, so trailing value tokens on
    the same line are NOT counted as part of the label."""
    n = len(anchor.split())
    for i in range(len(words)):
        window = [i]
        for j in range(i + 1, min(i + n + 8, len(words))):
            if words[j].page != words[i].page or abs(words[j].top - words[i].top) > 6:
                break
            window.append(j)
        # grow the prefix until it contains the anchor, then stop
        for k in range(len(window)):
            members = window[:k + 1]
            if anchor in " ".join(words[m].text for m in members).lower():
                yield words[members[0]], words[members[-1]], set(members)
                break


def _grid_value(words, first, last, fld, exclude):
    """W-2: value in the band directly below, column-aligned to the box's left."""
    col = first.x0
    below = []
    for idx, w in enumerate(words):
        if idx in exclude or w.page != first.page:
            continue
        if not _accepts(fld.kind, w.text):
            continue
        dy = w.top - last.bottom
        if 0 < dy <= fld.max_dy and abs(w.cx - col) <= _BOX_W:
            below.append((abs(w.cx - col), dy, w))
    if not below:
        return None, 0.0
    # prefer rich money, then nearest column, then nearest row
    def rank(c):
        rich = 0 if _is_rich(c[2].text) else 1
        return (rich, c[0], c[1])
    below.sort(key=rank)
    w = below[0][2]
    conf = 0.92 if (fld.kind != "money" or _is_rich(w.text)) else 0.55
    return w.text, conf


def _row_value(words, first, last, fld, exclude):
    """1040: value to the right on the same line; take the rightmost rich money."""
    same = []
    for idx, w in enumerate(words):
        if idx in exclude or w.page != first.page:
            continue
        if abs(w.top - last.top) > 8:
            continue
        if w.x0 < last.x1 - 2:
            continue
        if not _accepts(fld.kind, w.text):
            continue
        same.append(w)
    if not same:
        return None, 0.0
    if fld.kind == "money":
        rich = [w for w in same if _is_rich(w.text)]
        pool = rich or [w for w in same if _is_money(w.text)]
        if not pool:
            return None, 0.0
        # Take the amount NEAREST to the right of the label. On single-column
        # forms (1040, Schedule C/E) there is only one amount on the line, so
        # this is the same value the old "rightmost" rule picked. On the
        # two-column K-1 Part III it correctly grabs the box's OWN amount
        # instead of the neighbouring column's (e.g. box 1 vs box 14).
        w = min(pool, key=lambda w: w.x0)  # leftmost / nearest to label
        return w.text, (0.92 if _is_rich(w.text) else 0.55)
    w = min(same, key=lambda w: w.x0)
    return w.text, 0.85


def _name_below(words, first, last, fld, exclude):
    """Multi-word text (employer/employee name) on the line directly below the
    label, restricted to a narrow column so it doesn't bleed into the next box."""
    cands = [w for i, w in enumerate(words)
             if i not in exclude and w.page == first.page
             and 0 < (w.top - last.bottom) <= 22
             and -10 <= (w.x0 - first.x0) <= _BOX_W
             and not _is_money(w.text)
             and w.text.strip().lower() not in _LABEL_WORDS]
    if not cands:
        return None
    # keep only the single nearest line below
    top0 = min(w.top for w in cands)
    line = sorted((w for w in cands if abs(w.top - top0) <= 4),
                  key=lambda w: w.x0)
    toks = [w.text for w in line[:5]]
    return (" ".join(toks).strip() or None)


def _box12(words):
    for first, last, _m in _find_anchor_spans(words, "12a"):
        region = [w for w in words if w.page == last.page
                  and last.top - 4 <= w.top <= last.bottom + 22
                  and w.x0 >= first.x0 - 4]
        region.sort(key=lambda w: (round(w.top), w.x0))
        seq = " ".join(w.text for w in region)
        pairs = []
        for m in re.finditer(r"\b([A-Z]{1,2})\b[ ]+\$?(\d[\d,]*\.?\d*)", seq):
            if m.group(1) in _BOX12_CODES:
                pairs.append(f"{m.group(1)}={m.group(2).replace(',', '')}")
        if pairs:
            return "; ".join(pairs), 0.85
    return None, 0.0


def parse_positional(words, schema: FormSchema):
    out = {}
    for fld in schema.fields:
        if fld.kind == "code_amount":
            raw, conf = _box12(words)
            out[fld.key] = FieldResult(fld.key, fld.label, raw, raw or "", conf)
            continue

        # A field may override the form's layout (K-1 mixes grid + row).
        fld_layout = fld.layout or schema.layout
        finder = _grid_value if fld_layout == "grid" else _row_value

        is_name = fld.name_block or fld.key in ("employer_name", "employee_name")
        best_raw, best_conf = None, 0.0
        for anchor in fld.anchors:
            for first, last, members in _find_anchor_spans(words, anchor):
                if is_name:
                    raw = _name_below(words, first, last, fld, members)
                    conf = 0.85 if raw else 0.0
                else:
                    raw, conf = finder(words, first, last, fld, members)
                if raw and conf > best_conf:
                    best_raw, best_conf = raw, conf
        out[fld.key] = FieldResult(
            fld.key, fld.label, _clean(fld.kind, best_raw or ""),
            best_raw or "", round(best_conf, 2),
        )
    return out

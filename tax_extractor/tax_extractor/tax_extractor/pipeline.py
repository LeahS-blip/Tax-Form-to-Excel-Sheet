"""
Orchestration: one PDF (or a folder of them) -> FileResult objects ready for
the Excel writer.

A single client PDF is often a *packet*: a 1040 plus several schedules and one
or more K-1s. So we split each PDF into form segments (by detecting form
headers page by page) and extract each segment separately. A plain one-form PDF
simply yields one segment, so behaviour there is unchanged.

engine="auto": positional parser; if it's clearly weak (many missing fields)
and the LLM path is available, retry that segment with the LLM.
engine="positional": local only.
engine="llm": Anthropic API only.
"""

from __future__ import annotations
import os
import glob

from . import text_extract, llm_extract
from .schemas import SCHEMAS, detect_form_type, FormSchema
from .parsers import parse_positional, FieldResult
from .writer import FileResult


def _coverage(fields: dict[str, FieldResult]) -> float:
    if not fields:
        return 0.0
    have = sum(1 for f in fields.values() if f.value not in (None, ""))
    return have / len(fields)


def _extract_core(text: str, words, ft: str | None, engine: str):
    """Extract one form's fields. Returns (form_type, fields, used_engine).

    ft is the known/detected form type, or None for an unrecognized form (which
    routes to the generic LLM identifier when that engine is available)."""
    if ft is None or ft not in SCHEMAS:
        if engine != "positional" and llm_extract.available():
            gen_type, gen_fields = llm_extract.identify_and_extract(text)
            return (ft or gen_type), gen_fields, "llm"
        raise ValueError(
            f"Could not match this form to a known type "
            f"({', '.join(SCHEMAS)}). Set ANTHROPIC_API_KEY and use "
            f"engine='auto' to read unrecognized forms, or pass form_type."
        )

    schema: FormSchema = SCHEMAS[ft]
    if engine in ("positional", "auto"):
        fields = parse_positional(words, schema)
        if engine == "auto" and _coverage(fields) < 0.5 and llm_extract.available():
            return ft, llm_extract.parse_llm(text, schema), "llm"
        return ft, fields, "positional"
    if engine == "llm":
        if not llm_extract.available():
            raise RuntimeError(
                "engine='llm' requires ANTHROPIC_API_KEY and the 'anthropic' "
                "package (pip install anthropic)."
            )
        return ft, llm_extract.parse_llm(text, schema), "llm"
    raise ValueError(f"unknown engine: {engine}")


def _segment(page_texts: list[str]) -> list[tuple[str | None, list[int]]]:
    """Group pages into form segments. A new segment starts when a page's
    detected form type differs from the current one; pages where nothing is
    detected (continuation/instruction pages) attach to the current segment.

    Limitation: several forms of the SAME type back to back (e.g. three K-1s in
    a row) currently merge into one segment — flagged for the user to verify."""
    segs: list[tuple[str | None, list[int]]] = []
    cur_type: str | None = None
    cur_pages: list[int] = []
    for i, pt in enumerate(page_texts or []):
        t = detect_form_type(pt or "")
        if t is not None and cur_pages and t != cur_type:
            segs.append((cur_type, cur_pages))
            cur_type, cur_pages = t, [i]
        else:
            cur_pages.append(i)
            if cur_type is None and t is not None:
                cur_type = t
    if cur_pages:
        segs.append((cur_type, cur_pages))
    return segs


def process_file(path: str, engine: str = "auto",
                 force_ocr: bool = False,
                 form_type: str | None = None) -> FileResult:
    """Extract a single PDF as ONE form (back-compatible). For packets that may
    contain several forms, use process_forms / process_path."""
    doc = text_extract.extract(path, force_ocr=force_ocr)
    ft = form_type or detect_form_type(doc.text)
    rtype, fields, used = _extract_core(doc.text, doc.words, ft, engine)
    return FileResult(os.path.basename(path), rtype, doc.source, used, fields)


def process_forms(path: str, engine: str = "auto",
                  force_ocr: bool = False,
                  form_type: str | None = None) -> list[FileResult]:
    """Extract every form found in one PDF. A simple one-form PDF returns a
    single FileResult; a packet returns one per detected form."""
    doc = text_extract.extract(path, force_ocr=force_ocr)
    base = os.path.basename(path)

    # Caller forced a type, or we have no per-page text: treat as one form.
    if form_type is not None or not doc.page_texts:
        ft = form_type or detect_form_type(doc.text)
        rtype, fields, used = _extract_core(doc.text, doc.words, ft, engine)
        return [FileResult(base, rtype, doc.source, used, fields)]

    segs = _segment(doc.page_texts)
    detected = [s for s in segs if s[0] is not None]
    multi = len(detected) > 1

    results: list[FileResult] = []
    for ft, pages in segs:
        if ft is None and multi:
            continue  # skip stray undetected pages in a packet
        pageset = set(pages)
        seg_words = [w for w in doc.words if w.page in pageset]
        seg_text = "\n".join(doc.page_texts[p] for p in pages)
        try:
            rtype, fields, used = _extract_core(seg_text, seg_words, ft, engine)
        except ValueError:
            continue
        name = f"{base} [{rtype}]" if multi else base
        results.append(FileResult(name, rtype, doc.source, used, fields))

    if not results:
        # Nothing split cleanly — fall back to whole-document extraction so the
        # original error/behaviour surfaces.
        ft = detect_form_type(doc.text)
        rtype, fields, used = _extract_core(doc.text, doc.words, ft, engine)
        results = [FileResult(base, rtype, doc.source, used, fields)]
    return results


def process_path(path: str, **kw) -> list[FileResult]:
    """Accept a single PDF or a directory/glob of PDFs. Each PDF may yield more
    than one form (combined packets are split)."""
    if os.path.isdir(path):
        pdfs = sorted(glob.glob(os.path.join(path, "*.pdf")))
    elif any(ch in path for ch in "*?["):
        pdfs = sorted(glob.glob(path))
    else:
        pdfs = [path]
    if not pdfs:
        raise FileNotFoundError(f"No PDF files found at {path}")
    results: list[FileResult] = []
    for p in pdfs:
        results.extend(process_forms(p, **kw))
    return results

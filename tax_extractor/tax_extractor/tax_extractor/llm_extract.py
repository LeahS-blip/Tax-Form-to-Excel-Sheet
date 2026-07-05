"""
Optional LLM extraction path (Anthropic API).

Why have this at all? The positional parser is fast, free, and fully local,
but it's sensitive to layout. An LLM reading the page text against a schema is
dramatically more robust to year-to-year form changes and odd layouts.

PRIVACY: this sends document text to the Anthropic API. Tax forms contain SSNs,
EINs, names, and addresses. Only use this path if you're comfortable with that.
The positional parser keeps everything on-device.

Enable by setting ANTHROPIC_API_KEY and passing --engine llm (or both).
"""

from __future__ import annotations
import json
import os
from typing import Any

from .schemas import FormSchema
from .parsers import FieldResult, _clean


def available() -> bool:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
        return True
    except ImportError:
        return False


def _schema_prompt(schema: FormSchema) -> str:
    lines = [f'- "{f.key}": {f.label} (type: {f.kind})' for f in schema.fields]
    return "\n".join(lines)


def parse_llm(text: str, schema: FormSchema,
              model: str = "claude-sonnet-4-6") -> dict[str, FieldResult]:
    import anthropic

    client = anthropic.Anthropic()
    field_spec = _schema_prompt(schema)
    system = (
        "You extract structured data from US tax forms. You are given the raw "
        "text of a {ft} form. Return ONLY a JSON object, no prose, no markdown "
        "fences. For each key below, give the value found on the form. Use null "
        "if the field is blank or absent. Money values must be plain numbers "
        "(no $ or commas); parenthesized amounts are negative. Do not guess or "
        "compute values that aren't present.\n\nFields:\n{fields}"
    ).format(ft=schema.form_type, fields=field_spec)

    msg = client.messages.create(
        model=model,
        max_tokens=1500,
        system=system,
        messages=[{"role": "user", "content": text[:60000]}],
    )
    raw = "".join(b.text for b in msg.content if b.type == "text").strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        # last-ditch: grab the outermost {...}
        i, j = raw.find("{"), raw.rfind("}")
        data = json.loads(raw[i:j + 1]) if i >= 0 and j > i else {}

    out: dict[str, FieldResult] = {}
    for fld in schema.fields:
        v = data.get(fld.key)
        if isinstance(v, str):
            v = _clean(fld.kind, v)
        out[fld.key] = FieldResult(fld.key, fld.label, v,
                                   "" if v is None else str(v),
                                   0.9 if v is not None else 0.0)
    return out


def identify_and_extract(text: str,
                         model: str = "claude-sonnet-4-6"
                         ) -> tuple[str, dict[str, FieldResult]]:
    """Generic path for forms we have no schema for.

    Asks the model to (1) name the tax form and (2) return the
    tax-relevant fields it finds, as a flat {label: value} object. Used as a
    last resort so an unrecognized form still produces a usable table instead
    of an error. Requires ANTHROPIC_API_KEY + the 'anthropic' package.
    """
    import anthropic

    client = anthropic.Anthropic()
    system = (
        "You read US tax documents. Identify the form, then extract every "
        "tax-relevant field a preparer would need (parties, IDs, and all "
        "dollar amounts with their labels). Return ONLY a JSON object of the "
        "shape:\n"
        '{"form_type": "<e.g. 1099-B, 1098, W-2G, 5498>", '
        '"fields": {"<human label>": <value>, ...}}\n'
        "Money values must be plain numbers (no $ or commas); parenthesized "
        "amounts are negative. Use null for blank fields. Do not invent or "
        "compute values that are not on the document. No prose, no markdown."
    )
    msg = client.messages.create(
        model=model, max_tokens=2000, system=system,
        messages=[{"role": "user", "content": text[:60000]}],
    )
    raw = "".join(b.text for b in msg.content if b.type == "text").strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        i, j = raw.find("{"), raw.rfind("}")
        data = json.loads(raw[i:j + 1]) if i >= 0 and j > i else {}

    form_type = str(data.get("form_type") or "Unknown form").strip()
    raw_fields = data.get("fields") or {}
    out: dict[str, FieldResult] = {}
    for i, (label, value) in enumerate(raw_fields.items()):
        key = f"f{i}"
        money = isinstance(value, (int, float))
        out[key] = FieldResult(key, str(label), value,
                               "" if value is None else str(value),
                               0.85 if value not in (None, "") else 0.0)
    return form_type, out

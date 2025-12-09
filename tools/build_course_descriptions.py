#!/usr/bin/env python
"""
build_course_descriptions.py

Reads courses.json and generates docs/data/course-descriptions.json
with description-only data (no dates, no session_ids).

Usage (from repo root):
    python tools/build_course_descriptions.py
"""

import json
import re
from pathlib import Path

# Configuration
REPO_ROOT = Path(__file__).resolve().parents[1]  # ew2landers root
COURSES_JSON = REPO_ROOT / "courses.json"
OUTPUT_JSON = REPO_ROOT / "docs" / "data" / "course-descriptions.json"
MAX_SHORT_LEN = 260  # characters for shortDescription preview


def strip_html(html: str) -> str:
    """Simple HTML to plain text stripper."""
    if not html:
        return ""
    # remove script/style blocks
    html = re.sub(
        r"<(script|style)[^>]*>.*?</\\1>",
        "",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    # replace <br> and common block endings with spaces
    html = re.sub(r"<br\\s*/?>", " ", html, flags=re.IGNORECASE)
    html = re.sub(
        r"</(p|li|div|h[1-6])>",
        " ",
        html,
        flags=re.IGNORECASE,
    )
    # strip remaining tags
    html = re.sub(r"<[^>]+>", "", html)
    # collapse whitespace
    html = re.sub(r"\\s+", " ", html).strip()
    return html


def build_record(raw: dict) -> dict:
    """Create a clean description record from a raw courses.json entry."""
    course_id = raw.get("course_id")
    ugly_title = raw.get("uglyTitle") or ""
    clean_title = raw.get("cleanTitle") or ""
    family = raw.get("family") or ""
    cert_body = raw.get("certBody") or ""
    delivery_mode = raw.get("deliveryMode") or ""
    html = raw.get("uglyHTML") or ""

    # Prefer cleanTitle, fall back to uglyTitle
    full_title = clean_title or ugly_title

    # Split into title and detail on the first " — " like in your naming
    title = full_title
    detail = ""
    if " — " in full_title:
        parts = full_title.split(" — ", 1)
        title = parts[0].strip()
        detail = parts[1].strip()

    # Build shortDescription by stripping HTML and trimming
    text_body = strip_html(html)
    short_desc = text_body
    if len(short_desc) > MAX_SHORT_LEN:
        cut = short_desc[:MAX_SHORT_LEN]
        # trim at last space so we do not cut mid-word
        if " " in cut:
            cut = cut.rsplit(" ", 1)[0]
        short_desc = cut + "..."

    return {
        "course_id": course_id,
        "family": family,
        "certBody": cert_body,
        "deliveryMode": delivery_mode,
        "title": full_title,
        "detail": detail,
        "shortDescription": short_desc,
        "htmlDescription": html,
    }


def main() -> None:
    if not COURSES_JSON.exists():
        raise SystemExit(f"courses.json not found at: {COURSES_JSON}")

    with COURSES_JSON.open("r", encoding="utf-8") as f:
        source = json.load(f)

    raw_courses = source.get("courses", [])
    records = [build_record(c) for c in raw_courses]

    # Make sure docs/data exists
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "meta": {
            "generated_from": COURSES_JSON.name,
            "note": "Description-only export. Dates and session_ids intentionally excluded.",
            "course_count": len(records),
        },
        "courses": records,
    }

    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(records)} course records to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()

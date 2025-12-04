#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
build_schedule_page.py

Reads docs/data/schedule.json and templates/schedule_page_template.html
and writes docs/schedule.html with SEO-friendly, static course+session list.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, DefaultDict
from collections import defaultdict


ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "docs" / "data" / "schedule.json"
TEMPLATE_PATH = ROOT / "templates" / "schedule_page_template.html"
OUTPUT_PATH = ROOT / "docs" / "schedule.html"


def load_schedule() -> Dict[str, Any]:
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_iso(dt: str) -> datetime:
    # schedule.json should be ISO 8601 with offset, e.g. "2025-11-22T12:30:00-05:00"
    # Python 3.11: fromisoformat handles offsets.
    return datetime.fromisoformat(dt)


def slugify(text: str) -> str:
    import re

    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "class"


def build_course_blocks(schedule: Dict[str, Any]) -> str:
    courses = {c["id"]: c for c in schedule.get("courses", [])}
    sessions: List[Dict[str, Any]] = schedule.get("sessions", [])

    sessions_by_course: DefaultDict[int, List[Dict[str, Any]]] = defaultdict(list)
    for s in sessions:
        cid = s.get("course_id")
        if cid is not None:
            sessions_by_course[cid].append(s)

    # sort sessions by start date
    for cid in sessions_by_course:
        sessions_by_course[cid].sort(
            key=lambda s: parse_iso(s.get("start_iso") or s.get("start") or "2100-01-01T00:00:00")
        )

    blocks: List[str] = []

    for course_id, course in sorted(courses.items(), key=lambda kv: kv[1]["name"]):
        name = course["name"]
        sessions_for_course = sessions_by_course.get(course_id, [])
        if not sessions_for_course:
            # Skip completely empty courses to avoid clutter
            continue

        lines: List[str] = []
        lines.append('<section class="course-block">')
        lines.append(f"  <h2>{name}</h2>")
        lines.append("  <ul>")

        for sess in sessions_for_course:
            start_iso = sess.get("start_iso") or sess.get("start")
            dt = parse_iso(start_iso) if start_iso else None
            dt_display = sess.get("start_display")
            if not dt_display and dt:
                dt_display = dt.strftime("%A, %B %-d, %Y at %-I:%M %p")

            city = sess.get("city") or ""
            state = sess.get("state") or ""
            location = sess.get("location_name") or sess.get("location") or ""
            price = sess.get("price_display") or sess.get("price") or ""
            enroll_url = sess.get("enroll_url") or "#"

            # Link to the session lander; we’ll use a predictable pattern
            session_id = sess.get("session_id") or sess.get("id")
            slug = slugify(name)
            lander_href = f"/classes/{session_id}-{slug}.html"

            pieces = []
            pieces.append(f"<strong>{dt_display}</strong>")
            if city or state:
                pieces.append(f" – {city}, {state}".strip(" ,"))
            if price:
                pieces.append(f" – ${price}" if isinstance(price, (int, float)) else f" – {price}")

            lines.append("    <li>")
            lines.append(f"      {' '.join(pieces)}<br/>")
            lines.append(f'      <a href="{lander_href}">Details &amp; Register</a>')
            lines.append(f'      &nbsp;|&nbsp; <a href="{enroll_url}">Direct Enroll</a>')
            lines.append("    </li>")

        lines.append("  </ul>")
        lines.append("</section>")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def main() -> None:
    print("[build_schedule_page] Loading schedule.json from", DATA_PATH)
    schedule = load_schedule()

    print("[build_schedule_page] Building course blocks")
    course_blocks_html = build_course_blocks(schedule)

    print("[build_schedule_page] Loading template", TEMPLATE_PATH)
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    html = template.replace("<!--COURSE_BLOCKS-->", course_blocks_html)

    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print("[build_schedule_page] Wrote", OUTPUT_PATH)


if __name__ == "__main__":
    main()

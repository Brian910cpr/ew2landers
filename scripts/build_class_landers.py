#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
build_class_landers.py

Reads docs/data/schedule.json and templates/session_lander_template.html
and writes one HTML page per session under docs/classes/.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, DefaultDict
from collections import defaultdict


ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "docs" / "data" / "schedule.json"
TEMPLATE_PATH = ROOT / "templates" / "session_lander_template.html"
OUTPUT_DIR = ROOT / "docs" / "classes"


def load_schedule() -> Dict[str, Any]:
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_iso(dt: str) -> datetime:
    return datetime.fromisoformat(dt)


def slugify(text: str) -> str:
    import re

    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "class"


def build_other_dates_list(
    course_id: int,
    current_session_id: Any,
    sessions_by_course: DefaultDict[int, List[Dict[str, Any]]],
    course_name: str,
) -> str:
    items: List[str] = []
    for sess in sessions_by_course.get(course_id, []):
        sid = sess.get("session_id") or sess.get("id")
        if sid == current_session_id:
            continue

        start_iso = sess.get("start_iso") or sess.get("start")
        dt = parse_iso(start_iso) if start_iso else None
        dt_display = sess.get("start_display")
        if not dt_display and dt:
            dt_display = dt.strftime("%A, %B %-d, %Y at %-I:%M %p")

        city = sess.get("city") or ""
        state = sess.get("state") or ""
        name_slug = slugify(course_name)
        lander_href = f"/classes/{sid}-{name_slug}.html"

        label_parts = [dt_display]
        if city or state:
            label_parts.append(f"{city}, {state}".strip(" ,"))

        items.append(f'<li><a href="{lander_href}"> { " – ".join(p in label_parts if p for p in label_parts) } </a></li>')

    if not items:
        return "<li>No other scheduled times for this class are currently listed.</li>"

    return "\n      ".join(items)


def build_other_courses_list(this_course_id: int, courses: List[Dict[str, Any]]) -> str:
    # Pick some other “headline” courses for cross-link SEO
    # For now, just list 5 others by name.
    items: List[str] = []
    for c in courses:
        cid = c["id"]
        if cid == this_course_id:
            continue
        name = c["name"]
        slug = slugify(name)
        # Point them back to schedule.html anchor (simpler than per-course landers)
        href = f"/schedule.html#{slug}"
        items.append(f'<li><a href="{href}">{name}</a></li>')
        if len(items) >= 5:
            break

    if not items:
        return "<li>View our full <a href=\"/schedule.html\">class schedule</a>.</li>"

    return "\n      ".join(items)


def main() -> None:
    print("[build_class_landers] Loading schedule.json from", DATA_PATH)
    schedule = load_schedule()
    courses = schedule.get("courses", [])
    sessions: List[Dict[str, Any]] = schedule.get("sessions", [])

    courses_by_id = {c["id"]: c for c in courses}
    sessions_by_course: DefaultDict[int, List[Dict[str, Any]]] = defaultdict(list)

    for s in sessions:
        cid = s.get("course_id")
        if cid is not None:
            sessions_by_course[cid].append(s)

    for cid in sessions_by_course:
        sessions_by_course[cid].sort(
            key=lambda s: parse_iso(s.get("start_iso") or s.get("start") or "2100-01-01T00:00:00")
        )

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for sess in sessions:
        course_id = sess.get("course_id")
        course = courses_by_id.get(course_id)
        if not course:
            continue

        course_name = course["name"]
        course_snippet = course_name  # You can later swap this for richer text
        start_iso = sess.get("start_iso") or sess.get("start")
        dt = parse_iso(start_iso) if start_iso else None

        if dt:
            dt_display = dt.strftime("%A, %B %-d, %Y at %-I:%M %p")
        else:
            dt_display = sess.get("start_display") or "Date/time TBA"

        city = sess.get("city") or ""
        state = sess.get("state") or ""
        city_state = ", ".join(p for p in [city, state] if p)

        location = sess.get("location_name") or sess.get("location") or city_state
        price = sess.get("price_display") or sess.get("price") or "See registration page"
        enroll_url = sess.get("enroll_url") or "#"

        session_id = sess.get("session_id") or sess.get("id")
        slug = slugify(course_name)
        filename = f"{session_id}-{slug}.html"
        out_path = OUTPUT_DIR / filename

        page_title = f"{course_name} – {dt_display} – {city_state} | 910CPR"
        meta_desc = (
            f"{course_name} on {dt_display} at {location} in {city_state}. "
            f"Offered by 910CPR with fast eCards and reliable, on-time classes."
        )

        other_dates_html = build_other_dates_list(
            course_id, session_id, sessions_by_course, course_name
        )
        other_courses_html = build_other_courses_list(course_id, courses)

        html = (
            template.replace("{{PAGE_TITLE}}", page_title)
            .replace("{{META_DESCRIPTION}}", meta_desc)
            .replace("{{COURSE_NAME}}", course_name)
            .replace("{{DATE_TIME}}", dt_display)
            .replace("{{LOCATION}}", location)
            .replace("{{CITY_STATE}}", city_state)
            .replace("{{PRICE}}", str(price))
            .replace("{{ENROLL_URL}}", enroll_url)
            .replace("{{COURSE_SNIPPET}}", course_snippet)
            .replace("{{OTHER_DATES_LIST}}", other_dates_html)
            .replace("{{OTHER_COURSES_LIST}}", other_courses_html)
        )

        out_path.write_text(html, encoding="utf-8")
        print(f"[build_class_landers] Wrote {out_path}")


if __name__ == "__main__":
    main()

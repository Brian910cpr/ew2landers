#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
build_schedule_page.py

Reads docs/data/schedule.json (generated from parse_enrollware.py)
and renders a static HTML schedule page at docs/schedule.html using
templates/schedule_page_template.html.

This is intentionally loud/verbose so you can see exactly what it’s doing.
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


def log(msg: str) -> None:
    print(f"[build_schedule_page] {msg}", flush=True)


def repo_root() -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, ".."))


def load_schedule(path: str) -> Dict[str, Any]:
    log(f"Loading schedule.json from {path}")
    if not os.path.exists(path):
        raise FileNotFoundError(f"schedule.json not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Basic sanity
    courses = data.get("courses", [])
    sessions = data.get("sessions", [])

    log(f"Loaded schedule.json: courses={len(courses)}, sessions={len(sessions)}")
    return data


def slugify(text: str) -> str:
    text = text.strip().lower()
    out_chars: List[str] = []
    for ch in text:
        if ch.isalnum():
            out_chars.append(ch)
        elif ch in (" ", "-", "_", "/", "|"):
            out_chars.append("-")
        # else drop weird stuff
    slug = "".join(out_chars)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "class"


def parse_start_dt(session: Dict[str, Any]) -> Tuple[datetime, str]:
    """
    Try to parse a usable datetime from the session.
    We guess field names based on parse_enrollware.
    """
    raw = (
        session.get("start_iso")
        or session.get("start")
        or session.get("start_time")
        or ""
    )

    if not raw:
        # Fallback: now, but mark clearly
        log(f"WARNING: session {session.get('id')} missing start timestamp; using now()")
        return datetime.now(timezone.utc), "Unknown date/time"

    # Normalize a bit
    txt = str(raw).strip()
    disp = txt

    # Try ISO parse
    dt = None
    try:
        # Handle trailing Z
        if txt.endswith("Z"):
            txt = txt[:-1] + "+00:00"
        dt = datetime.fromisoformat(txt)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except Exception as e:
        log(f"WARNING: could not parse start '{raw}' for session {session.get('id')}: {e}")
        dt = datetime.now(timezone.utc)

    # Human display
    try:
        disp = dt.astimezone().strftime("%a %b %d, %Y · %I:%M %p").lstrip("0")
    except Exception:
        pass

    return dt, disp


def format_time_range(session: Dict[str, Any]) -> str:
    """
    Try to show something like "9:00 AM – 1:00 PM".
    If we can’t find end time, just return the date/time we already show.
    """
    # If parse_enrollware stored explicit end, you can expand this later.
    # For now, this is a placeholder.
    return ""


def build_course_blocks(schedule: Dict[str, Any]) -> str:
    courses = schedule.get("courses", [])
    sessions = schedule.get("sessions", [])

    # Build lookup: course_id -> course record
    course_by_id: Dict[int, Dict[str, Any]] = {}
    for c in courses:
        cid = c.get("id")
        if isinstance(cid, int):
            course_by_id[cid] = c

    log(f"Indexed {len(course_by_id)} courses by id")

    # Group sessions by course_id
    sessions_by_course: Dict[int, List[Dict[str, Any]]] = {}
    now_utc = datetime.now(timezone.utc)

    for s in sessions:
        cid = s.get("course_id")
        if not isinstance(cid, int):
            continue

        start_dt, disp = parse_start_dt(s)

        # Add derived values for rendering
        s["_start_dt"] = start_dt
        s["_start_display"] = disp
        s["_time_range"] = format_time_range(s)

        # Filter out obviously past sessions, but we keep a small buffer
        if start_dt < now_utc.replace(hour=0, minute=0, second=0, microsecond=0):
            # Past session – still welcome to keep it if you want archive-style
            # For now, we keep everything; if you want only future, uncomment:
            # continue
            pass

        sessions_by_course.setdefault(cid, []).append(s)

    log(f"Grouped sessions by course: {len(sessions_by_course)} course_ids with sessions")

    blocks: List[str] = []

    # Sort courses by name for stability
    sorted_courses = sorted(
        ((cid, course_by_id.get(cid)) for cid in sessions_by_course.keys()),
        key=lambda pair: (pair[1].get("name", "").lower() if pair[1] else ""),
    )

    for cid, course in sorted_courses:
        if not course:
            log(f"WARNING: no course record for course_id={cid}, skipping")
            continue

        name = course.get("name", f"Course {cid}")
        log(f"Rendering course block: id={cid}, name='{name[:60]}...'")

        course_sessions = sessions_by_course.get(cid, [])
        # Sort sessions by start date/time
        course_sessions.sort(key=lambda s: s.get("_start_dt"))

        # Show only the next N sessions for each course on the main schedule
        MAX_PER_COURSE = 12
        visible_sessions = course_sessions[:MAX_PER_COURSE]

        items_html: List[str] = []
        for s in visible_sessions:
            sid = s.get("id")
            if sid is None:
                continue
            city = s.get("city") or ""
            state = s.get("state") or ""
            location = s.get("location") or ""
            price = s.get("price")
            enroll_url = s.get("enroll_url") or ""
            start_display = s.get("_start_display") or ""
            time_range = s.get("_time_range") or ""

            # Build a slugged lander filename
            slug = slugify(name)
            lander_filename = f"{sid}-{slug}.html"
            lander_href = f"/classes/{lander_filename}"

            price_display = ""
            if isinstance(price, (int, float)):
                price_display = f"${price:0.2f}"
            elif isinstance(price, str) and price.strip():
                price_display = price.strip()

            location_bits = [b for b in [location, city, state] if b]
            loc_display = ", ".join(location_bits)

            line_parts: List[str] = []
            if start_display:
                line_parts.append(start_display)
            if time_range:
                line_parts.append(time_range)
            if loc_display:
                line_parts.append(loc_display)
            if price_display:
                line_parts.append(price_display)

            summary = " · ".join(line_parts) if line_parts else "(details coming soon)"

            items_html.append(
                f'<li>'
                f'<a href="{lander_href}">{summary}</a>'
                f' &nbsp; '
                f'<a href="{enroll_url}" rel="nofollow">[Book via Enrollware]</a>'
                f'</li>'
            )

        if not items_html:
            items_html.append("<li>No upcoming public dates are currently listed for this class.</li>")

        block_html = (
            f'<section class="course-block" id="course-{cid}">\n'
            f'  <h2>{name}</h2>\n'
            f'  <ul>\n'
            f'    ' + "\n    ".join(items_html) + "\n"
            f'  </ul>\n'
            f'</section>\n'
        )

        blocks.append(block_html)

    log(f"Built {len(blocks)} course blocks for schedule page")
    return "\n".join(blocks)


def main() -> None:
    root = repo_root()
    schedule_path = os.path.join(root, "docs", "data", "schedule.json")
    template_path = os.path.join(root, "templates", "schedule_page_template.html")
    output_path = os.path.join(root, "docs", "schedule.html")

    log(f"Repo root is {root}")
    log(f"Template: {template_path}")
    log(f"Output:   {output_path}")

    schedule = load_schedule(schedule_path)

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found at {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        template_html = f.read()

    course_blocks_html = build_course_blocks(schedule)

    rendered = template_html.replace("<!--COURSE_BLOCKS-->", course_blocks_html)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    log(f"Wrote schedule page to {output_path}")


if __name__ == "__main__":
    main()

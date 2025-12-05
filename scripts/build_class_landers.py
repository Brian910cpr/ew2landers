#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_class_landers.py

Reads docs/data/schedule.json and builds one HTML "class lander"
per session under docs/classes/.

It also decides the "more times" button label:

- If this session is in the future AND there are other future
  sessions for the same course:
    -> "More times?"

- If this session is in the past OR there are no other future
  sessions:
    -> "Registration closed. See other times?"
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------
# Data models
# ---------------------------

@dataclass
class Course:
    id: str
    name: str
    slug: str
    schedule_url: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Course":
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", data.get("title", ""))),
            slug=str(data.get("slug", data.get("url_slug", data.get("url_fragment", "")))),
            schedule_url=str(
                data.get("schedule_url")
                or data.get("course_schedule_url")
                or data.get("course_url")
                or "#"
            ),
        )


@dataclass
class Session:
    id: str
    course_id: str
    start_iso: Optional[str]
    end_iso: Optional[str]
    location: str
    city: str
    state: str
    enroll_url: str
    raw: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        return cls(
            id=str(data.get("id", "")),
            course_id=str(data.get("course_id", "")),
            start_iso=data.get("start_iso") or data.get("start") or None,
            end_iso=data.get("end_iso") or data.get("end") or None,
            location=str(data.get("location", "")),
            city=str(data.get("city", "")),
            state=str(data.get("state", "")),
            enroll_url=str(
                data.get("enroll_url")
                or data.get("registration_url")
                or data.get("register_url")
                or "#"
            ),
            raw=data,
        )


# ---------------------------
# Helpers
# ---------------------------

def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_schedule(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_iso(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        # handle Z suffix
        if dt_str.endswith("Z"):
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return datetime.fromisoformat(dt_str)
    except Exception:
        return None


def classify_more_times_label(
    this_session: Session,
    siblings: List[Session],
    now: datetime,
) -> str:
    this_start = parse_iso(this_session.start_iso)
    has_future_sibling = False

    for sib in siblings:
        if sib.id == this_session.id:
            continue
        sib_start = parse_iso(sib.start_iso)
        if sib_start and sib_start >= now:
            has_future_sibling = True
            break

    # If this session is in the future and there are future siblings, "More times?"
    if this_start and this_start >= now and has_future_sibling:
        return "More times?"

    # Otherwise, treat as "closed" and point to other times
    return "Registration closed. See other times?"


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_template(path: Path) -> Optional[str]:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def render_with_template(template: str, context: Dict[str, Any]) -> str:
    """
    Simple {{key}} replacement, no Jinja dependency.
    """
    html = template
    for key, value in context.items():
        placeholder = "{{" + key + "}}"
        html = html.replace(placeholder, escape(str(value)))
    return html


def default_html(context: Dict[str, Any]) -> str:
    """
    Fallback HTML if templates/class_lander_template.html does not exist
    or does not use {{ }} style placeholders.
    """
    title = escape(str(context.get("course_name", "")))
    location = escape(str(context.get("location", "")))
    city_state = escape(str(context.get("city_state", "")))
    date_str = escape(str(context.get("start_date", "")))
    time_str = escape(str(context.get("start_time", "")))
    enroll_url = escape(str(context.get("enroll_url", "#")))
    schedule_url = escape(str(context.get("schedule_url", "#")))
    more_label = escape(str(context.get("more_times_label", "More times?")))
    is_past = bool(context.get("is_past"))

    status_banner = ""
    if is_past:
        status_banner = (
            '<div style="background:#ffe4e4;color:#900;padding:10px;'
            'border-radius:4px;margin-bottom:16px;font-weight:bold;">'
            "This class date has passed. To see current options, use the button below."
            "</div>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title} – {date_str} {time_str}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 24px; max-width: 900px; margin: 0 auto;">
  {status_banner}
  <h1 style="margin-bottom: 4px;">{title}</h1>
  <p style="margin-top: 0; color: #555;">
    {date_str} at {time_str}<br>
    {location}<br>
    {city_state}
  </p>

  <div style="margin: 24px 0;">
    <a href="{enroll_url}" style="display:inline-block;padding:10px 18px;border-radius:4px;border:1px solid #0b6efb;text-decoration:none;">
      Register for this class
    </a>
  </div>

  <div style="margin-top: 12px;">
    <a href="{schedule_url}" style="display:inline-block;padding:8px 14px;border-radius:4px;border:1px solid #999;text-decoration:none;">
      {more_label}
    </a>
  </div>
</body>
</html>
"""


# ---------------------------
# Main build routine
# ---------------------------

def main(argv: List[str]) -> int:
    root = repo_root()
    schedule_path = root / "docs" / "data" / "schedule.json"
    template_path = root / "templates" / "class_lander_template.html"
    output_dir = root / "docs" / "classes"

    print(f"[build_class_landers] Repo root is {root}")
    print(f"[build_class_landers] Loading schedule.json from {schedule_path}")

    schedule = load_schedule(schedule_path)
    courses_raw = schedule.get("courses", [])
    sessions_raw = schedule.get("sessions", [])

    courses: Dict[str, Course] = {}
    for c in courses_raw:
        course = Course.from_dict(c)
        if course.id:
            courses[course.id] = course

    sessions: List[Session] = []
    for s in sessions_raw:
        sess = Session.from_dict(s)
        if not sess.id or not sess.course_id:
            # Skip malformed sessions
            continue
        sessions.append(sess)

    print(f"[build_class_landers] Loaded {len(courses)} courses and {len(sessions)} sessions")

    # Group sessions by course_id for sibling lookups
    sessions_by_course: Dict[str, List[Session]] = {}
    for sess in sessions:
        sessions_by_course.setdefault(sess.course_id, []).append(sess)

    ensure_output_dir(output_dir)
    template_text = load_template(template_path)
    now = datetime.now(timezone.utc)

    built_count = 0

    for sess in sessions:
        course = courses.get(sess.course_id)
        if not course:
            # If course is missing, skip quietly
            continue

        start_dt = parse_iso(sess.start_iso)
        is_past = False
        start_date = ""
        start_time = ""
        start_iso_safe = sess.start_iso or ""

        if start_dt:
            # Normalize everything to local-looking string; we don't care about exact tz conversion here
            local_dt = start_dt
            if start_dt.tzinfo is None:
                local_dt = start_dt.replace(tzinfo=timezone.utc)
            is_past = local_dt < now
            start_date = local_dt.strftime("%A, %B %d, %Y")
            start_time = local_dt.strftime("%I:%M %p").lstrip("0")

        city_state = ", ".join(
            x for x in [sess.city.strip(), sess.state.strip()] if x
        )

        siblings = sessions_by_course.get(sess.course_id, [])
        more_label = classify_more_times_label(sess, siblings, now)

        context: Dict[str, Any] = {
            "session_id": sess.id,
            "course_id": sess.course_id,
            "course_name": course.name,
            "course_slug": course.slug,
            "location": sess.location,
            "city": sess.city,
            "state": sess.state,
            "city_state": city_state,
            "start_iso": start_iso_safe,
            "start_date": start_date,
            "start_time": start_time,
            "is_past": is_past,
            "enroll_url": sess.enroll_url,
            "schedule_url": course.schedule_url,
            "more_times_label": more_label,
        }

        if template_text:
            html = render_with_template(template_text, context)
        else:
            html = default_html(context)

        # File name scheme: session-<id>.html
        out_path = output_dir / f"session-{sess.id}.html"
        out_path.write_text(html, encoding="utf-8")
        built_count += 1

    print(f"[build_class_landers] Built {built_count} class lander pages in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

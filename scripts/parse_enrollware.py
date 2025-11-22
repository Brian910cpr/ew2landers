#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_enrollware.py

Reads the saved Enrollware schedule HTML and produces a simple JSON file:
{
  "generated_at": "...",
  "courses": [...],
  "sessions": [...]
}

This version is updated for the current Enrollware layout which uses
accordion panels (.enrpanel) and <ul class="enrclass-list"> for the
actual dated class sessions.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup  # type: ignore


ENROLLWARE_BASE = "https://coastalcprtraining.enrollware.com"


def load_html(path: Path) -> BeautifulSoup:
    """Load the saved HTML file into BeautifulSoup."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    return BeautifulSoup(text, "html.parser")


def normalize_course_name(raw: str) -> str:
    """
    Clean up the course name a bit.

    We keep it simple here – strip whitespace and collapse spaces.
    """
    if not raw:
        return ""
    cleaned = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def extract_session_id_from_href(href: str) -> str:
    """
    Extract numeric session id from an enroll link like:
      /enroll?id=11925103
      https://coastalcprtraining.enrollware.com/enroll?id=11925103
    """
    if not href:
        return ""
    parsed = urlparse(href)
    qs = parse_qs(parsed.query)
    if "id" in qs and qs["id"]:
        return qs["id"][0]

    # Fallback: regex
    m = re.search(r"id=(\d+)", href)
    return m.group(1) if m else ""


def extract_date_text(a_tag) -> str:
    """
    In Enrollware's <ul class="enrclass-list">, each <a> looks like:
      <a href="...">Wednesday, February 4, 2026 at 6:30 PM
        <span>NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office</span>
      </a>

    We want everything BEFORE the <span>.
    """
    parts: List[str] = []
    for child in a_tag.children:
        # Stop once we hit the span that contains the location
        if getattr(child, "name", None) == "span":
            break
        if isinstance(child, str):
            text = child.strip()
            if text:
                parts.append(text)
    return " ".join(parts).strip()


def parse_html(path: Path) -> Tuple[List[Dict], List[Dict]]:
    """
    Parse the Enrollware schedule HTML and return (courses, sessions).

    courses:  list of { "id": int, "name": str }
    sessions: list of {
       "id": str,
       "course_id": int,
       "course_name": str,
       "start_display": str,
       "location": str,
       "location_short": str,
       "register_url": str,
       ...
    }
    """
    soup = load_html(path)

    courses: List[Dict] = []
    sessions: List[Dict] = []
    course_index: Dict[str, int] = {}

    # Each accordion section is an ".enrpanel" with a header and body.
    # Inside the body we should see <ul class="enrclass-list"> with <li><a> entries.
    panels = soup.select("#enraccordion .enrpanel")
    if not panels:
        # Fallback: try any .enrpanel in case the id changes.
        panels = soup.select(".enrpanel")

    for panel in panels:
        # Try value="" attribute first (Enrollware uses this for searching)
        raw_course_name = panel.get("value") or ""

        if not raw_course_name:
            title_el = panel.select_one(".enrpanel-title")
            if title_el:
                raw_course_name = title_el.get_text(" ", strip=True)

        course_name = normalize_course_name(raw_course_name)
        if not course_name:
            # If we truly can't find a course name, skip this panel
            continue

        # Assign or reuse a numeric course_id
        if course_name not in course_index:
            cid = len(course_index) + 1
            course_index[course_name] = cid
            courses.append({"id": cid, "name": course_name})
        course_id = course_index[course_name]

        # Now look for the actual dated classes under this panel
        for ul in panel.select("ul.enrclass-list"):
            for li in ul.find_all("li"):
                a = li.find("a", href=True)
                if not a:
                    continue

                href = a["href"]
                # We only care about real enroll links, not internal anchors
                if "enroll" not in href:
                    continue

                session_id = extract_session_id_from_href(href)
                start_display = extract_date_text(a)
                # Location is in the <span> inside the link
                span = a.find("span")
                location = span.get_text(" ", strip=True) if span else ""
                location_short = location  # you can shorten later if desired

                register_url = urljoin(ENROLLWARE_BASE, href)

                session = {
                    "id": session_id,
                    "course_id": course_id,
                    "course_name": course_name,
                    "start_display": start_display,
                    "location": location,
                    "location_short": location_short,
                    "register_url": register_url,
                }
                sessions.append(session)

    return courses, sessions


def write_schedule_json(
    output_path: Path, courses: List[Dict], sessions: List[Dict]
) -> None:
    """Write the combined schedule.json file."""
    payload = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "courses": courses,
        "sessions": sessions,
    }
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=False),
        encoding="utf-8",
    )


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        print(
            "Usage: parse_enrollware.py INPUT_HTML OUTPUT_JSON",
            file=sys.stderr,
        )
        return 1

    input_html = Path(argv[1])
    output_json = Path(argv[2])

    if not input_html.exists():
        print(f"Input HTML not found: {input_html}", file=sys.stderr)
        return 1

    courses, sessions = parse_html(input_html)
    write_schedule_json(output_json, courses, sessions)

    print(
        f"Wrote {len(courses)} courses and {len(sessions)} sessions "
        f"to {output_json}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

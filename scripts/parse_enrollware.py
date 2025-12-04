#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_enrollware.py (verbose)

Reads the saved Enrollware schedule HTML and produces a JSON file:
{
  "generated_at": "...",
  "courses": [...],
  "sessions": [...]
}

Now with detailed print() logging so you can see every step.
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


def log(msg: str) -> None:
    print(f"[parse_enrollware] {msg}", flush=True)


def load_html(path: Path) -> BeautifulSoup:
    log(f"Loading HTML snapshot from: {path}")
    text = path.read_text(encoding="utf-8", errors="ignore")
    log(f"Snapshot size: {len(text)} bytes")
    return BeautifulSoup(text, "html.parser")


def normalize_course_name(raw: str) -> str:
    if not raw:
        return ""
    cleaned = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def extract_session_id_from_href(href: str) -> str:
    """
    Extract numeric session id from:
      /enroll?id=11925103
      https://coastalcprtraining.enrollware.com/enroll?id=11925103
    """
    if not href:
        return ""
    parsed = urlparse(href)
    qs = parse_qs(parsed.query)
    if "id" in qs and qs["id"]:
        return qs["id"][0]
    m = re.search(r"id=(\d+)", href)
    return m.group(1) if m else ""


def extract_date_text(a_tag) -> str:
    """
    Extract everything BEFORE the <span> in an <a> entry inside
    <ul class="enrclass-list">
    """
    parts: List[str] = []
    for child in a_tag.children:
        if getattr(child, "name", None) == "span":
            break
        if isinstance(child, str):
            text = child.strip()
            if text:
                parts.append(text)
    return " ".join(parts).strip()


def parse_html(path: Path) -> Tuple[List[Dict], List[Dict]]:
    soup = load_html(path)

    courses: List[Dict] = []
    sessions: List[Dict] = []
    course_index: Dict[str, int] = {}

    panels = soup.select("#enraccordion .enrpanel")
    if not panels:
        log("No #enraccordion .enrpanel found; falling back to .enrpanel.")
        panels = soup.select(".enrpanel")

    log(f"Found {len(panels)} panels.")

    for panel_idx, panel in enumerate(panels, start=1):
        raw_course_name = panel.get("value") or ""
        if not raw_course_name:
            title_el = panel.select_one(".enrpanel-title")
            if title_el:
                raw_course_name = title_el.get_text(" ", strip=True)

        course_name = normalize_course_name(raw_course_name)
        if not course_name:
            log(f"Panel #{panel_idx}: skipped (no course name).")
            continue

        if course_name not in course_index:
            cid = len(course_index) + 1
            course_index[course_name] = cid
            courses.append({"id": cid, "name": course_name})
            log(f"Panel #{panel_idx}: NEW course [{cid}] {course_name!r}")
        else:
            cid = course_index[course_name]
            log(f"Panel #{panel_idx}: existing course [{cid}] {course_name!r}")

        for ul in panel.select("ul.enrclass-list"):
            for li in ul.find_all("li"):
                a = li.find("a", href=True)
                if not a:
                    continue
                href = a["href"]
                if "enroll" not in href:
                    continue

                session_id = extract_session_id_from_href(href)
                start_display = extract_date_text(a)
                span = a.find("span")
                location = span.get_text(" ", strip=True) if span else ""
                register_url = urljoin(ENROLLWARE_BASE, href)

                sessions.append({
                    "id": session_id,
                    "course_id": cid,
                    "course_name": course_name,
                    "start_display": start_display,
                    "location": location,
                    "location_short": location,
                    "register_url": register_url,
                })

    log(f"Finished parsing: {len(courses)} courses, {len(sessions)} sessions.")
    return courses, sessions


def write_schedule_json(output_path: Path, courses: List[Dict], sessions: List[Dict]) -> None:
    log(f"Writing schedule JSON to: {output_path}")
    payload = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "courses": courses,
        "sessions": sessions,
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log("Finished writing schedule.json.")


def main(argv: List[str]) -> int:
    log("Starting parse_enrollware main().")
    if len(argv) != 3:
        print("Usage: parse_enrollware.py INPUT_HTML OUTPUT_JSON", file=sys.stderr)
        log("Incorrect arguments; exiting.")
        return 1

    input_html = Path(argv[1])
    output_json = Path(argv[2])

    if not input_html.exists():
        print(f"Input HTML not found: {input_html}", file=sys.stderr)
        log("HTML file missing; exiting.")
        return 1

    courses, sessions = parse_html(input_html)
    write_schedule_json(output_json, courses, sessions)

    log(f"Done: wrote {len(courses)} courses and {len(sessions)} sessions to {output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

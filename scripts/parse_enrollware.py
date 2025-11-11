#!/usr/bin/env python3
"""
parse_enrollware.py

Lightweight scraper for an Enrollware schedule snapshot HTML file.

Usage (from repo root)
----------------------
  python scripts/parse_enrollware.py docs/data/enrollware-schedule.html > docs/data/schedule.json

Output JSON (to stdout)
-----------------------
{
  "meta": {...},
  "sessions": [
     {
        "id": 123456,
        "url": "https://coastalcprtraining.enrollware.com/enroll?id=123456",
        "start": "2025-11-10T13:00:00",
        "end": null,
        "location": "NC - Burgaw: 111 S Wright St @ 910CPR's Office",
        "title": "... human course title ...",
        "course_title": "... same as title ...",
        "course_id": "ct209806",
        "section": "short course description without the long list of dates",
        "classType": "BLS|ACLS|PALS|Heartsaver|HSI|Other",
        "instructor": null,
        "seats": null,
        "start_text": "Monday, November 10, 2025 at 1:00 PM NC - Burgaw: 111 S Wright St @ 910CPR's Office"
     },
     ...
  ],
  "sections": [],
  "courses": []
}
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup  # type: ignore
from dateutil import parser as dtparser  # type: ignore

ENROLL_BASE = "https://coastalcprtraining.enrollware.com/"


@dataclass
class Session:
    id: Optional[int]
    url: str
    start: Optional[str]
    end: Optional[str]
    location: str
    title: str
    course_title: str
    course_id: Optional[str]
    section: str
    classType: str
    instructor: Optional[str]
    seats: Optional[int]
    start_text: str


def guess_class_type(title: str) -> str:
    t = (title or "").lower()
    if "acls" in t:
        return "ACLS"
    if "pals" in t:
        return "PALS"
    if "bls" in t:
        return "BLS"
    if "heartsaver" in t:
        return "Heartsaver"
    if "hsi" in t:
        return "HSI"
    return "Other"


# e.g. "Monday, December 29, 2025 at 1:00 PM"
DATE_TIME_RE = re.compile(
    r"([A-Za-z]+,\s+[A-Za-z]+\s+\d{1,2},\s+\d{4}\s+at\s+\d{1,2}:\d{2}\s*(?:AM|PM))",
    re.IGNORECASE,
)


def extract_start_iso(text: str) -> Optional[str]:
    """
    Pull the first 'Monday, December 29, 2025 at 1:00 PM' style chunk out of the
    text and return it as ISO-8601. If parsing fails, returns None.
    """
    if not text:
        return None
    m = DATE_TIME_RE.search(text)
    if not m:
        return None
    when_str = m.group(1)
    try:
        dt = dtparser.parse(when_str)
    except Exception:
        return None
    # store as naive ISO (no offset) – frontend just compares relative
    return dt.replace(tzinfo=None).isoformat()


def find_course_panel(a_tag):
    """
    Walk up the DOM from a schedule <a> node until we reach the enclosing
    'panel' that represents a single course.
    """
    node = a_tag
    while node is not None:
        if getattr(node, "get", None):
            classes = node.get("class") or []
            if any("panel" in c or "enrpanel" in c for c in classes):
                return node
        node = getattr(node, "parent", None)
    return None


def get_course_title(panel) -> str:
    if panel is None:
        return ""
    for sel in [".enrpanel-title", ".panel-title", "h3", "h4"]:
        h = panel.select_one(sel)
        if h and h.get_text(strip=True):
            return h.get_text(strip=True)
    # fall back to any strong header-ish text
    header = panel.find(["strong", "b"])
    return header.get_text(strip=True) if header else ""


def get_course_id(panel) -> Optional[str]:
    if panel is None:
        return None
    # Enrollware often uses anchors like <a name="ct209806">
    a = panel.find("a", attrs={"name": re.compile(r"^ct\d+", re.IGNORECASE)})
    if a and a.has_attr("name"):
        return a["name"]
    return None


def get_section_text(panel) -> str:
    """
    Return the course description text WITHOUT the long list of date/time lines.
    We do this by cloning the body, stripping out any <ul> that looks like the
    schedule list, then reading text.
    """
    if panel is None:
        return ""
    body = panel.select_one(".enrpanel-body") or panel
    # work on a cloned fragment so we can destructively modify
    clone = BeautifulSoup(str(body), "lxml")
    # remove any ULs that contain enroll links
    for ul in clone.find_all("ul"):
        if ul.find("a", href=re.compile(r"enroll\?id=", re.IGNORECASE)):
            ul.decompose()
    # whatever remains is the descriptive text
    text = " ".join(clone.stripped_strings)
    return text


def parse_html(path: Path) -> dict:
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")

    sessions: List[Session] = []

    anchors = soup.find_all("a", href=re.compile(r"enroll\?id=\d+", re.IGNORECASE))
    for a in anchors:
        href = a.get("href") or ""
        if not href:
            continue
        # build absolute URL
        if href.startswith("http"):
            url = href
        else:
            url = ENROLL_BASE.rstrip("/") + "/" + href.lstrip("/")

        # numeric id from querystring
        m = re.search(r"id=(\d+)", url)
        sess_id = int(m.group(1)) if m else None

        # location is usually in a <span> inside the anchor
        location = ""
        span = a.find("span")
        if span:
            location = span.get_text(strip=True)

        # human-readable text (includes date/time and maybe seats/location)
        start_text = " ".join(a.stripped_strings)

        # course context
        panel = find_course_panel(a)
        course_title = get_course_title(panel)
        course_id = get_course_id(panel)
        section_text = get_section_text(panel)

        class_type = guess_class_type(course_title or start_text)
        start_iso = extract_start_iso(start_text)

        sess = Session(
            id=sess_id,
            url=url,
            start=start_iso,
            end=None,
            location=location,
            title=course_title or start_text,
            course_title=course_title or start_text,
            course_id=course_id,
            section=section_text,
            classType=class_type,
            instructor=None,
            seats=None,
            start_text=start_text,
        )
        sessions.append(sess)

    meta = {
        "source": str(path),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "panel_count": None,
        "session_count": len(sessions),
    }
    return {
        "meta": meta,
        "sections": [],
        "courses": [],
        "sessions": [asdict(s) for s in sessions],
    }


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: parse_enrollware.py SCHEDULE_HTML > schedule.json", file=sys.stderr)
        return 1
    in_path = Path(argv[1])
    if not in_path.is_file():
        print(f"ERROR: HTML file not found: {in_path}", file=sys.stderr)
        return 1
    data = parse_html(in_path)
    json.dump(data, sys.stdout, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

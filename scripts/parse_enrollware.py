#!/usr/bin/env python3
"""
Parse Enrollware snapshot HTML into a JSON sessions list.

Input:  path to docs/data/enrollware-schedule.html
Output: JSON to stdout:

{
  "meta": {
    "source": "docs/data/enrollware-schedule.html",
    "fetched_at": "...",
    "panel_count": 48,
    "session_count": 1234
  },
  "sessions": [
    {
      "id": 11930079,
      "url": "https://coastalcprtraining.enrollware.com/enroll?id=11930079",
      "start": "2025-12-29T13:00:00",
      "end": null,
      "location": "NC - Burgaw: 111 S Wright St @ 910CPR's Office",
      "title": "AHA - BLS Provider - In-person Initial Instructor-led Classroom for Expired or New BLS",
      "course_title": "AHA - BLS Provider - In-person Initial Instructor-led Classroom for Expired or New BLS",
      "course_id": "ct209806",
      "section": "Healthcare Provider: BLS Course Basic Life Support (BLS) ... Select a Program Below ...",
      "classType": "BLS",
      "instructor": null,
      "seats": 5,
      "start_text": "Monday, December 29, 2025 at 1:00 PM NC - Burgaw: 111 S Wright St @ 910CPR's Office"
    },
    ...
  ]
}
"""

import sys
import re
import json
from datetime import datetime, timezone

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

ENROLLWARE_BASE = "https://coastalcprtraining.enrollware.com/"


# ---------- small helpers ----------

def normspace(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


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


def to_abs_url(href: str) -> str:
    href = href or ""
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return ENROLLWARE_BASE + href.lstrip("./")


def extract_seats(text: str):
    """
    From '... at 1:00 PM (5 seats left) ...' -> 5
    """
    if not text:
        return None
    m = re.search(r"\((\d+)\s+seats?\s+left\)", text, re.I)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


def strip_seats(text: str) -> str:
    if not text:
        return ""
    return normspace(re.sub(r"\(\d+\s+seats?\s+left\)", "", text, flags=re.I))


def parse_start_iso(text: str):
    """
    Best-effort parse of 'Monday, December 29, 2025 at 1:00 PM NC - Burgaw: ...'
    Returns ISO string or None.
    """
    if not text:
        return None
    # Give dateutil the whole line and let it ignore the location
    try:
        dt = dateparser.parse(text, fuzzy=True)
        if not dt:
            return None
        # If dateutil gives us a date with no time, don't pretend
        if dt.hour == 0 and dt.minute == 0 and "am" not in text.lower() and "pm" not in text.lower():
            return None
        # Make it naive ISO (browser will interpret local, as before)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt.isoformat(timespec="minutes")
    except Exception:
        return None


def extract_panel_section_text(panel):
    """
    Get the course description text without the giant schedule list.

    Strategy:
      - Find .enrpanel-body
      - Remove any <ul class="enrclass-list"> from a *copy*
      - Return remaining text as 'section'
    """
    body = panel.select_one(".enrpanel-body")
    if not body:
        return ""

    # Work on a clone to safely strip the <ul>
    clone = BeautifulSoup(str(body), "lxml")
    ul = clone.select_one(".enrclass-list")
    if ul:
        ul.decompose()
    text = normspace(clone.get_text(" ", strip=True))
    return text


# ---------- core parser ----------

def parse_schedule_from_html(html: str):
    soup = BeautifulSoup(html, "lxml")

    sessions = []
    panel_count = 0

    # Main accordion: one .enrpanel per course
    panels = soup.select("#enraccordion .enrpanel")
    if not panels:
        # Fall back: if markup changes, still try generic anchors
        return parse_generic_anchors(soup)

    for panel in panels:
        panel_count += 1

        # Course id from <a name="ctXXXXX">
        course_anchor = panel.find("a", attrs={"name": True})
        course_id = course_anchor["name"] if course_anchor and course_anchor.has_attr("name") else None

        # Course title from panel heading
        heading = panel.select_one(".enrpanel-heading .enrpanel-title") or panel.select_one(".enrpanel-heading")
        course_title = normspace(heading.get_text(" ", strip=True)) if heading else ""

        class_type = guess_class_type(course_title)
        section_text = extract_panel_section_text(panel)

        # Each li in .enrclass-list is a session
        ul = panel.select_one(".enrclass-list")
        if not ul:
            continue

        for li in ul.find_all("li"):
            a = li.find("a", href=lambda h: h and "enroll?id=" in h)
            if not a:
                continue

            href = a.get("href") or ""
            url = to_abs_url(href)
            m = re.search(r"id=(\d+)", url)
            sess_id = int(m.group(1)) if m else None

            visible_text = normspace(a.get_text(" ", strip=True))
            seats = extract_seats(visible_text)
            start_text = strip_seats(visible_text)

            # Location: prefer explicit span inside the anchor
            loc_span = a.find("span")
            location = normspace(loc_span.get_text(" ", strip=True)) if loc_span else ""

            start_iso = parse_start_iso(start_text)

            sessions.append(
                {
                    "id": sess_id,
                    "url": url,
                    "start": start_iso,
                    "end": None,
                    "location": location,
                    "title": course_title,
                    "course_title": course_title,
                    "course_id": course_id,
                    "section": section_text,
                    "classType": class_type,
                    "instructor": None,
                    "seats": seats,
                    "start_text": start_text,
                }
            )

    meta = {
        "source": "docs/data/enrollware-schedule.html",
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "panel_count": panel_count,
        "session_count": len(sessions),
    }
    return {"meta": meta, "sessions": sessions}


def parse_generic_anchors(soup):
    """
    Fallback if .enrpanel structure is not present.
    Parses any <a href*="enroll?id="> found in the document.
    Much dumber, but better than returning nothing.
    """
    sessions = []
    anchors = soup.select('a[href*="enroll?id="]')
    for a in anchors:
        href = a.get("href") or ""
        url = to_abs_url(href)
        m = re.search(r"id=(\d+)", url)
        sess_id = int(m.group(1)) if m else None

        row = a.find_parent(["li", "tr", "div"]) or a
        row_text = normspace(row.get_text(" ", strip=True))
        seats = extract_seats(row_text)
        start_text = strip_seats(row_text)

        loc_span = a.find("span")
        location = normspace(loc_span.get_text(" ", strip=True)) if loc_span else ""
        title = normspace(a.get("title") or a.get_text(" ", strip=True) or row_text)
        class_type = guess_class_type(title)
        start_iso = parse_start_iso(start_text)

        sessions.append(
            {
                "id": sess_id,
                "url": url,
                "start": start_iso,
                "end": None,
                "location": location,
                "title": title,
                "course_title": title,
                "course_id": None,
                "section": "",
                "classType": class_type,
                "instructor": None,
                "seats": seats,
                "start_text": start_text,
            }
        )

    meta = {
        "source": "docs/data/enrollware-schedule.html",
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "panel_count": 0,
        "session_count": len(sessions),
    }
    return {"meta": meta, "sessions": sessions}


# ---------- CLI ----------

def main():
    if len(sys.argv) < 2:
        print("Usage: parse_enrollware.py docs/data/enrollware-schedule.html", file=sys.stderr)
        sys.exit(1)

    html_path = sys.argv[1]
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    data = parse_schedule_from_html(html)
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Parse docs/data/enrollware-schedule.html into a simple sessions JSON:

{
  "meta": {
    "source": "docs/data/enrollware-schedule.html",
    "fetched_at": "...",
    "panel_count": 48
  },
  "sessions": [
    {
      "id": 11930079,
      "url": "https://coastalcprtraining.enrollware.com/enroll?id=11930079",
      "start": "2025-12-29T13:00:00",
      "end": null,
      "location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
      "title": "AHA - BLS Provider - In-person Initial Instructor-led Classroom for Expired or New BLS",
      "course_title": "AHA - BLS Provider - In-person Initial Instructor-led Classroom for Expired or New BLS",
      "course_id": "ct209806",
      "section": "Healthcare Provider: BLS Course Basic Life Support (BLS) for healthcare professionals ...",
      "classType": "BLS",
      "instructor": null,
      "seats": null,
      "start_text": "Monday, December 29, 2025 at 1:00 PM (5 seats left) NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office"
    },
    ...
  ]
}

Notes:
- `start` is ISO 8601 when we can parse it, otherwise null.
- `start_text` keeps the raw visible Enrollware text for debugging.
"""

import sys
import re
import json
from datetime import datetime, timezone

from bs4 import BeautifulSoup, Tag
from dateutil import parser as dateparser

ENROLLWARE_BASE = "https://coastalcprtraining.enrollware.com/"

# Heuristic: what kind of class is this?
def guess_type(title: str | None) -> str:
    t = (title or "").lower()
    if "acls" in t:
        return "ACLS"
    if "pals" in t:
        return "PALS"
    if "bls" in t:
        return "BLS"
    if "heartsaver" in t or "first aid" in t:
        return "Heartsaver"
    if "hsi" in t:
        return "HSI"
    return "Other"


def normspace(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def to_abs_url(href: str | None) -> str:
    href = href or ""
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return ENROLLWARE_BASE + href.lstrip("./")


def guess_start_iso(text: str | None) -> str | None:
    """
    Try very hard to get an ISO datetime out of the Enrollware
    visible text, e.g.:

      "Monday, December 29, 2025 at 1:00 PM (5 seats left)
       NC - Burgaw: ..."

    We let dateutil.parser skip the junk (fuzzy=True).
    """
    txt = normspace(text)
    if not txt:
        return None
    try:
        dt = dateparser.parse(txt, fuzzy=True)
        if not dt:
            return None
        # Normalise to naive ISO; frontend doesn't care about tz right now.
        # If the parser didn't get any time component, this will still be 00:00.
        return dt.replace(tzinfo=None).isoformat()
    except Exception:
        return None


def find_section_label(panel: Tag) -> str:
    """
    Walk backwards from a panel to find the nearest "section-ish" text.
    On the Enrollware snapshot this is typically the BLS/ACLS/PALS
    section heading just above the panel.
    """
    cur: Tag | None = panel
    steps = 0
    while cur is not None and steps < 200:
        steps += 1
        sib = cur.previous_sibling
        while sib is not None:
            if isinstance(sib, Tag):
                txt = normspace(sib.get_text(" ", strip=True))
                if txt:
                    return txt
            sib = sib.previous_sibling
        parent = cur.parent if isinstance(cur, Tag) else None
        if parent is None or getattr(parent, "name", "").lower() == "body":
            break
        cur = parent
    return ""


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage: parse_enrollware.py docs/data/enrollware-schedule.html",
            file=sys.stderr,
        )
        sys.exit(1)

    html_path = sys.argv[1]

    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    panels = soup.select("div.enrpanel")
    sessions: list[dict] = []

    for panel in panels:
        # Course-level data
        name_anchor = panel.find("a", attrs={"name": True})
        course_id = name_anchor.get("name") if name_anchor else None

        title_el = panel.select_one(".enrpanel-title")
        course_title = normspace(title_el.get_text(" ", strip=True)) if title_el else ""
        section_label = find_section_label(panel)
        class_type = guess_type(course_title)

        # Each scheduled class inside this panel
        for a in panel.select('a[href*="enroll?id="]'):
            href = a.get("href") or ""
            url = to_abs_url(href)

            m = re.search(r"id=(\d+)", url)
            sess_id = int(m.group(1)) if m else None

            # Visible text & location span
            # Example:
            #   "Monday, December 29, 2025 at 1:00 PM (5 seats left)
            #    NC - Burgaw: ... "
            start_text = normspace(a.get_text(" ", strip=True))

            span_loc = a.find("span")
            location = normspace(span_loc.get_text(" ", strip=True)) if span_loc else ""

            start_iso = guess_start_iso(start_text)

            sessions.append(
                {
                    "id": sess_id,
                    "url": url,
                    "start": start_iso,
                    "end": None,
                    "location": location,
                    "title": course_title or start_text,
                    "course_title": course_title or start_text,
                    "course_id": course_id,
                    "section": section_label,
                    "classType": class_type,
                    "instructor": None,
                    "seats": None,
                    "start_text": start_text,
                }
            )

    out = {
        "meta": {
            "source": html_path,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "panel_count": len(panels),
        },
        "sessions": sessions,
    }

    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

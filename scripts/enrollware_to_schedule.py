#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
enrollware_to_schedule.py

One-step builder:
  docs/data/enrollware-schedule.html  ->  docs/data/schedule.json (flat legacy list)

✅ FIXES ADDED (this is the “schedule.json fix” you asked for):
  1) Parses Enrollware's displayed date/time into a real ISO datetime:
       - start_iso (timezone-aware, America/New_York)
       - start_ms  (epoch millis for bulletproof sorting)
  2) Adds is_past computed at build time (based on start_iso)
  3) Adds schedule_url per course (Enrollware schedule#ct#######)
  4) Adds register_url alias (keeps your existing "url" too)

Keeps your existing DOM anchors:
  - #enraccordion .enrpanel
  - ul.enrclass-list > li > a[href*="enroll"]

Logs go to STDERR so schedule.json stays clean JSON.

Usage:
  python scripts/enrollware_to_schedule.py
  python scripts/enrollware_to_schedule.py INPUT_HTML OUTPUT_JSON
"""

import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime

try:
    from zoneinfo import ZoneInfo  # py3.9+
except Exception:
    ZoneInfo = None

from bs4 import BeautifulSoup

ENROLLWARE_BASE = "https://coastalcprtraining.enrollware.com/"
LOCAL_TZ_NAME = "America/New_York"
LOCAL_TZ = ZoneInfo(LOCAL_TZ_NAME) if ZoneInfo else None

ROOT = Path(__file__).resolve().parents[1]  # repo root
DEFAULT_INPUT = ROOT / "docs" / "data" / "enrollware-schedule.html"
DEFAULT_OUTPUT = ROOT / "docs" / "data" / "schedule.json"


def log(msg: str) -> None:
    print(f"[enrollware_to_schedule] {msg}", file=sys.stderr, flush=True)


def extract_session_id_from_href(href: str):
    if not href:
        return None
    try:
        parsed = urlparse(href)
        qs = parse_qs(parsed.query)
        if "id" in qs and qs["id"]:
            return int(qs["id"][0])
    except Exception:
        pass

    digits = "".join(ch for ch in href if ch.isdigit())
    return int(digits) if digits else None


def extract_course_number_from_text(text: str):
    """
    Try to find a course filter value like ct209811 in any text/href.
    Returns digits as string, or None.
    """
    if not text:
        return None
    m = re.search(r"#ct(\d+)", text)
    if m:
        return m.group(1)
    m = re.search(r"[?&]course=(\d+)", text)
    if m:
        return m.group(1)
    return None


def normalize_course_name(raw: str) -> str:
    if not raw:
        return ""
    s = raw.strip()
    s = " ".join(s.split())
    return s


def extract_date_text(anchor_tag) -> str:
    txt = anchor_tag.get_text(" ", strip=True)
    return " ".join(txt.split())


def try_extract_price(panel_text: str):
    if not panel_text:
        return None
    m = re.search(r"\$\s*\d+(?:\.\d{2})?", panel_text)
    if not m:
        return None
    return m.group(0).replace(" ", "")


def build_schedule_url(course_number: str | None) -> str | None:
    if not course_number:
        return None
    # IMPORTANT: user wants real, full URLs (no bit.ly, no hiding)
    # Enrollware course filter is schedule#ct#######
    return urljoin(ENROLLWARE_BASE, f"schedule#ct{course_number}")


def _try_parse_start_display_to_dt(start_display: str) -> datetime | None:
    """
    Enrollware typically displays:
      "Saturday, December 20, 2025 at 12:30 PM"
    Sometimes "12:30PM" or missing weekday punctuation, etc.

    Returns timezone-aware datetime in America/New_York if possible.
    """
    if not start_display:
        return None

    s = " ".join(start_display.strip().split())

    # Normalize small formatting variants
    s = s.replace(" at ", " at ")
    s = re.sub(r"\s+", " ", s)

    # Common formats to try
    # - With weekday and "at"
    # - Without weekday
    # - Without "at"
    fmts = [
        "%A, %B %d, %Y at %I:%M %p",
        "%A, %B %d, %Y at %I %p",
        "%B %d, %Y at %I:%M %p",
        "%B %d, %Y at %I %p",
        "%A, %B %d, %Y %I:%M %p",
        "%B %d, %Y %I:%M %p",
    ]

    for fmt in fmts:
        try:
            naive = datetime.strptime(s, fmt)
            if LOCAL_TZ:
                return naive.replace(tzinfo=LOCAL_TZ)
            return naive  # fallback (naive) if zoneinfo missing
        except Exception:
            continue

    # Last-chance regex parse (e.g., weird spacing)
    m = re.search(
        r"(?:(?P<weekday>[A-Za-z]+),\s*)?(?P<month>[A-Za-z]+)\s+(?P<day>\d{1,2}),\s+(?P<year>\d{4})\s+(?:at\s+)?(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<ampm>AM|PM)",
        s,
        re.IGNORECASE,
    )
    if not m:
        return None

    try:
        month_name = m.group("month").title()
        day = int(m.group("day"))
        year = int(m.group("year"))
        hour = int(m.group("hour"))
        minute = int(m.group("minute") or "0")
        ampm = m.group("ampm").upper()

        if ampm == "PM" and hour != 12:
            hour += 12
        if ampm == "AM" and hour == 12:
            hour = 0

        naive = datetime(year, datetime.strptime(month_name, "%B").month, day, hour, minute)
        if LOCAL_TZ:
            return naive.replace(tzinfo=LOCAL_TZ)
        return naive
    except Exception:
        return None


def html_to_schedule_rows(html_text: str):
    soup = BeautifulSoup(html_text, "lxml")

    panels = soup.select("#enraccordion .enrpanel")
    if not panels:
        log("No #enraccordion .enrpanel found; falling back to .enrpanel.")
        panels = soup.select(".enrpanel")

    log(f"Found {len(panels)} enrpanel blocks.")

    rows = []
    course_index = {}  # course_name -> course_id
    course_meta = {}   # course_id -> dict

    # "now" for is_past calculation
    now_dt = datetime.now(tz=LOCAL_TZ) if LOCAL_TZ else datetime.now()

    for panel in panels:
        raw_course_name = panel.get("value") or ""
        if not raw_course_name:
            title_el = panel.select_one(".enrpanel-title")
            if title_el:
                raw_course_name = title_el.get_text(" ", strip=True)

        course_name = normalize_course_name(raw_course_name)
        if not course_name:
            continue

        if course_name not in course_index:
            cid = len(course_index) + 1
            course_index[course_name] = cid
        else:
            cid = course_index[course_name]

        # Try to find course_number (ct######) from the panel's anchor:
        # Enrollware uses: <a name='ct209806'></a>
        course_number = None

        a_ct = panel.select_one("a[name^='ct']")
        if a_ct and a_ct.get("name"):
            nm = a_ct.get("name").strip()  # e.g. "ct209806"
            if nm.lower().startswith("ct") and nm[2:].isdigit():
                course_number = nm[2:]

        # Fallback: if not found, try to find #ct####### in any href
        if not course_number:
            for a in panel.find_all("a", href=True):
                course_number = extract_course_number_from_text(a["href"])
                if course_number:
                    break

        schedule_url = build_schedule_url(course_number)

        panel_text = panel.get_text(" ", strip=True)
        price = try_extract_price(panel_text)

        if cid not in course_meta:
            course_meta[cid] = {
                "course_number": course_number,
                "schedule_url": schedule_url,
                "price": price,
                "course_name": course_name,
            }
        else:
            if not course_meta[cid].get("course_number") and course_number:
                course_meta[cid]["course_number"] = course_number
                course_meta[cid]["schedule_url"] = build_schedule_url(course_number)
            if not course_meta[cid].get("schedule_url") and schedule_url:
                course_meta[cid]["schedule_url"] = schedule_url
            if not course_meta[cid].get("price") and price:
                course_meta[cid]["price"] = price

        # Sessions
        for ul in panel.select("ul.enrclass-list"):
            for li in ul.find_all("li"):
                a = li.find("a", href=True)
                if not a:
                    continue
                href = a["href"]
                if "enroll" not in href:
                    continue

                session_id = extract_session_id_from_href(href)
                if not session_id:
                    continue

                start_display = extract_date_text(a)
                start_dt = _try_parse_start_display_to_dt(start_display)

                start_iso = start_dt.isoformat() if start_dt else None
                start_ms = int(start_dt.timestamp() * 1000) if start_dt else None
                is_past = (start_dt < now_dt) if (start_dt and now_dt) else None

                span = li.find("span")
                location = span.get_text(" ", strip=True) if span else ""
                register_url = urljoin(ENROLLWARE_BASE, href)

                rows.append({
                    # Legacy / existing fields (kept)
                    "id": session_id,
                    "course_id": cid,
                    "course_number": course_meta[cid].get("course_number"),
                    "title": course_name,
                    "date": start_display,   # raw display
                    "time": None,            # (kept for legacy compatibility)
                    "location": location,
                    "price": course_meta[cid].get("price"),
                    "url": register_url,     # legacy name (kept)

                    # New / fixed fields
                    "register_url": register_url,                 # better field name for UI
                    "schedule_url": course_meta[cid].get("schedule_url"),
                    "start_iso": start_iso,                       # timezone-aware ISO if possible
                    "start_ms": start_ms,                         # epoch ms for bulletproof sorting
                    "is_past": is_past,                           # computed at build time
                    "end_iso": None,                              # left blank unless you add durations later
                })

    # Deterministic ordering helps diffs and makes the UI consistent
    # Sort by course_id then start_ms (unknowns last)
    def _sort_key(r):
        sm = r.get("start_ms")
        return (r.get("course_id") or 0, sm if isinstance(sm, int) else 9_999_999_999_999)

    rows.sort(key=_sort_key)

    log(f"Built {len(rows)} schedule rows.")
    return rows


def main(argv) -> int:
    input_path = Path(argv[1]) if len(argv) >= 2 else DEFAULT_INPUT
    output_path = Path(argv[2]) if len(argv) >= 3 else DEFAULT_OUTPUT

    if not input_path.exists():
        log(f"Input HTML not found: {input_path}")
        return 1

    html_text = input_path.read_text(encoding="utf-8", errors="ignore")
    rows = html_to_schedule_rows(html_text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    log(f"Wrote {len(rows)} rows to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
